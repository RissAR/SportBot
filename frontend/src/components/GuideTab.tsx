import React, { useState } from "react";
import { triggerHaptic } from "../api";

interface GuideExercise {
  slug: string;
  name: string;
  category: "push" | "pull" | "legs" | "core" | "cardio";
  metric: string;
  description: string;
  safetyCues: string;
  progressions: {
    light: string;
    medium: string;
    hard: string;
  };
}

const EXERCISE_GUIDE_DATA: GuideExercise[] = [
  {
    slug: "dips",
    name: "Parallel Bar Dips",
    category: "push",
    metric: "Reps",
    description: "Compound bodyweight pushing exercise focusing on the lower pectorals, triceps, and anterior deltoids.",
    safetyCues: "Maintain active scapular depression, lean torso forward ~45° to target chest, keep elbows tucked at ~45° (never flare out 90° to protect rotator cuffs at 85kg bw), maintain hollow body.",
    progressions: {
      light: "Bench Dips / Band-Assisted Dips (3 × 8)",
      medium: "Parallel Bar Dips (4 × 12, Tempo: 3-1-1)",
      hard: "Straight Bar / Deficit Dips (4 × 16)",
    },
  },
  {
    slug: "decline_pushups",
    name: "Decline Push-ups",
    category: "push",
    metric: "Reps",
    description: "Push-up variation with feet elevated on a 30-50cm platform, shifting load to clavicular upper pectorals and front deltoids.",
    safetyCues: "Squeeze glutes and brace core to prevent lumbar hyperextension, tuck elbows at 45°, lower with a 3-second eccentric tempo until chest gently touches the floor.",
    progressions: {
      light: "Standard Flat Push-ups (3 × 10)",
      medium: "Decline Push-ups 30cm elevation (4 × 14)",
      hard: "High Decline Push-ups 50cm elevation (4 × 18)",
    },
  },
  {
    slug: "pike_pushups",
    name: "Pike Push-ups",
    category: "push",
    metric: "Reps",
    description: "Vertical pushing bodyweight progression forming an inverted V-shape, loading the anterior and lateral deltoids.",
    safetyCues: "Keep hips high and legs straight, lower head forward forming an equilateral triangle between head and hands, press back up and through to finish with active shoulder elevation.",
    progressions: {
      light: "Incline Pike Push-ups (3 × 8)",
      medium: "Floor Pike Push-ups (4 × 10)",
      hard: "Feet-Elevated Pike Push-ups (4 × 12)",
    },
  },
  {
    slug: "pullups",
    name: "Overhand Pull-ups",
    category: "pull",
    metric: "Reps",
    description: "Full vertical pulling exercise targeting the latissimus dorsi, rhomboids, rear delts, and forearm flexors.",
    safetyCues: "Initiate from a dead hang with active scapular depression and retraction before bending elbows. Drive elbows down into back pockets, pull chest towards the bar without swinging.",
    progressions: {
      light: "Band-Assisted / Negative Pull-ups (3 × 6)",
      medium: "Strict Overhand Pull-ups (4 × 8)",
      hard: "Chest-to-Bar / L-Sit Pull-ups (4 × 12)",
    },
  },
  {
    slug: "chinups",
    name: "Underhand Chin-ups",
    category: "pull",
    metric: "Reps",
    description: "Supinated grip vertical pull engaging the latissimus dorsi with maximal emphasis on biceps brachii recruitment.",
    safetyCues: "Keep shoulders depressed away from ears, initiate pull with lats, squeeze biceps hard at the peak with chin clearing the bar, lower smoothly under full 3-second control.",
    progressions: {
      light: "Band-Assisted / Isometric Chin-ups (3 × 6)",
      medium: "Strict Underhand Chin-ups (4 × 8)",
      hard: "Pause Underhand Chin-ups (4 × 12, 2s peak hold)",
    },
  },
  {
    slug: "horizontal_rows",
    name: "Australian Rows",
    category: "pull",
    metric: "Reps",
    description: "Horizontal bodyweight pulling movement balancing push volume and fortifying the rotator cuff, middle traps, and rhomboids.",
    safetyCues: "Keep body in a rigid plank, retract shoulder blades before pulling, touch lower chest to bar/rings, control eccentric return without dropping shoulders forward.",
    progressions: {
      light: "High-Angle Incline Rows (3 × 10)",
      medium: "Horizontal Australian Rows (4 × 12)",
      hard: "Feet-Elevated Australian Rows (4 × 15)",
    },
  },
  {
    slug: "toes_to_bar",
    name: "Hanging Toes-to-Bar",
    category: "core",
    metric: "Reps",
    description: "Dynamic anterior chain calisthenics movement challenging rectus abdominis, hip flexors, and grip strength.",
    safetyCues: "Engage lats in active hang to prevent backward swinging. Contract core dynamically to lift legs and touch toes to the bar with controlled return.",
    progressions: {
      light: "Hanging Knee Raises (3 × 10)",
      medium: "Hanging Leg Raises to 90° (4 × 10)",
      hard: "Strict Hanging Toes-to-Bar (4 × 12)",
    },
  },
  {
    slug: "l_sit_bars",
    name: "Parallel Bar L-Sit",
    category: "core",
    metric: "Seconds",
    description: "Isometric core and active shoulder depression hold keeping legs extended horizontally at a 90-degree angle to torso.",
    safetyCues: "Lock out elbows with active shoulder depression, compress abs and quadriceps hard, keep toes pointed and legs parallel to ground without sagging.",
    progressions: {
      light: "Tuck L-Sit Hold (3 × 15s)",
      medium: "Single-Leg Extended L-Sit (4 × 20s)",
      hard: "Full Parallel Bar L-Sit (4 × 25s)",
    },
  },
  {
    slug: "bulgarian_split_squats",
    name: "Bulgarian Split Squats",
    category: "legs",
    metric: "Reps",
    description: "Unilateral lower body movement producing high quadriceps, gluteal, and stabilizing muscle hypertrophy without spinal compression.",
    safetyCues: "Elevate rear foot on bench (instep flat), keep front knee tracking over middle toes, descend into deep hip flexion while keeping torso slightly forward to bias glutes.",
    progressions: {
      light: "Assisted Split Squats (3 × 10)",
      medium: "Bodyweight Bulgarian Split Squats (4 × 12)",
      hard: "Deficit Bulgarian Split Squats (4 × 15)",
    },
  },
  {
    slug: "cossack_squats",
    name: "Cossack Squats",
    category: "legs",
    metric: "Reps",
    description: "Frontal plane lateral squat developing hip mobility, adductor flexibility, and knee tendon resilience.",
    safetyCues: "Keep working heel firmly planted on floor, opposite leg straight with toes rotated upward, sink as deep as mobility permits while maintaining neutral spine.",
    progressions: {
      light: "Supported Cossack Squats (3 × 8)",
      medium: "Full Bodyweight Cossack Squats (4 × 10)",
      hard: "Deficit / Pause Cossack Squats (4 × 12)",
    },
  },
  {
    slug: "running_intervals",
    name: "Interval Running",
    category: "cardio",
    metric: "Minutes",
    description: "Anaerobic and aerobic conditioning sprint protocol alternating maximum effort bursts with active walking recovery.",
    safetyCues: "Sprint at 85-90% maximal speed with high knee drive and midfoot landing. Walk actively during rest intervals to flush lactic acid and regulate heart rate.",
    progressions: {
      light: "6 Intervals: 45s run / 90s walk (15 min)",
      medium: "8 Intervals: 60s sprint / 90s walk (20 min)",
      hard: "10 Intervals: 60s max sprint / 60s jog (25 min)",
    },
  },
  {
    slug: "running_zone2",
    name: "Steady Zone 2 Tempo Run",
    category: "cardio",
    metric: "Minutes",
    description: "Low-intensity steady-state aerobic conditioning optimizing mitochondrial density, fat oxidation, and vascular recovery.",
    safetyCues: "Maintain a steady conversational pace strictly through nasal breathing (approx. 65-75% max HR). Avoid spikes in speed, focus on rhythmic light cadence (~170-180 spm).",
    progressions: {
      light: "Zone 2 Run / Brisk Walk (20 min)",
      medium: "Zone 2 Steady Tempo Run (25 min)",
      hard: "Zone 2 Endurance Tempo Run (30 min)",
    },
  },
];

