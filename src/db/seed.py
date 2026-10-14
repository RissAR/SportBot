"""Idempotent database seeder for SportBot 30-day calisthenics cycle and exercise catalog."""

import asyncio
import logging
from typing import Dict, List

from sqlalchemy import func, select

from src.db.models import CycleDay, CycleDayExercise, Exercise, ExerciseProgression
from src.db.session import get_db_session, init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("sportbot.seed")

# 12 Core Exercises Definition
EXERCISES_DATA = [
    # Push Block
    {
        "slug": "dips",
        "name": "Parallel Bar Dips",
        "category": "push",
        "metric_type": "reps",
        "description": "Compound bodyweight pushing exercise focusing on the lower pectorals, triceps, and anterior deltoids.",
        "technique_tips": "Maintain active scapular depression, lean torso forward ~45° to target chest, keep elbows tucked at ~45° (never flare out 90° to protect rotator cuffs at 85kg bw), maintain hollow body.",
        "progressions": [
            {"difficulty_tier": "light", "progression_name": "Bench Dips / Band-Assisted Dips", "target_sets": 3, "target_value": 8, "tempo": "3-1-1", "rest_seconds": 60},
            {"difficulty_tier": "medium", "progression_name": "Parallel Bar Dips", "target_sets": 4, "target_value": 12, "tempo": "3-1-1", "rest_seconds": 60},
            {"difficulty_tier": "hard", "progression_name": "Straight Bar / Deficit Dips", "target_sets": 4, "target_value": 16, "tempo": "3-1-1", "rest_seconds": 60},
        ],
    },
    {
        "slug": "decline_pushups",
        "name": "Decline Push-ups",
        "category": "push",
        "metric_type": "reps",
        "description": "Push-up variation with feet elevated on a 30-50cm platform, shifting load to clavicular upper pectorals and front deltoids.",
        "technique_tips": "Squeeze glutes and brace core to prevent lumbar hyperextension, tuck elbows at 45°, lower with a 3-second eccentric tempo until chest gently touches the floor.",
        "progressions": [
            {"difficulty_tier": "light", "progression_name": "Standard Flat Push-ups", "target_sets": 3, "target_value": 10, "tempo": "3-1-1", "rest_seconds": 60},
            {"difficulty_tier": "medium", "progression_name": "Decline Push-ups (30cm elevation)", "target_sets": 4, "target_value": 14, "tempo": "3-1-1", "rest_seconds": 60},
            {"difficulty_tier": "hard", "progression_name": "High Decline Push-ups (50cm elevation)", "target_sets": 4, "target_value": 18, "tempo": "3-1-1", "rest_seconds": 60},
        ],
    },
    {
        "slug": "pike_pushups",
        "name": "Pike Push-ups",
        "category": "push",
        "metric_type": "reps",
        "description": "Vertical pushing bodyweight progression forming an inverted V-shape, loading the anterior and lateral deltoids.",
        "technique_tips": "Keep hips high and legs straight, lower head forward forming an equilateral triangle between head and hands, press back up and through to finish with active shoulder elevation.",
        "progressions": [
            {"difficulty_tier": "light", "progression_name": "Incline Pike Push-ups", "target_sets": 3, "target_value": 8, "tempo": "3-1-1", "rest_seconds": 60},
            {"difficulty_tier": "medium", "progression_name": "Floor Pike Push-ups", "target_sets": 4, "target_value": 10, "tempo": "3-1-1", "rest_seconds": 60},
            {"difficulty_tier": "hard", "progression_name": "Feet-Elevated Pike Push-ups", "target_sets": 4, "target_value": 12, "tempo": "3-1-1", "rest_seconds": 60},
        ],
    },
    # Pull & Core Block
    {
        "slug": "pullups",
        "name": "Overhand Pull-ups",
        "category": "pull",
        "metric_type": "reps",
        "description": "Full vertical pulling exercise targeting the latissimus dorsi, rhomboids, rear delts, and forearm flexors.",
        "technique_tips": "Initiate from a dead hang with active scapular depression and retraction before bending elbows. Drive elbows down into back pockets, pull chest towards the bar without swinging.",
        "progressions": [
            {"difficulty_tier": "light", "progression_name": "Band-Assisted / Negative Pull-ups", "target_sets": 3, "target_value": 6, "tempo": "3-1-1", "rest_seconds": 60},
            {"difficulty_tier": "medium", "progression_name": "Strict Overhand Pull-ups", "target_sets": 4, "target_value": 8, "tempo": "3-1-1", "rest_seconds": 60},
            {"difficulty_tier": "hard", "progression_name": "Chest-to-Bar / L-Sit Pull-ups", "target_sets": 4, "target_value": 12, "tempo": "3-1-1", "rest_seconds": 60},
        ],
    },
    {
        "slug": "chinups",
        "name": "Underhand Chin-ups",
        "category": "pull",
        "metric_type": "reps",
        "description": "Supinated grip vertical pull engaging the latissimus dorsi with maximal emphasis on biceps brachii recruitment.",
        "technique_tips": "Keep shoulders depressed away from ears, initiate pull with lats, squeeze biceps hard at the peak with chin clearing the bar, lower smoothly under full 3-second control.",
        "progressions": [
            {"difficulty_tier": "light", "progression_name": "Band-Assisted / Isometric Chin-ups", "target_sets": 3, "target_value": 6, "tempo": "3-1-1", "rest_seconds": 60},
            {"difficulty_tier": "medium", "progression_name": "Strict Underhand Chin-ups", "target_sets": 4, "target_value": 8, "tempo": "3-1-1", "rest_seconds": 60},
            {"difficulty_tier": "hard", "progression_name": "Pause Underhand Chin-ups (2s hold at top)", "target_sets": 4, "target_value": 12, "tempo": "3-1-1", "rest_seconds": 60},
        ],
    },
    {
        "slug": "horizontal_rows",
        "name": "Australian Rows",
        "category": "pull",
        "metric_type": "reps",
        "description": "Horizontal bodyweight pulling movement balancing push volume and fortifying the rotator cuff, middle traps, and rhomboids.",
        "technique_tips": "Keep body in a rigid plank, retract shoulder blades before pulling, touch lower chest to bar/rings, control eccentric return without dropping shoulders forward.",
        "progressions": [
            {"difficulty_tier": "light", "progression_name": "High-Angle Incline Rows", "target_sets": 3, "target_value": 10, "tempo": "3-1-1", "rest_seconds": 60},
            {"difficulty_tier": "medium", "progression_name": "Horizontal Australian Rows", "target_sets": 4, "target_value": 12, "tempo": "3-1-1", "rest_seconds": 60},
            {"difficulty_tier": "hard", "progression_name": "Feet-Elevated Australian Rows", "target_sets": 4, "target_value": 15, "tempo": "3-1-1", "rest_seconds": 60},
        ],
    },
    {
        "slug": "toes_to_bar",
        "name": "Hanging Toes-to-Bar",
        "category": "core",
        "metric_type": "reps",
        "description": "Dynamic anterior chain calisthenics movement challenging rectus abdominis, hip flexors, and grip strength.",
        "technique_tips": "Engage lats in active hang to prevent backward swinging. Contract core dynamically to lift legs and touch toes to the bar with controlled return.",
        "progressions": [
            {"difficulty_tier": "light", "progression_name": "Hanging Knee Raises", "target_sets": 3, "target_value": 10, "tempo": "3-1-1", "rest_seconds": 60},
            {"difficulty_tier": "medium", "progression_name": "Hanging Leg Raises (to 90°)", "target_sets": 4, "target_value": 10, "tempo": "3-1-1", "rest_seconds": 60},
            {"difficulty_tier": "hard", "progression_name": "Strict Hanging Toes-to-Bar", "target_sets": 4, "target_value": 12, "tempo": "3-1-1", "rest_seconds": 60},
        ],
    },
    {
        "slug": "l_sit_bars",
        "name": "Parallel Bar L-Sit",
        "category": "core",
        "metric_type": "seconds",
        "description": "Isometric core and active shoulder depression hold keeping legs extended horizontally at a 90-degree angle to torso.",
        "technique_tips": "Lock out elbows with active shoulder depression, compress abs and quadriceps hard, keep toes pointed and legs parallel to ground without sagging.",
        "progressions": [
            {"difficulty_tier": "light", "progression_name": "Tuck L-Sit Hold", "target_sets": 3, "target_value": 15, "tempo": "3-1-1", "rest_seconds": 60},
            {"difficulty_tier": "medium", "progression_name": "Single-Leg Extended L-Sit Hold", "target_sets": 4, "target_value": 20, "tempo": "3-1-1", "rest_seconds": 60},
            {"difficulty_tier": "hard", "progression_name": "Full Parallel Bar L-Sit Hold", "target_sets": 4, "target_value": 25, "tempo": "3-1-1", "rest_seconds": 60},
        ],
    },
    # Legs & Cardio Block
    {
        "slug": "bulgarian_split_squats",
        "name": "Bulgarian Split Squats",
        "category": "legs",
        "metric_type": "reps",
        "description": "Unilateral lower body movement producing high quadriceps, gluteal, and stabilizing muscle hypertrophy without spinal compression.",
        "technique_tips": "Elevate rear foot on bench (instep flat), keep front knee tracking over middle toes, descend into deep hip flexion while keeping torso slightly forward to bias glutes.",
        "progressions": [
            {"difficulty_tier": "light", "progression_name": "Assisted Split Squats", "target_sets": 3, "target_value": 10, "tempo": "3-1-1", "rest_seconds": 60},
            {"difficulty_tier": "medium", "progression_name": "Bodyweight Bulgarian Split Squats", "target_sets": 4, "target_value": 12, "tempo": "3-1-1", "rest_seconds": 60},
            {"difficulty_tier": "hard", "progression_name": "Deficit Bulgarian Split Squats (Pause at bottom)", "target_sets": 4, "target_value": 15, "tempo": "3-1-1", "rest_seconds": 60},
        ],
    },
    {
        "slug": "cossack_squats",
        "name": "Cossack Squats",
        "category": "legs",
        "metric_type": "reps",
        "description": "Frontal plane lateral squat developing hip mobility, adductor flexibility, and knee tendon resilience.",
        "technique_tips": "Keep working heel firmly planted on floor, opposite leg straight with toes rotated upward, sink as deep as mobility permits while maintaining neutral spine.",
        "progressions": [
            {"difficulty_tier": "light", "progression_name": "Supported Cossack Squats", "target_sets": 3, "target_value": 8, "tempo": "3-1-1", "rest_seconds": 60},
            {"difficulty_tier": "medium", "progression_name": "Full Bodyweight Cossack Squats", "target_sets": 4, "target_value": 10, "tempo": "3-1-1", "rest_seconds": 60},
            {"difficulty_tier": "hard", "progression_name": "Deficit / Pause Cossack Squats", "target_sets": 4, "target_value": 12, "tempo": "3-1-1", "rest_seconds": 60},
        ],
    },
    {
        "slug": "running_intervals",
        "name": "Interval Running",
        "category": "cardio",
        "metric_type": "minutes",
        "description": "Anaerobic and aerobic conditioning sprint protocol alternating maximum effort bursts with active walking recovery.",
        "technique_tips": "Sprint at 85-90% maximal speed with high knee drive and midfoot landing. Walk actively during rest intervals to flush lactic acid and regulate heart rate.",
        "progressions": [
            {"difficulty_tier": "light", "progression_name": "6 Intervals: 45s run / 90s walk", "target_sets": 1, "target_value": 15, "tempo": "3-1-1", "rest_seconds": 90},
            {"difficulty_tier": "medium", "progression_name": "8 Intervals: 60s sprint / 90s walk", "target_sets": 1, "target_value": 20, "tempo": "3-1-1", "rest_seconds": 90},
            {"difficulty_tier": "hard", "progression_name": "10 Intervals: 60s max sprint / 60s jog", "target_sets": 1, "target_value": 25, "tempo": "3-1-1", "rest_seconds": 60},
        ],
    },
    {
        "slug": "running_zone2",
        "name": "Steady Zone 2 Tempo Run",
        "category": "cardio",
        "metric_type": "minutes",
        "description": "Low-intensity steady-state aerobic conditioning optimizing mitochondrial density, fat oxidation, and vascular recovery.",
        "technique_tips": "Maintain a steady conversational pace strictly through nasal breathing (approx. 65-75% max HR). Avoid spikes in speed, focus on rhythmic light cadence (~170-180 spm).",
        "progressions": [
            {"difficulty_tier": "light", "progression_name": "Zone 2 Run / Brisk Walk", "target_sets": 1, "target_value": 20, "tempo": "3-1-1", "rest_seconds": 0},
            {"difficulty_tier": "medium", "progression_name": "Zone 2 Steady Tempo Run", "target_sets": 1, "target_value": 25, "tempo": "3-1-1", "rest_seconds": 0},
            {"difficulty_tier": "hard", "progression_name": "Zone 2 Endurance Tempo Run", "target_sets": 1, "target_value": 30, "tempo": "3-1-1", "rest_seconds": 0},
        ],
    },
]


