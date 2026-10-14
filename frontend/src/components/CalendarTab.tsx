import React, { useEffect, useState } from "react";
import { api, triggerHaptic } from "../api";
import { CycleDaySummary, TodayWorkout, UserProfile } from "../types";

interface CalendarTabProps {
  user: UserProfile;
}

export const CalendarTab: React.FC<CalendarTabProps> = ({ user }) => {
  // Rules of Hooks: declared at top
  const [days, setDays] = useState<CycleDaySummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedDayNum, setSelectedDayNum] = useState<number | null>(null);
  const [dayDetails, setDayDetails] = useState<TodayWorkout | null>(null);
  const [modalLoading, setModalLoading] = useState<boolean>(false);

  useEffect(() => {
    let isMounted = true;
    const loadDays = async () => {
      try {
        const res = await api.fetchCycleDays();
        if (isMounted) {
          setDays(res.days);
        }
      } catch (err) {
        console.error("Failed to load cycle days:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };
    loadDays();
    return () => {
      isMounted = false;
    };
  }, [user.current_day]);

  const handleOpenDay = async (dayNum: number) => {
    triggerHaptic("light");
    setSelectedDayNum(dayNum);
    setModalLoading(true);
    setDayDetails(null);

    try {
      const details = await api.fetchDayDetails(dayNum);
      setDayDetails(details);
    } catch (err) {
      console.error("Failed to fetch day details:", err);
    } finally {
      setModalLoading(false);
    }
  };

  const handleCloseModal = () => {
    triggerHaptic("light");
    setSelectedDayNum(null);
    setDayDetails(null);
  };

  const getBlockTag = (blockType: string, isRest: boolean) => {
    if (isRest) return "REST";
    if (blockType.includes("PUSH")) return "PUSH";
    if (blockType.includes("PULL")) return "PULL";
    if (blockType.includes("LEGS")) return "LEGS";
    return blockType.replace("_", " ");
  };

  const getExerciseCountLabel = (blockType: string, isRest: boolean) => {
    if (isRest) return "Rest Day";
    if (blockType.includes("PULL")) return "5 Exercises";
    if (blockType.includes("PUSH")) return "3 Exercises";
    if (blockType.includes("LEGS")) return "3 Exercises";
    return "Training Day";
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-zinc-400">
        <div className="w-8 h-8 border-2 border-red-500 border-t-transparent rounded-full animate-spin mb-3"></div>
        <span className="text-sm">Loading 30-day schedule...</span>
      </div>
    );
  }

  return (
    <div className="space-y-4 animate-fade-in pb-4">
      {/* Calendar Header (Stealth Dark) */}
      <div className="p-4 rounded-2xl bg-[#151720] border border-[#222533] flex items-center justify-between">
        <div>
          <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
            Cycle {user.current_cycle}
          </span>
          <h2 className="text-base font-bold text-white tracking-tight mt-0.5">30-Day Training Calendar</h2>
        </div>
        <div className="text-right">
          <span className="text-xs font-semibold text-zinc-300">
            Day {user.current_day} of 30
          </span>
          <div className="text-[11px] text-zinc-400 mt-0.5">
            {Math.round(((user.current_day - 1) / 30) * 100)}% Complete
          </div>
        </div>
      </div>

      {/* 30-Day Grid (Clean ergonomic tiles, no truncated text) */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
        {days.map((day) => {
          const isCurrent = day.status === "current";
          const isCompleted = day.status === "completed";
          const isLocked = day.status === "locked";

          let borderClass = "border-[#222533]";
          let bgClass = "bg-[#151720]";

          if (isCurrent) {
            borderClass = "border-red-500/80 shadow-[0_0_16px_rgba(239,68,68,0.25)]";
            bgClass = "bg-[#151720]";
          } else if (isCompleted) {
            borderClass = "border-emerald-600/40";
            bgClass = "bg-[#151720]";
          } else if (day.is_rest_day) {
            bgClass = "bg-[#12141c]";
          }

          return (
            <button
              key={day.day_number}
              type="button"
              onClick={() => handleOpenDay(day.day_number)}
              className={`p-3 rounded-2xl border text-left transition-all active:scale-[0.98] relative flex flex-col justify-between h-24 ${borderClass} ${bgClass}`}
            >
              {/* Top Row: Day number + status */}
              <div className="flex items-center justify-between w-full">
                <span className="text-xs font-bold text-white">
                  Day {day.day_number}
                </span>
                {isCompleted && (
                  <span className="text-[10px] font-bold text-emerald-400 bg-emerald-950/60 border border-emerald-600/40 px-1.5 py-0.5 rounded-md">
                    ✓
                  </span>
                )}
                {isCurrent && (
                  <span className="flex h-2 w-2 relative">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
                  </span>
                )}
                {isLocked && (
                  <span className="text-[11px] text-zinc-500">🔒</span>
                )}
              </div>

              {/* Middle Row: Restrained Block Tag */}
              <div>
                <span className="inline-block text-[11px] font-semibold text-zinc-300 uppercase tracking-wider bg-white/[0.04] px-2 py-0.5 rounded-md border border-white/5">
                  {getBlockTag(day.block_type, day.is_rest_day)}
                </span>
              </div>

              {/* Bottom Row: Exercise Count or Rest Day */}
              <div className="text-xs text-zinc-400 font-medium">
                {getExerciseCountLabel(day.block_type, day.is_rest_day)}
              </div>
            </button>
          );
        })}
      </div>

      {/* Day Details Modal (View-Only, Stealth Dark) */}
      {selectedDayNum !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
          <div className="bg-[#151720] border border-[#222533] rounded-2xl max-w-md w-full max-h-[85vh] overflow-y-auto no-scrollbar p-5 space-y-4 shadow-2xl">
            {/* Modal Header */}
            <div className="flex items-start justify-between border-b border-[#222533] pb-3">
              <div>
                <span className="text-[11px] uppercase tracking-wider text-zinc-400 font-semibold block">
                  Inspection View (Day {selectedDayNum})
                </span>
                <h3 className="text-base font-bold text-white tracking-tight mt-0.5">
                  {dayDetails ? dayDetails.title : `Day ${selectedDayNum}`}
                </h3>
              </div>
              <button
                type="button"
                onClick={handleCloseModal}
                className="w-8 h-8 rounded-full bg-[#222533] text-zinc-400 hover:text-white flex items-center justify-center text-sm transition-colors"
              >
                ✕
              </button>
            </div>

            {/* Modal Body */}
            {modalLoading ? (
              <div className="py-12 flex justify-center">
                <div className="w-6 h-6 border-2 border-red-500 border-t-transparent rounded-full animate-spin"></div>
              </div>
            ) : dayDetails ? (
              <div className="space-y-3 text-xs">
                {dayDetails.is_rest_day ? (
                  <div className="p-4 rounded-xl bg-[#0c0d12] border border-[#222533] text-zinc-300">
                    <div className="font-bold text-white mb-1">🌴 Rest & Muscle Adaptation</div>
                    <p className="text-zinc-400 leading-relaxed">{dayDetails.recovery_guidelines}</p>
                  </div>
                ) : (
                  <>
                    <div className="text-zinc-400">
                      🎯 Focus: <span className="font-medium text-zinc-200">{dayDetails.focus_areas}</span>
                    </div>

                    <div className="space-y-2">
                      <div className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
                        Assigned Exercises
                      </div>
                      {dayDetails.exercises.map((ex, i) => (
                        <div key={ex.id} className="p-3 rounded-xl bg-[#0c0d12] border border-[#222533] space-y-1">
                          <div className="flex justify-between font-semibold text-white">
                            <span>{i + 1}. {ex.name}</span>
                            <span className="text-zinc-300 font-medium">
                              {ex.target_sets} × {ex.target_value}
                            </span>
                          </div>
                          <div className="text-[11px] text-zinc-400">{ex.progression_name}</div>
                          <div className="text-[10px] text-zinc-500">
                            Tempo: {ex.tempo} • Rest: {ex.rest_seconds}s
                          </div>
                        </div>
                      ))}
                    </div>
                  </>
                )}

                <div className="p-2.5 rounded-lg bg-[#0c0d12] border border-[#222533] text-[11px] text-zinc-500 text-center">
                  ℹ️ Past and future days are view-only. You can only complete your active day ({user.current_day}).
                </div>
              </div>
            ) : null}

            <button
              type="button"
              onClick={handleCloseModal}
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
