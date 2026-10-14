import React, { useEffect, useState } from "react";
import { triggerHaptic } from "../api";

interface RestTimerHUDProps {
  targetTimestamp: number | null;
  onClose: () => void;
  onAdjust: (seconds: number) => void;
}

export const RestTimerHUD: React.FC<RestTimerHUDProps> = ({
  targetTimestamp,
  onClose,
  onAdjust,
}) => {
  // Rules of Hooks: declared at top level
  const [secondsRemaining, setSecondsRemaining] = useState<number>(0);

  useEffect(() => {
    if (!targetTimestamp) {
      setSecondsRemaining(0);
      return;
    }

    const updateTimer = () => {
      const now = Date.now();
      const diff = Math.ceil((targetTimestamp - now) / 1000);

      if (diff <= 0) {
        setSecondsRemaining(0);
        triggerHaptic("success");
        onClose();
      } else {
        setSecondsRemaining(diff);
      }
    };

    updateTimer();
    const interval = setInterval(updateTimer, 500);
    return () => clearInterval(interval);
  }, [targetTimestamp, onClose]);

  if (!targetTimestamp || secondsRemaining <= 0) {
    return null;
  }

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}:${s < 10 ? "0" : ""}${s}`;
  };

  return (
    <div className="fixed bottom-20 left-0 right-0 z-40 px-4 max-w-md mx-auto pointer-events-auto">
      <div className="bg-[#151720]/95 border border-red-500/40 shadow-[0_0_20px_rgba(239,68,68,0.2)] backdrop-blur-md rounded-2xl p-3 flex items-center justify-between text-white">
        {/* Timer Display */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-red-600/10 border border-red-500/30 flex items-center justify-center text-red-400 font-bold">
            <svg
              className="w-4 h-4 animate-spin"
              style={{ animationDuration: "3s" }}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              ></circle>
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-wider text-zinc-400 font-semibold">
              Rest Interval
            </div>
            <div className="text-xl font-bold tabular-nums tracking-tight text-white">
              {formatTime(secondsRemaining)}
            </div>
          </div>
        </div>

        {/* Adjust Controls */}
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={() => {
              triggerHaptic("light");
              onAdjust(-15);
            }}
            className="px-2.5 py-1.5 rounded-lg bg-[#222533] hover:bg-[#2c3042] text-zinc-300 text-xs font-semibold active:scale-95 transition-all"
          >
            -15s
          </button>
          <button
            type="button"
            onClick={() => {
              triggerHaptic("light");
              onAdjust(15);
            }}
            className="px-2.5 py-1.5 rounded-lg bg-[#222533] hover:bg-[#2c3042] text-zinc-300 text-xs font-semibold active:scale-95 transition-all"
          >
            +15s
          </button>
          <button
            type="button"
            onClick={() => {
              triggerHaptic("medium");
              onClose();
            }}
            className="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-xs font-bold uppercase tracking-wider text-white shadow-sm active:scale-95 transition-all"
          >
            Skip
          </button>
        </div>
      </div>
    </div>
  );
};