export const GuideTab: React.FC = () => {
  // Rules of Hooks: All hooks at top level
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [expandedSlug, setExpandedSlug] = useState<string | null>(null);

  const categories = [
    { id: "all", label: "All" },
    { id: "push", label: "💪 Push" },
    { id: "pull", label: "🧗 Pull" },
    { id: "legs", label: "🦵 Legs" },
    { id: "core", label: "⚡️ Core" },
    { id: "cardio", label: "🏃 Cardio" },
  ];

  const filteredExercises =
    selectedCategory === "all"
      ? EXERCISE_GUIDE_DATA
      : EXERCISE_GUIDE_DATA.filter((ex) => ex.category === selectedCategory);

  const toggleExpand = (slug: string) => {
    triggerHaptic("light");
    setExpandedSlug(expandedSlug === slug ? null : slug);
  };

  return (
    <div className="space-y-4 animate-fade-in pb-4">
      {/* Guide Header (Stealth Dark) */}
      <div className="p-4 rounded-2xl bg-[#151720] border border-[#222533] shadow-sm">
        <span className="text-xs uppercase tracking-wider text-zinc-400 font-semibold">
          Movement Library
        </span>
        <h2 className="text-base font-bold text-white tracking-tight mt-0.5">EXERCISE TECHNIQUE GUIDE</h2>
        <p className="text-xs text-zinc-400 mt-1 leading-relaxed">
          Injury-prevention form cues, joint angles, and progressive levers for 85 kg athletes.
        </p>
      </div>

      {/* Category Pills */}
      <div className="flex gap-2 overflow-x-auto pb-1 no-scrollbar touch-pan-x">
        {categories.map((cat) => (
          <button
            key={cat.id}
            type="button"
            onClick={() => {
              triggerHaptic("light");
              setSelectedCategory(cat.id);
            }}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
              selectedCategory === cat.id
                ? "bg-[#272b3b] text-white border border-zinc-600 shadow-sm"
                : "bg-[#151720] text-zinc-400 hover:text-white border border-[#222533]"
            }`}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {/* Exercises List */}
      <div className="space-y-2.5">
        {filteredExercises.map((ex) => {
          const isExpanded = expandedSlug === ex.slug;

          return (
            <div
              key={ex.slug}
              className="rounded-2xl bg-[#151720] border border-[#222533] overflow-hidden transition-all shadow-sm"
            >
              <button
                type="button"
                onClick={() => toggleExpand(ex.slug)}
                className="w-full p-4 flex items-center justify-between text-left hover:bg-white/[0.01]"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-bold text-white tracking-tight">{ex.name}</h3>
                    <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-md bg-[#222533] text-zinc-300">
                      {ex.category}
                    </span>
                  </div>
                  <div className="text-xs text-zinc-400 mt-0.5 line-clamp-1">{ex.description}</div>
                </div>
                <span className="text-zinc-500 text-xs ml-2">{isExpanded ? "▲" : "▼"}</span>
              </button>

              {/* Expanded Card Details */}
              {isExpanded && (
                <div className="px-4 pb-4 pt-1 border-t border-[#222533] space-y-3 text-xs">
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-1 flex items-center gap-1.5">
                      <span>📖</span>
                      <span>Biomechanics & Execution</span>
                    </div>
                    <p className="text-zinc-300 leading-relaxed">{ex.description}</p>
                  </div>

                  <div className="p-3 rounded-xl bg-[#0c0d12] border border-[#222533] text-xs">
                    <div className="font-semibold text-zinc-300 mb-1 flex items-center gap-1.5">
                      <span>💡</span>
                      <span>Safety Tips for 85 kg Bodyweight</span>
                    </div>
                    <p className="text-zinc-400 leading-relaxed">{ex.safetyCues}</p>
                  </div>

                  <div className="space-y-2 pt-1">
                    <div className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
                      Progression Tiers
                    </div>
                    <div className="grid gap-2">
                      <div className="p-2.5 rounded-xl bg-[#0c0d12] border border-[#222533] flex items-start gap-2.5">
                        <span className="px-2 py-0.5 rounded-md bg-[#222533] text-zinc-300 text-[11px] font-semibold tracking-wide shrink-0">
                          Light
                        </span>
                        <span className="text-xs text-zinc-300 leading-snug">
                          {ex.progressions.light}
                        </span>
                      </div>
                      <div className="p-2.5 rounded-xl bg-[#0c0d12] border border-[#222533] flex items-start gap-2.5">
                        <span className="px-2 py-0.5 rounded-md bg-[#272b3b] text-zinc-200 text-[11px] font-semibold tracking-wide shrink-0">
                          Medium
                        </span>
                        <span className="text-xs text-zinc-300 leading-snug">
                          {ex.progressions.medium}
                        </span>
                      </div>
                      <div className="p-2.5 rounded-xl bg-[#0c0d12] border border-[#222533] flex items-start gap-2.5">
                        <span className="px-2 py-0.5 rounded-md bg-[#222533] text-zinc-200 text-[11px] font-semibold tracking-wide shrink-0">
                          Hard
                        </span>
                        <span className="text-xs text-zinc-300 leading-snug">
                          {ex.progressions.hard}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
