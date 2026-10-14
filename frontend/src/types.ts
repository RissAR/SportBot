/**
 * TypeScript data models and API contract matching SportBot FastAPI backend.
 */

export interface UserProfile {
  telegram_id: number;
  username?: string | null;
  current_day: number;
  current_cycle: number;
  difficulty_mode: "light" | "medium" | "hard";
  total_workouts_completed: number;
  latest_weight?: number | null;
}

export interface WarmupStep {
  order: number;
  title: string;
  duration_seconds: number;
  description: string;
}

export interface CooldownStep {
  order: number;
  title: string;
  duration_seconds: number;
  description: string;
}

export interface ExerciseDetail {
  id: number;
  slug: string;
  name: string;
  category: "push" | "pull" | "legs" | "core" | "cardio" | string;
  metric_type: "reps" | "seconds" | "minutes" | string;
  progression_name: string;
  target_sets: number;
  target_value: number;
  tempo: string;
  rest_seconds: number;
  description: string;
  technique_tips: string;
}

export interface TodayWorkout {
  day_number: number;
  cycle_number: number;
  block_type: string;
  title: string;
  focus_areas: string;
  is_rest_day: boolean;
  warmup_steps: WarmupStep[];
  exercises: ExerciseDetail[];
  cooldown_steps: CooldownStep[];
  recovery_guidelines?: string | null;
}

export interface CycleDaySummary {
  day_number: number;
  block_type: "A_PUSH" | "B_PULL" | "C_LEGS_RUN" | "REST" | string;
  title: string;
  focus_areas: string;
  is_rest_day: boolean;
  status: "completed" | "current" | "locked";
}

export interface CycleDaysOverview {
  cycle_number: number;
  current_day: number;
  days: CycleDaySummary[];
}

export interface WorkoutExerciseInput {
  exercise_id: number;
  sets_completed: number;
  value_completed: number;
  is_completed: boolean;
}

export interface WorkoutCompleteRequest {
  day_number: number;
  cycle_number: number;
  duration_seconds: number;
  difficulty_mode: string;
  exercises: WorkoutExerciseInput[];
}

export interface WorkoutCompleteResponse {
  success: boolean;
  message: string;
  cycle_completed: boolean;
  next_day: number;
  next_cycle: number;
}

export interface WeightRecord {
  id: number;
  weight_kg: number;
  cycle_number: number;
  logged_at: string;
}

export interface WeightLogResponse {
  id: number;
  weight_kg: number;
  cycle_number: number;
  logged_at: string;
  is_cycle_reset: boolean;
}
