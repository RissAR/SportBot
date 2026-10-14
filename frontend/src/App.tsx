import React, { useState, useEffect } from 'react';

declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        ready: () => void;
        expand: () => void;
        close: () => void;
        HapticFeedback?: {
          impactOccurred: (style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft') => void;
          notificationOccurred: (type: 'error' | 'success' | 'warning') => void;
          selectionChanged: () => void;
        };
        initDataUnsafe?: {
          user?: {
            id: number;
            first_name: string;
            last_name?: string;
            username?: string;
          };
        };
      };
    };
  }
}

export const App: React.FC = () => {
  // Rules of Hooks: All hooks declared unconditionally at the very top
  const [userName, setUserName] = useState<string>('Athlete');
  const [activeCycle, setActiveCycle] = useState<boolean>(false);
  const [selectedDifficulty, setSelectedDifficulty] = useState<'Light' | 'Medium' | 'Hard'>('Medium');

  useEffect(() => {
    if (typeof window !== 'undefined' && window.Telegram?.WebApp) {
      window.Telegram.WebApp.ready();
      window.Telegram.WebApp.expand();

      const tgUser = window.Telegram.WebApp.initDataUnsafe?.user;
      if (tgUser?.first_name) {
        setUserName(tgUser.first_name);
      }
    }
  }, []);

  const triggerHaptic = (style: 'light' | 'medium' | 'heavy') => {
    try {
      if (typeof window !== 'undefined' && window.Telegram?.WebApp?.HapticFeedback) {
        window.Telegram.WebApp.HapticFeedback.impactOccurred(style);
      }
    } catch {
      // Safe fallback for standard browser testing
    }
  };

  const handleStartCycle = () => {
    triggerHaptic('heavy');
    setActiveCycle(true);
  };

  const handleDifficultySelect = (difficulty: 'Light' | 'Medium' | 'Hard') => {
    triggerHaptic('light');
    setSelectedDifficulty(difficulty);
  };

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-[#07040d] via-[#100822] to-[#16072b] text-white flex flex-col justify-between p-5 selection:bg-rose-500 selection:text-white">
      {/* Header */}
      <header className="flex flex-col items-center pt-4 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-950/60 border border-red-800/40 text-xs font-semibold uppercase tracking-wider text-red-400 mb-3 shadow-[0_0_15px_rgba(239,68,68,0.2)]">
          <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
          Workout Protocol
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white uppercase drop-shadow-[0_2px_10px_rgba(0,0,0,0.8)]">
          SPORTBOT <span className="text-red-500">//</span> 30-DAY BODYWEIGHT CYCLE
        </h1>
        <p className="text-sm text-zinc-400 mt-2">
          Welcome, <span className="text-zinc-200 font-medium">{userName}</span>! Your personal cycle is ready.
        </p>
      </header>

      {/* Main Badges and Controls */}
      <main className="flex-1 flex flex-col items-center justify-center my-6 space-y-5 max-w-md mx-auto w-full">
        <div className="w-full flex flex-col gap-2.5">
          {/* Badge 1: 30 Days Cycle */}
          <div className="flex items-center justify-between p-3.5 rounded-xl bg-white/[0.03] border border-white/10 backdrop-blur-md">
            <span className="text-xs uppercase font-mono tracking-wider text-zinc-400">Duration</span>
            <span className="text-sm font-bold text-zinc-100 bg-red-950/70 border border-red-700/50 px-3 py-1 rounded-lg">
              30 Days Cycle
            </span>
          </div>

          {/* Badge 2: 3 Difficulty Modes */}
          <div className="p-3.5 rounded-xl bg-white/[0.03] border border-white/10 backdrop-blur-md">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs uppercase font-mono tracking-wider text-zinc-400">Intensity Level</span>
              <span className="text-xs text-red-400 font-medium">3 Difficulty Modes: Light / Medium / Hard</span>
            </div>
            <div className="grid grid-cols-3 gap-2">
              {(['Light', 'Medium', 'Hard'] as const).map((mode) => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => handleDifficultySelect(mode)}
                  className={`py-2 px-1 text-xs font-semibold rounded-lg border transition-all ${
                    selectedDifficulty === mode
                      ? 'bg-red-600 border-red-500 text-white shadow-[0_0_12px_rgba(220,38,38,0.5)]'
                      : 'bg-zinc-900/60 border-zinc-800 text-zinc-400 hover:text-zinc-200'
                  }`}
                >
                  {mode}
                </button>
              ))}
            </div>
          </div>

          {/* Badge 3: Weight Tracking */}
          <div className="flex items-center justify-between p-3.5 rounded-xl bg-white/[0.03] border border-white/10 backdrop-blur-md">
            <span className="text-xs uppercase font-mono tracking-wider text-zinc-400">Progress Tracking</span>
            <span className="text-sm font-bold text-zinc-100 bg-zinc-800/80 border border-zinc-700 px-3 py-1 rounded-lg flex items-center gap-1.5">
              <span>⚖️</span> Weight Tracking
            </span>
          </div>
        </div>

        {/* Dynamic status card */}
        {activeCycle && (
          <div className="w-full p-4 rounded-xl bg-gradient-to-r from-red-950/80 to-zinc-900/80 border border-red-600/50 text-center shadow-[0_0_20px_rgba(220,38,38,0.25)]">
            <p className="text-sm font-bold text-red-400 uppercase tracking-wide">
              🔥 Cycle Active ({selectedDifficulty})
            </p>
            <p className="text-xs text-zinc-300 mt-1">
              Day 1/30: Loading workout protocol...
            </p>
          </div>
        )}
      </main>

      {/* Action Button */}
      <footer className="w-full max-w-md mx-auto pb-4">
        <button
          type="button"
          onClick={handleStartCycle}
          className="w-full py-4 px-6 rounded-xl font-bold text-base tracking-wider uppercase text-white bg-gradient-to-r from-red-600 to-rose-700 hover:from-red-500 hover:to-rose-600 active:scale-[0.98] transition-all shadow-[0_4px_25px_rgba(220,38,38,0.4)] flex items-center justify-center gap-2 cursor-pointer"
        >
          <span>🔥</span>
          <span>{activeCycle ? 'Continue Workout' : 'Start 30-Day Cycle'}</span>
        </button>
      </footer>
    </div>
  );
};

export default App;
