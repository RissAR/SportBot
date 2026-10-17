/**
 * HTTP API client for SportBot backend with automatic Telegram initData injection.
 */

import {
  CycleDaysOverview,
  TodayWorkout,
  UserProfile,
  WeightLogResponse,
  WeightRecord,
  WorkoutCompleteRequest,
  WorkoutCompleteResponse,
} from "./types";

declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        ready: () => void;
        expand: () => void;
        close: () => void;
        initData?: string;
        initDataUnsafe?: {
          user?: {
            id: number;
            first_name: string;
            last_name?: string;
            username?: string;
          };
        };
        HapticFeedback?: {
          impactOccurred: (style: "light" | "medium" | "heavy" | "rigid" | "soft") => void;
          notificationOccurred: (type: "error" | "success" | "warning") => void;
          selectionChanged: () => void;
        };
      };
    };
  }
}

const BASE_URL = "/api";

export const triggerHaptic = (
  type: "light" | "medium" | "heavy" | "rigid" | "soft" | "success" | "warning" | "error"
) => {
  try {
    const tg = window.Telegram?.WebApp;
    if (!tg?.HapticFeedback) return;
    if (type === "success" || type === "warning" || type === "error") {
      tg.HapticFeedback.notificationOccurred(type);
    } else {
      tg.HapticFeedback.impactOccurred(type);
    }
  } catch {
    // Safe fallback for browser dev
  }
};

const getHeaders = (): HeadersInit => {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  const initData = window.Telegram?.WebApp?.initData;
  if (initData && initData.trim().length > 0) {
    headers["Authorization"] = `tma ${initData}`;
  } else {
    // Fallback for direct browser testing
    headers["X-Dev-Telegram-Id"] = "123456789";
  }

  return headers;
};

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = "Server request failed";
    try {
      const err = await res.json();
      if (err.detail) errorDetail = err.detail;
    } catch {
      errorDetail = `HTTP ${res.status}: ${res.statusText}`;
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export const api = {
  async fetchUserProfile(): Promise<UserProfile> {
    const res = await fetch(`${BASE_URL}/user/me`, { headers: getHeaders() });
    return handleResponse<UserProfile>(res);
  },

  async updateDifficulty(mode: "light" | "medium" | "hard"): Promise<UserProfile> {
    const res = await fetch(`${BASE_URL}/user/difficulty`, {
      method: "PATCH",
      headers: getHeaders(),
      body: JSON.stringify({ difficulty_mode: mode }),
    });
    return handleResponse<UserProfile>(res);
  },

  async fetchTodayWorkout(): Promise<TodayWorkout> {
    const res = await fetch(`${BASE_URL}/cycle/today`, { headers: getHeaders() });
    return handleResponse<TodayWorkout>(res);
  },

  async completeWorkout(data: WorkoutCompleteRequest): Promise<WorkoutCompleteResponse> {
    const res = await fetch(`${BASE_URL}/workout/complete`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse<WorkoutCompleteResponse>(res);
  },

  async fetchCycleDays(): Promise<CycleDaysOverview> {
    const res = await fetch(`${BASE_URL}/cycle/days`, { headers: getHeaders() });
    return handleResponse<CycleDaysOverview>(res);
  },

  async fetchDayDetails(dayNumber: number): Promise<TodayWorkout> {
    const res = await fetch(`${BASE_URL}/cycle/days/${dayNumber}`, { headers: getHeaders() });
    return handleResponse<TodayWorkout>(res);
  },

  async logWeight(weight_kg: number, cycle_number: number): Promise<WeightLogResponse> {
    const res = await fetch(`${BASE_URL}/weight`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ weight_kg, cycle_number }),
    });
    return handleResponse<WeightLogResponse>(res);
  },

  async fetchWeightHistory(): Promise<WeightRecord[]> {
    const res = await fetch(`${BASE_URL}/weight/history`, { headers: getHeaders() });
    const data = await handleResponse<{ history: WeightRecord[] }>(res);
    return data.history || [];
  },
};
