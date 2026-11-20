/**
 * Data models and interfaces for the Pole Sport AI Training Generator frontend
 */

export interface Exercise {
  id: string;
  name: string;
  description?: string;
  category: string;
  level: 'beginner' | 'intermediate' | 'advanced';
  equipment?: string;
  primary_muscles: string[];
  secondary_muscles: string[];
  instructions?: string[];
  is_pole_sport: boolean;
  difficulty_progression?: string;
  source?: string;
}

export interface TrainingPlanExercise {
  exercise_id?: string | null;
  name: string;
  duration_minutes: number;
  sets?: number;
  repetitions?: number;
  rest_seconds: number;
  intensity: 'low' | 'medium' | 'high';
  instructions?: string[] | null;
  notes?: string | null;
  order: number;
  day: number;
  session_title: string;
}

export interface GenerationInfo {
  provider: string;
  model: string;
  duration_ms: number;
  attempts: number;
  input_tokens?: number | null;
  output_tokens?: number | null;
  catalog_size: number;
  unknown_exercises: string[];
  warnings: string[];
}

export interface TrainingPlan {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  duration_weeks: number;
  focus_area: string;
  difficulty_level: 'beginner' | 'intermediate' | 'advanced';
  exercises: TrainingPlanExercise[];
  notes?: string;
  created_at: string;
  is_active: boolean;
  generation?: GenerationInfo;
}

export interface UserProfile {
  age: number;
  gender?: string;
  experience_level: 'beginner' | 'intermediate' | 'advanced';
  fitness_level: number; // 1-10
  available_days_per_week: number;
  hours_per_session: number;
  goals: string[];
  injuries_or_limitations?: string;
}

export interface TrainingPlanRequest {
  age: number;
  gender?: string;
  experience_level: 'beginner' | 'intermediate' | 'advanced';
  fitness_level: number;
  available_days_per_week: number;
  hours_per_session?: number;
  goals: string[];
  injuries_or_limitations?: string;
  duration_weeks?: number;
}

export interface ExerciseFilterOptions {
  skip?: number;
  limit?: number;
  category?: string;
  level?: string;
  search?: string;
}

export interface ExerciseStats {
  total_exercises: number;
  pole_sport_exercises: number;
  general_exercises: number;
  sources: string[];
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}
