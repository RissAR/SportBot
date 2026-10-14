import React, { useEffect, useState } from "react";
import { api, triggerHaptic } from "../api";
import { UserProfile, WeightRecord } from "../types";

interface ProgressTabProps {
  user: UserProfile;
  onRefreshUser: () => void;
}

export const ProgressTab: React.FC<ProgressTabProps> = ({ user, onRefreshUser }) => {
  // Rules of Hooks: All hooks declared unconditionally at top level
  const [history, setHistory] = useState<WeightRecord[]>([]);
  const [loadingHistory, setLoadingHistory] = useState<boolean>(true);
  const [weightModalOpen, setWeightModalOpen] = useState<boolean>(false);
  const [weightInput, setWeightInput] = useState<string>("");
  const [submittingWeight, setSubmittingWeight] = useState<boolean>(false);
  const [weightError, setWeightError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    const loadWeightHistory = async () => {
      try {
        const records = await api.fetchWeightHistory();
        if (isMounted) setHistory(records);
      } catch (err) {
        console.error("Failed to load weight history:", err);
      } finally {
        if (isMounted) setLoadingHistory(false);
      }
    };
    loadWeightHistory();
    return () => {
      isMounted = false;
    };
  }, [user.latest_weight]);

  const handleDifficultyChange = async (newMode: "light" | "medium" | "hard") => {
    if (newMode === user.difficulty_mode) return;
    triggerHaptic("medium");
    try {
      await api.updateDifficulty(newMode);
      onRefreshUser();
    } catch (err) {
      console.error("Failed to update difficulty:", err);
    }
  };

  const handleSaveWeight = async (e: React.FormEvent) => {
    e.preventDefault();
    const val = parseFloat(weightInput);
    if (isNaN(val) || val <= 30 || val >= 300) {
      setWeightError("Please enter a valid bodyweight between 30 and 300 kg.");
      return;
    }

    triggerHaptic("heavy");
    setSubmittingWeight(true);
    setWeightError(null);

    try {
      await api.logWeight(val, user.current_cycle);
      triggerHaptic("success");
      setWeightModalOpen(false);
      setWeightInput("");
      onRefreshUser();
      const updated = await api.fetchWeightHistory();
      setHistory(updated);
    } catch (err: any) {
      triggerHaptic("error");
      setWeightError(err.message || "Failed to record weight.");
    } finally {
      setSubmittingWeight(false);
    }
  };

  const completedDays = Math.max(0, user.current_day - 1);
  const progressPct = Math.round((completedDays / 30) * 100);

  return (
    <div className="space-y-6 animate-fade-in pb-4">
      {/* Cycle Progress Summary */}
      <div className="p-5 rounded-2xl bg-[#151720] border border-[#222533] shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-xs uppercase tracking-wider text-zinc-400 font-semibold">
              Cycle {user.current_cycle} Overview
            </span>
            <h2 className="text-base font-bold text-white tracking-tight mt-0.5">ATHLETIC PROGRESSION</h2>
          </div>
          <span className="text-xl font-bold text-white tracking-tight">{progressPct}%</span>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-[#0c0d12] h-2.5 rounded-full overflow-hidden border border-[#222533] p-0.5">
          <div
            className="bg-red-600 h-full rounded-full transition-all duration-500 shadow-sm"
            style={{ width: `${progressPct}%` }}
          ></div>
        </div>

        <div className="grid grid-cols-2 gap-3 pt-1 text-center">
          <div className="p-3 rounded-xl bg-[#0c0d12] border border-[#222533]">
            <div className="text-[10px] text-zinc-400 uppercase tracking-wider font-semibold">Current Day</div>
            <div className="text-base font-bold text-white mt-0.5">{user.current_day} / 30</div>
          </div>
          <div className="p-3 rounded-xl bg-[#0c0d12] border border-[#222533]">
            <div className="text-[10px] text-zinc-400 uppercase tracking-wider font-semibold">Total Completed</div>
            <div className="text-base font-bold text-white mt-0.5">
              {user.total_workouts_completed} Workouts
            </div>
          </div>
        </div>
      </div>

      {/* Difficulty Tier Selector */}
      <div className="p-4 rounded-2xl bg-[#151720] border border-[#222533] space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs uppercase font-bold tracking-wider text-zinc-300">
            Training Intensity
          </span>
          <span className="text-xs text-zinc-400 font-semibold uppercase">
            Active: {user.difficulty_mode}
          </span>
        </div>
        <div className="grid grid-cols-3 gap-2">
          {(["light", "medium", "hard"] as const).map((mode) => (
            <button
              key={mode}
              type="button"
              onClick={() => handleDifficultyChange(mode)}
              className={`py-2 px-1 rounded-xl text-xs font-semibold capitalize transition-all ${
                user.difficulty_mode === mode
                  ? "bg-red-600 text-white font-bold shadow-sm"
                  : "bg-[#0c0d12] border border-[#222533] text-zinc-400 hover:text-white"
              }`}
            >
              {mode}
            </button>
          ))}
        </div>
      </div>

      {/* Bodyweight Tracking Block */}
      <div className="p-4 rounded-2xl bg-[#151720] border border-[#222533] space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-tight">Bodyweight Tracker</h3>
            <span className="text-xs text-zinc-400">Track monthly adaptation & body mass balance</span>
          </div>
          <button
            type="button"
            onClick={() => {
              triggerHaptic("light");
              setWeightModalOpen(true);
            }}
            className="px-3 py-1.5 rounded-xl bg-red-600 hover:bg-red-500 text-white text-xs font-bold shadow-sm active:scale-95 transition-all"
          >
            Log Weight
          </button>
        </div>

        {/* Current Weight Card */}
        <div className="p-3.5 rounded-xl bg-[#0c0d12] border border-[#222533] flex items-center justify-between">
          <span className="text-xs text-zinc-400">Latest Recorded Mass</span>
          <span className="text-lg font-bold tabular-nums text-white">
            {user.latest_weight ? `${user.latest_weight.toFixed(1)} kg` : "No data yet"}
          </span>
        </div>

        {/* History List */}
        <div className="space-y-2">
          <span className="text-[10px] uppercase text-zinc-400 tracking-wider font-semibold">
            Check-in History:
          </span>
          {loadingHistory ? (
            <div className="text-xs text-zinc-500 py-2">Loading history...</div>
          ) : history.length === 0 ? (
            <div className="text-xs text-zinc-500 italic py-2">No weight check-ins recorded yet.</div>
          ) : (
            <div className="space-y-1.5 max-h-40 overflow-y-auto no-scrollbar pr-1">
              {history.map((record) => (
                <div
                  key={record.id}
                  className="flex items-center justify-between p-2.5 rounded-xl bg-[#0c0d12] border border-[#222533] text-xs"
                >
                  <span className="text-zinc-400 font-medium">Cycle {record.cycle_number}</span>
                  <span className="text-zinc-500 text-[11px]">
                    {new Date(record.logged_at).toLocaleDateString()}
                  </span>
                  <span className="font-bold tabular-nums text-white">{record.weight_kg.toFixed(1)} kg</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Log Weight Modal (Stealth Dark) */}
      {weightModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
          <form
            onSubmit={handleSaveWeight}
            className="bg-[#151720] border border-[#222533] rounded-2xl max-w-sm w-full p-5 space-y-4 shadow-2xl"
          >
            <div className="flex items-center justify-between border-b border-[#222533] pb-3">
              <h3 className="text-base font-bold text-white tracking-tight">Log Bodyweight</h3>
              <button
                type="button"
                onClick={() => setWeightModalOpen(false)}
                className="w-8 h-8 rounded-full bg-[#222533] text-zinc-400 hover:text-white flex items-center justify-center text-sm"
              >
                ✕
              </button>
            </div>

            {weightError && (
              <div className="p-2.5 rounded-xl bg-red-950/80 border border-red-500 text-red-200 text-xs">
                {weightError}
              </div>
            )}

            <div>
              <label className="block text-xs text-zinc-300 font-medium mb-1">
                Bodyweight (kg):
              </label>
              <input
                type="number"
                step="0.1"
                min="30"
                max="300"
                value={weightInput}
                onChange={(e) => setWeightInput(e.target.value)}
                placeholder="e.g. 85.0"
                autoFocus
                required
                className="w-full px-3 py-2.5 rounded-xl bg-[#0c0d12] border border-[#222533] text-white text-lg focus:outline-none focus:border-red-500"
              />
            </div>

            <div className="flex gap-2 pt-2">
              <button
                type="button"
                onClick={() => setWeightModalOpen(false)}
                className="w-1/2 py-2.5 rounded-xl bg-[#222533] text-zinc-300 text-xs font-semibold hover:bg-[#2c3042]"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submittingWeight}
                className="w-1/2 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 text-white text-xs font-bold shadow-md"
              >
                {submittingWeight ? "Saving..." : "Save Weight"}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
