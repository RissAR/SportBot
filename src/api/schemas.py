"""Pydantic v2 schemas and data contracts for SportBot REST API."""

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------
# User Schemas
# ---------------------------------------------------------
class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    telegram_id: int
    username: Optional[str] = None
    current_day: int
    current_cycle: int
    difficulty_mode: str
    total_workouts_completed: int
    latest_weight: Optional[float] = None


class DifficultyUpdateRequest(BaseModel):
    difficulty_mode: Literal["light", "medium", "hard"]


# ---------------------------------------------------------
# Warmup & Cooldown Protocols
# ---------------------------------------------------------
class WarmupStep(BaseModel):
    order: int
    title: str
    duration_seconds: int
    description: str


class CooldownStep(BaseModel):
    order: int
    title: str
    duration_seconds: int
    description: str


DEFAULT_WARMUP_STEPS: List[WarmupStep] = [
    WarmupStep(
        order=1,
        title="Wrists Mobility & Rotations",
        duration_seconds=60,
        description="Gentle circular rotations and wrist flexor/extensor stretches on the ground to prepare joints for dips and push-ups.",
    ),
    WarmupStep(
        order=2,
        title="Shoulder Arm Circles & Dislocates",
        duration_seconds=60,
        description="Dynamic forward and backward arm circles and pass-throughs to activate deltoids and rotators.",
    ),
    WarmupStep(
        order=3,
        title="Scapular Pulls & Push-up Shrugs",
        duration_seconds=60,
        description="Active depression and elevation in dead hang and plank to prime scapular stabilizers for load.",
    ),
    WarmupStep(
        order=4,
        title="Hip Openers & Deep Squat Hold",
        duration_seconds=60,
        description="Bodyweight deep squat sit with active hip external rotation and thoracic reach.",
    ),
    WarmupStep(
        order=5,
        title="Knee Flexion & Quad Activation",
        duration_seconds=60,
        description="Light dynamic lunges and knee circles to warm synovial fluid in patellar ligaments.",
    ),
]

DEFAULT_COOLDOWN_STEPS: List[CooldownStep] = [
    CooldownStep(
        order=1,
        title="Doorway / Bar Chest Stretch",
        duration_seconds=45,
        description="Gentle static stretch across pectoralis major and anterior deltoids to restore resting muscle length.",
    ),
    CooldownStep(
        order=2,
        title="Hanging Lat & Spine Decompression",
        duration_seconds=45,
        description="Relaxed passive dead hang with toes touching floor to gently decompress the thoracic spine and lats.",
    ),
    CooldownStep(
        order=3,
        title="Cat-Cow Spinal Mobility",
        duration_seconds=60,
        description="Slow spinal flexion and extension synchronized with deep breathing to relieve paraspinal tension.",
    ),
    CooldownStep(
        order=4,
        title="Diaphragmatic Box Breathing",
        duration_seconds=60,
        description="Inhale 4s, hold 4s, exhale 4s, hold 4s in supine position to activate parasympathetic nervous recovery.",
    ),
]


# ---------------------------------------------------------
# Workout & Cycle Schemas
# ---------------------------------------------------------
class ExerciseDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    category: str
    metric_type: str
    progression_name: str
    target_sets: int
    target_value: int
    tempo: str
    rest_seconds: int
    description: str
    technique_tips: str


class TodayWorkoutResponse(BaseModel):
    day_number: int
    cycle_number: int
    block_type: str
    title: str
    focus_areas: str
    is_rest_day: bool
    warmup_steps: List[WarmupStep]
    exercises: List[ExerciseDetailResponse]
    cooldown_steps: List[CooldownStep]
    recovery_guidelines: Optional[str] = None


class CycleDaySummary(BaseModel):
    day_number: int
    block_type: str
    title: str
    focus_areas: str
    is_rest_day: bool
    status: Literal["completed", "current", "locked"]


class CycleDaysOverviewResponse(BaseModel):
    cycle_number: int
    current_day: int
    days: List[CycleDaySummary]


# ---------------------------------------------------------
# Workout Completion Schemas
# ---------------------------------------------------------
class WorkoutExerciseInput(BaseModel):
    exercise_id: int
    sets_completed: int
    value_completed: int
    is_completed: bool = True


class WorkoutCompleteRequest(BaseModel):
    day_number: int
    cycle_number: int
    duration_seconds: int = 0
    difficulty_mode: str
    exercises: List[WorkoutExerciseInput] = Field(default_factory=list)


class WorkoutCompleteResponse(BaseModel):
    success: bool
    message: str
    cycle_completed: bool
    next_day: int
    next_cycle: int


# ---------------------------------------------------------
# Weight & Admin Schemas
# ---------------------------------------------------------
class WeightLogRequest(BaseModel):
    weight_kg: float
    cycle_number: int


class WeightLogResponse(BaseModel):
    id: int
    weight_kg: float
    cycle_number: int
    logged_at: str
    is_cycle_reset: bool


class WeightHistoryItem(BaseModel):
    id: int
    weight_kg: float
    cycle_number: int
    logged_at: str


class WeightHistoryResponse(BaseModel):
    history: List[WeightHistoryItem]


class AdminMetricsResponse(BaseModel):
    total_athletes: int
    total_workouts_completed: int
    difficulty_distribution: Dict[str, int]
    active_cycles_distribution: Dict[int, int]
