import React, { useEffect, useState } from "react";
import { api, triggerHaptic } from "../api";
import { ExerciseDetail, TodayWorkout, UserProfile, WorkoutExerciseInput } from "../types";

interface WorkoutTabProps {
  user: UserProfile;
  workout: TodayWorkout | null;
  loading: boolean;
  onRefresh: () => void;
  onStartRest: (seconds: number) => void;
}

export const WorkoutTab: React.FC<WorkoutTabProps> = ({
  user,
  workout,
  loading,
  onRefresh,
  onStartRest,
}) => {
  // Rules of Hooks: All hooks declared unconditionally at top of component
  const [warmupDone, setWarmupDone] = useState<boolean>(false);
  const [cooldownDone, setCooldownDone] = useState<boolean>(false);
  const [isWarmupOpen, setIsWarmupOpen] = useState<boolean>(false);
  const [isCooldownOpen, setIsCooldownOpen] = useState<boolean>(false);
  const [infoModalExercise, setInfoModalExercise] = useState<ExerciseDetail | null>(null);
  const [completedSets, setCompletedSets] = useState<Record<number, number[]>>({});
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Storage key for keeping workout progress across app minimizations
  const storageKey = workout ? `sportbot_progress_c${user.current_cycle}_d${workout.day_number}` : "";

  // Load progress from localStorage on day/workout change
  useEffect(() => {
    if (!storageKey) return;
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved) {
        const parsed = JSON.parse(saved);
        setWarmupDone(!!parsed.warmupDone);
        setCooldownDone(!!parsed.cooldownDone);
        setCompletedSets(parsed.completedSets || {});
      } else {
        setWarmupDone(false);
        setCooldownDone(false);
        setCompletedSets({});
      }
    } catch {
      // Ignore parsing errors
    }
  }, [storageKey]);

  // Sync progress to localStorage
  const saveProgress = (newWarmup: boolean, newCooldown: boolean, newSets: Record<number, number[]>) => {
    if (!storageKey) return;
    try {
      localStorage.setItem(
        storageKey,
        JSON.stringify({
          warmupDone: newWarmup,
          cooldownDone: newCooldown,
          completedSets: newSets,
        })
      );
    } catch {
      // Ignore quota errors
    }
  };

  const handleToggleWarmup = () => {
    triggerHaptic("light");
    const next = !warmupDone;
    setWarmupDone(next);
    if (next) {
      setIsWarmupOpen(false); // auto-collapse when marked done
    }
    saveProgress(next, cooldownDone, completedSets);
  };

  const handleToggleCooldown = () => {
    triggerHaptic("light");
    const next = !cooldownDone;
    setCooldownDone(next);
    if (next) {
      setIsCooldownOpen(false); // auto-collapse when marked done
    }
    saveProgress(warmupDone, next, completedSets);
  };

  const handleToggleSet = (exerciseId: number, setIndex: number, restSeconds: number) => {
    triggerHaptic("medium");
    const currentList = completedSets[exerciseId] || [];
    const isCompleted = currentList.includes(setIndex);

    let updatedList: number[];
    if (isCompleted) {
      updatedList = currentList.filter((idx) => idx !== setIndex);
    } else {
      updatedList = [...currentList, setIndex];
      // Trigger rest timer on completing a set
      onStartRest(restSeconds || 60);
    }

    const updatedSets = { ...completedSets, [exerciseId]: updatedList };
    setCompletedSets(updatedSets);
    saveProgress(warmupDone, cooldownDone, updatedSets);
  };

  const handleCompleteWorkout = async () => {
    if (!workout) return;
    triggerHaptic("heavy");
    setSubmitting(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    const exerciseLogs: WorkoutExerciseInput[] = (workout.exercises || []).map((ex) => {
      const setsDone = (completedSets[ex.id] || []).length;
      return {
        exercise_id: ex.id,
        sets_completed: setsDone,
        value_completed: setsDone * ex.target_value,
        is_completed: setsDone >= ex.target_sets,
      };
    });

    try {
      const res = await api.completeWorkout({
        day_number: workout.day_number,
        cycle_number: user.current_cycle,
        duration_seconds: 3000,
        difficulty_mode: user.difficulty_mode,
        exercises: exerciseLogs,
      });

      triggerHaptic("success");
      setSuccessMsg(res.message);
      // Clean up localStorage for completed day
      if (storageKey) localStorage.removeItem(storageKey);
      setTimeout(() => {
        onRefresh();
        setSuccessMsg(null);
      }, 1500);
    } catch (err: any) {
      triggerHaptic("error");
      setErrorMsg(err.message || "Failed to complete workout");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-zinc-400">
        <div className="w-8 h-8 border-2 border-red-500 border-t-transparent rounded-full animate-spin mb-3"></div>
        <span className="text-sm font-medium">Loading training protocol...</span>
      </div>
    );
  }

  if (!workout) {
    return (
      <div className="p-6 text-center text-zinc-400">
        <p className="text-sm font-medium">No active workout data available.</p>
        <button
          type="button"
          onClick={onRefresh}
          className="mt-4 px-4 py-2 bg-red-600 rounded-xl text-white font-semibold text-xs"
        >
          Retry
        </button>
      </div>
    );
  }

  // Rest Day Screen (Stealth Dark)
  if (workout.is_rest_day) {
    return (
      <div className="space-y-4 animate-fade-in">
        <div className="p-5 rounded-2xl bg-[#151720] border border-[#222533] text-center shadow-sm">
          <div className="w-12 h-12 mx-auto mb-2 rounded-2xl bg-[#222533] flex items-center justify-center text-xl">
            🌴
          </div>
          <span className="text-xs uppercase tracking-wider text-zinc-400 font-semibold">
            Day {workout.day_number} of 30
          </span>
          <h2 className="text-xl font-bold text-white mt-0.5 tracking-tight">Full Recovery & Rest</h2>
          <p className="text-xs text-zinc-400 mt-2 max-w-sm mx-auto leading-relaxed">
            {workout.recovery_guidelines ||
              "Hydration (min 2.5–3L water), 8+ hours quality sleep, and light walking. Honor your central nervous system recovery."}
          </p>
        </div>

        <div className="grid grid-cols-1 gap-2.5">
          <div className="p-3.5 rounded-xl bg-[#151720] border border-[#222533] flex items-center gap-3">
            <span className="text-xl">💧</span>
            <div>
              <div className="text-sm font-semibold text-white">Hydration & Electrolytes</div>
              <div className="text-xs text-zinc-400">Drink 2.5–3L clean water to flush cellular metabolic waste.</div>
            </div>
          </div>
          <div className="p-3.5 rounded-xl bg-[#151720] border border-[#222533] flex items-center gap-3">
            <span className="text-xl">😴</span>
            <div>
              <div className="text-sm font-semibold text-white">Deep Anabolic Sleep</div>
              <div className="text-xs text-zinc-400">Aim for 8–9 hours. Growth hormone release peaks in slow-wave sleep.</div>
            </div>
          </div>
          <div className="p-3.5 rounded-xl bg-[#151720] border border-[#222533] flex items-center gap-3">
            <span className="text-xl">🚶</span>
            <div>
              <div className="text-sm font-semibold text-white">Active Joint Mobility</div>
              <div className="text-xs text-zinc-400">20–30 min gentle walk or light stretching to circulate synovial fluid.</div>
            </div>
          </div>
        </div>

        <button
          type="button"
          onClick={handleCompleteWorkout}
          disabled={submitting}
          className="w-full py-4 rounded-xl font-bold uppercase tracking-wider text-white bg-red-600 hover:bg-red-500 active:scale-[0.98] transition-all shadow-md text-sm"
        >
          {submitting ? "Saving..." : "COMPLETE WORKOUT"}
        </button>
      </div>
    );
  }

  // Active Workout Day (Stealth Dark / Whoop Style)
  return (
    <div className="space-y-3.5 animate-fade-in pb-4">
      {/* Block Header (Clean, low-profile) */}
      <div className="p-4 rounded-2xl bg-[#151720] border border-[#222533] shadow-sm">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-white tracking-tight">
            Day {workout.day_number}: {workout.title.replace(/^Day \d+:\s*/i, "")}
          </h2>
          <span className="text-[11px] font-semibold text-zinc-400 bg-[#222533] px-2.5 py-0.5 rounded-md">
            {workout.block_type.replace("_", " ")}
          </span>
        </div>
        <p className="text-xs text-zinc-400 mt-1">
          {workout.exercises.length} exercises • 50–55 min • {workout.focus_areas}
        </p>
      </div>

      {/* Notifications */}
      {errorMsg && (
        <div className="p-3.5 rounded-xl bg-red-950/80 border border-red-600/50 text-red-200 text-xs font-semibold">
          ⚠️ {errorMsg}
        </div>
      )}
      {successMsg && (
        <div className="p-3.5 rounded-xl bg-emerald-950/80 border border-emerald-600/50 text-emerald-200 text-xs font-semibold">
          ✓ {successMsg}
        </div>
      )}

      {/* Section 1: Dynamic Warm-Up Smart Accordion */}
      <div className="rounded-2xl bg-[#151720] border border-[#222533] overflow-hidden transition-all shadow-sm">
        <div className="p-3.5 flex items-center justify-between gap-2">
          <button
            type="button"
            onClick={() => {
              triggerHaptic("light");
              setIsWarmupOpen(!isWarmupOpen);
            }}
            className="flex items-center gap-2.5 text-left flex-1"
          >
            <span className="text-base">⚡️</span>
            <div>
              <div className="text-xs font-semibold text-white">
                Warm-up <span className="text-zinc-500 font-normal">• 5 mobility drills • 8–10 min</span>
              </div>
            </div>
          </button>
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={handleToggleWarmup}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                warmupDone
                  ? "bg-emerald-600/90 text-white shadow-sm"
                  : "bg-[#222533] text-zinc-300 hover:text-white"
              }`}
            >
              {warmupDone ? "✓ Done" : "Mark Done"}
            </button>
            <button
              type="button"
              onClick={() => {
                triggerHaptic("light");
                setIsWarmupOpen(!isWarmupOpen);
              }}
              className="w-7 h-7 flex items-center justify-center text-zinc-500 hover:text-zinc-300 text-xs"
              aria-label="Toggle Warm-up details"
            >
              {isWarmupOpen ? "▲" : "▼"}
            </button>
          </div>
        </div>

        {isWarmupOpen && (
          <div className="p-3.5 pt-1 border-t border-[#222533] space-y-2">
            {workout.warmup_steps.map((step) => (
              <div
                key={step.order}
                className="flex items-start gap-2.5 text-xs text-zinc-300 bg-[#0c0d12] p-2.5 rounded-xl border border-[#222533]"
              >
                <span className="text-xs text-zinc-500 font-bold shrink-0">{step.order}.</span>
                <div>
                  <span className="font-semibold text-zinc-200">{step.title}:</span>{" "}
                  <span className="text-zinc-400">{step.description}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Section 2: Main Protocol Exercises */}
      <div className="space-y-3">
        {workout.exercises.map((ex, exIdx) => {
          const completedSetIndices = completedSets[ex.id] || [];
          const metricSuffix = ex.metric_type === "reps" ? "reps" : ex.metric_type === "seconds" ? "sec" : "min";

          return (
            <div
              key={ex.id}
              className="p-4 rounded-2xl bg-[#151720] border border-[#222533] transition-all space-y-3 shadow-sm"
            >
              {/* Exercise Header: Clean White Title + Info Button */}
              <div className="flex items-center justify-between gap-2">
                <h4 className="text-sm font-bold text-white tracking-tight">
                  {exIdx + 1}. {ex.name}
                </h4>
                <button
                  type="button"
                  onClick={() => {
                    triggerHaptic("light");
                    setInfoModalExercise(ex);
                  }}
                  className="px-2.5 py-1 rounded-md bg-[#222533] hover:bg-[#2c3042] text-zinc-300 text-xs font-medium transition-colors"
                >
                  Info
                </button>
              </div>

              {/* Compact Parameters Line (neutral gray) */}
              <div className="text-xs text-zinc-400 font-normal">
                Target: <span className="text-zinc-200 font-medium">{ex.target_sets} sets × {ex.target_value} {metricSuffix}</span>
                {"  •  "}
                Tempo: <span className="text-zinc-200 font-medium">{ex.tempo}</span>
                {"  •  "}
                Rest: <span className="text-zinc-200 font-medium">{ex.rest_seconds || 60}s</span>
              </div>

              {/* Interactive Sets Grid */}
              <div className="grid grid-cols-4 gap-2 pt-0.5">
                {Array.from({ length: ex.target_sets }).map((_, setIdx) => {
                  const setNum = setIdx + 1;
                  const isChecked = completedSetIndices.includes(setNum);

                  return (
                    <button
                      key={setNum}
                      type="button"
                      onClick={() => handleToggleSet(ex.id, setNum, ex.rest_seconds)}
                      className={`py-2.5 px-2 rounded-xl text-xs font-semibold flex flex-col items-center justify-center transition-all ${
                        isChecked
                          ? "bg-red-600 text-white font-bold shadow-md border border-red-500"
                          : "bg-[#1c1f2b] text-zinc-300 hover:text-white border border-[#272b3b] hover:border-zinc-600"
                      }`}
                    >
                      <span className={`text-[10px] font-medium ${isChecked ? "text-red-100" : "text-zinc-400"}`}>
                        Set {setNum}
                      </span>
                      <span className="text-sm font-bold mt-0.5">
                        {isChecked ? "✓" : `${ex.target_value}`}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {/* Section 3: Cool-Down & Recovery Smart Accordion */}
      <div className="rounded-2xl bg-[#151720] border border-[#222533] overflow-hidden transition-all shadow-sm">
        <div className="p-3.5 flex items-center justify-between gap-2">
          <button
            type="button"
            onClick={() => {
              triggerHaptic("light");
              setIsCooldownOpen(!isCooldownOpen);
            }}
            className="flex items-center gap-2.5 text-left flex-1"
          >
            <span className="text-base">🧘</span>
            <div>
              <div className="text-xs font-semibold text-white">
                Cool-down <span className="text-zinc-500 font-normal">• 4 stretches • 5–7 min</span>
              </div>
            </div>
          </button>
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={handleToggleCooldown}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                cooldownDone
                  ? "bg-emerald-600/90 text-white shadow-sm"
                  : "bg-[#222533] text-zinc-300 hover:text-white"
              }`}
            >
              {cooldownDone ? "✓ Done" : "Mark Done"}
            </button>
            <button
              type="button"
              onClick={() => {
                triggerHaptic("light");
                setIsCooldownOpen(!isCooldownOpen);
              }}
              className="w-7 h-7 flex items-center justify-center text-zinc-500 hover:text-zinc-300 text-xs"
              aria-label="Toggle Cool-down details"
            >
              {isCooldownOpen ? "▲" : "▼"}
            </button>
          </div>
        </div>

        {isCooldownOpen && (
          <div className="p-3.5 pt-1 border-t border-[#222533] space-y-2">
            {workout.cooldown_steps.map((step) => (
              <div
                key={step.order}
                className="flex items-start gap-2.5 text-xs text-zinc-300 bg-[#0c0d12] p-2.5 rounded-xl border border-[#222533]"
              >
                <span className="text-xs text-zinc-500 font-bold shrink-0">{step.order}.</span>
                <div>
                  <span className="font-semibold text-zinc-200">{step.title}:</span>{" "}
                  <span className="text-zinc-400">{step.description}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Complete Workout Action (Clean, without fire emoji) */}
      <div className="pt-2">
        <button
          type="button"
          onClick={handleCompleteWorkout}
          disabled={submitting}
          className="w-full py-4 rounded-xl font-bold text-sm uppercase tracking-wider text-white bg-red-600 hover:bg-red-500 active:scale-[0.98] transition-all shadow-md flex items-center justify-center disabled:opacity-60"
        >
          <span>{submitting ? "Saving..." : "COMPLETE WORKOUT"}</span>
        </button>
      </div>

      {/* Exercise Detail Modal (Stealth Dark) */}
      {infoModalExercise && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in">
          <div className="w-full max-w-md bg-[#151720] border border-[#222533] rounded-2xl p-5 shadow-2xl space-y-4 max-h-[85vh] overflow-y-auto no-scrollbar">
            {/* Header */}
            <div className="flex items-start justify-between gap-3 border-b border-[#222533] pb-3">
              <div>
                <span className="text-[10px] uppercase tracking-wider text-zinc-400 font-semibold block">
                  {infoModalExercise.category}
                </span>
                <h3 className="text-base font-bold text-white tracking-tight mt-0.5">{infoModalExercise.name}</h3>
                <span className="text-xs text-zinc-400 font-medium mt-0.5 block">
                  {infoModalExercise.progression_name}
                </span>
              </div>
              <button
                type="button"
                onClick={() => {
                  triggerHaptic("light");
                  setInfoModalExercise(null);
                }}
                className="w-8 h-8 rounded-full bg-[#222533] hover:bg-[#2c3042] text-zinc-400 hover:text-white flex items-center justify-center transition-colors text-sm"
                aria-label="Close modal"
              >
                ✕
              </button>
            </div>

            {/* Target Parameters Summary */}
            <div className="p-3 rounded-xl bg-[#0c0d12] border border-[#222533] grid grid-cols-3 gap-2 text-center text-xs">
              <div>
                <span className="text-[10px] text-zinc-500 uppercase tracking-wider block">Target</span>
                <span className="font-semibold text-white">
                  {infoModalExercise.target_sets} × {infoModalExercise.target_value}{" "}
                  {infoModalExercise.metric_type === "reps" ? "reps" : "sec"}
                </span>
              </div>
              <div>
                <span className="text-[10px] text-zinc-500 uppercase tracking-wider block">Tempo</span>
                <span className="font-semibold text-white">{infoModalExercise.tempo}</span>
              </div>
              <div>
                <span className="text-[10px] text-zinc-500 uppercase tracking-wider block">Rest</span>
                <span className="font-semibold text-white">{infoModalExercise.rest_seconds || 60}s</span>
              </div>
            </div>

            {/* Biomechanics & Execution */}
            <div className="space-y-1.5">
              <div className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
                Biomechanics & Execution
              </div>
              <p className="text-xs text-zinc-300 leading-relaxed">
                {infoModalExercise.description ||
                  "Compound calisthenics movement targeting prime mover hypertrophy and joint resilience."}
              </p>
            </div>

            {/* Joint & Safety Tips for 85kg */}
            <div className="p-3.5 rounded-xl bg-[#0c0d12] border border-[#222533] text-xs">
              <div className="font-semibold text-zinc-300 mb-1 flex items-center gap-1.5">
                <span>💡</span>
                <span>Safety Tips for 85 kg Bodyweight</span>
              </div>
              <p className="text-zinc-400 leading-relaxed">
                {infoModalExercise.technique_tips ||
                  "Maintain active scapular control, strict core bracing, and avoid momentum."}
              </p>
            </div>

            {/* Close Action */}
            <button
              type="button"
              onClick={() => {
                triggerHaptic("light");
                setInfoModalExercise(null);
              }}
              className="w-full py-2.5 rounded-xl bg-[#222533] hover:bg-[#2c3042] text-white font-medium text-xs transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