async def seed_initial_data() -> None:
    """Seed initial exercises, progressions, and 30-day cycle plan idempotently."""
    logger.info("Checking and seeding database with initial data...")

    async with get_db_session() as session:
        # 1. Seed Exercises & Progressions
        exercise_map: Dict[str, Exercise] = {}

        # Fetch existing exercises
        existing_exercises = (await session.scalars(select(Exercise))).all()
        existing_by_slug = {e.slug: e for e in existing_exercises}

        for item in EXERCISES_DATA:
            slug = item["slug"]
            if slug in existing_by_slug:
                exercise = existing_by_slug[slug]
            else:
                exercise = Exercise(
                    slug=slug,
                    name=item["name"],
                    category=item["category"],
                    metric_type=item["metric_type"],
                    description=item["description"],
                    technique_tips=item["technique_tips"],
                )
                session.add(exercise)
                await session.flush()
                logger.info("Added exercise: %s (%s)", exercise.name, exercise.slug)

            exercise_map[slug] = exercise

            # Check progressions
            existing_progs = (
                await session.scalars(
                    select(ExerciseProgression).where(ExerciseProgression.exercise_id == exercise.id)
                )
            ).all()
            existing_tiers = {p.difficulty_tier for p in existing_progs}

            for prog_data in item["progressions"]:
                tier = prog_data["difficulty_tier"]
                if tier not in existing_tiers:
                    progression = ExerciseProgression(
                        exercise_id=exercise.id,
                        difficulty_tier=tier,
                        progression_name=prog_data["progression_name"],
                        target_sets=prog_data["target_sets"],
                        target_value=prog_data["target_value"],
                        tempo=prog_data.get("tempo", "3-1-1"),
                        rest_seconds=prog_data.get("rest_seconds", 60),
                    )
                    session.add(progression)
                    logger.info("Added progression for %s: %s", slug, tier)

        await session.flush()

        # 2. Seed 30-Day Training Cycle
        existing_days = (await session.scalars(select(CycleDay))).all()
        existing_days_by_num = {d.day_number: d for d in existing_days}

        legs_day_counter = 0

        for day_num in range(1, 31):
            modulo = day_num % 4

            if modulo == 1:
                block_type = "A_PUSH"
                title = f"Day {day_num}: Upper Body Push"
                focus_areas = "Chest, Shoulders & Triceps"
                is_rest_day = False
                day_exercise_slugs = ["dips", "decline_pushups", "pike_pushups"]
            elif modulo == 2:
                block_type = "B_PULL"
                title = f"Day {day_num}: Upper Body Pull & Core"
                focus_areas = "Lats, Upper Back, Biceps & Core"
                is_rest_day = False
                day_exercise_slugs = ["pullups", "chinups", "horizontal_rows", "toes_to_bar", "l_sit_bars"]
            elif modulo == 3:
                legs_day_counter += 1
                block_type = "C_LEGS_RUN"
                title = f"Day {day_num}: Lower Body & Aerobic Capacity"
                focus_areas = "Quads, Hamstrings, Hip Mobility & Cardio"
                is_rest_day = False
                # If odd legs day -> running_intervals, if even legs day -> running_zone2
                cardio_slug = "running_intervals" if legs_day_counter % 2 == 1 else "running_zone2"
                day_exercise_slugs = ["bulgarian_split_squats", "cossack_squats", cardio_slug]
            else:  # modulo == 0
                block_type = "REST"
                title = f"Day {day_num}: Full Recovery & Mobility"
                focus_areas = "Active Recovery, Stretching & Joint Health"
                is_rest_day = True
                day_exercise_slugs = []

            if day_num in existing_days_by_num:
                cycle_day = existing_days_by_num[day_num]
            else:
                cycle_day = CycleDay(
                    day_number=day_num,
                    block_type=block_type,
                    title=title,
                    focus_areas=focus_areas,
                    is_rest_day=is_rest_day,
                )
                session.add(cycle_day)
                await session.flush()
                logger.info("Added cycle day: %d (%s)", day_num, block_type)

            # Assign exercises to cycle day if not already assigned
            existing_mappings = (
                await session.scalars(
                    select(CycleDayExercise).where(CycleDayExercise.cycle_day_id == cycle_day.id)
                )
            ).all()

            if not existing_mappings and day_exercise_slugs:
                for order, slug in enumerate(day_exercise_slugs, start=1):
                    ex = exercise_map.get(slug)
                    if ex:
                        session.add(
                            CycleDayExercise(
                                cycle_day_id=cycle_day.id,
                                exercise_id=ex.id,
                                order=order,
                            )
                        )
                logger.info("Assigned %d exercises to Day %d", len(day_exercise_slugs), day_num)

        await session.flush()

    logger.info("Database seeding successfully verified and completed.")


async def main() -> None:
    """CLI entrypoint to initialize tables and seed data."""
    await init_db()
    await seed_initial_data()


if __name__ == "__main__":
    asyncio.run(main())
