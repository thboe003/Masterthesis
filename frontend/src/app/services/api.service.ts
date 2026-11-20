import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  Exercise,
  TrainingPlan,
  TrainingPlanRequest,
  ExerciseStats,
  ExerciseFilterOptions,
  AnalyzableExercise,
  VideoAnalysisRequest,
  VideoAnalysisResult,
} from '../models/index';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = 'http://localhost:8000/api/v1';

  constructor(private http: HttpClient) {}

  /**
   * Get all exercises with optional filtering
   */
  getExercises(options?: ExerciseFilterOptions): Observable<Exercise[]> {
    let params = new HttpParams();
    if (options) {
      if (options.skip !== undefined) params = params.set('skip', options.skip.toString());
      if (options.limit !== undefined) params = params.set('limit', options.limit.toString());
      if (options.category) params = params.set('category', options.category);
      if (options.level) params = params.set('level', options.level);
      if (options.search) params = params.set('search', options.search);
    }
    return this.http.get<Exercise[]>(`${this.apiUrl}/exercises`, { params });
  }

  /**
   * Get pole sport specific exercises
   */
  getPoleSportExercises(level?: string, limit: number = 20): Observable<Exercise[]> {
    let params = new HttpParams();
    params = params.set('limit', limit.toString());
    if (level) params = params.set('level', level);
    return this.http.get<Exercise[]>(`${this.apiUrl}/exercises/pole-sport`, { params });
  }

  /**
   * Get exercises for a specific muscle group
   */
  getExercisesByMuscle(muscle: string, limit: number = 20): Observable<Exercise[]> {
    const params = new HttpParams().set('limit', limit.toString());
    return this.http.get<Exercise[]>(
      `${this.apiUrl}/exercises/by-muscle/${muscle}`,
      { params }
    );
  }

  /**
   * Get a single exercise by ID
   */
  getExercise(exerciseId: string): Observable<Exercise> {
    return this.http.get<Exercise>(`${this.apiUrl}/exercises/${exerciseId}`);
  }

  /**
   * Get exercise categories
   */
  getExerciseCategories(): Observable<string[]> {
    return this.http.get<string[]>(`${this.apiUrl}/exercises/categories`);
  }

  /**
   * Get exercise database statistics
   */
  getExerciseStats(): Observable<ExerciseStats> {
    return this.http.get<ExerciseStats>(`${this.apiUrl}/exercises/stats`);
  }

  /**
   * Generate a training plan based on user profile
   */
  generateTrainingPlan(userProfile: TrainingPlanRequest): Observable<TrainingPlan> {
    return this.http.post<TrainingPlan>(
      `${this.apiUrl}/training-plans/generate`,
      userProfile
    );
  }

  /**
   * Get a specific training plan
   */
  getTrainingPlan(planId: string): Observable<TrainingPlan> {
    return this.http.get<TrainingPlan>(`${this.apiUrl}/training-plans/${planId}`);
  }

  /**
   * Update a training plan
   */
  updateTrainingPlan(planId: string, plan: TrainingPlan): Observable<TrainingPlan> {
    return this.http.put<TrainingPlan>(
      `${this.apiUrl}/training-plans/${planId}`,
      plan
    );
  }

  /**
   * Delete a training plan
   */
  deleteTrainingPlan(planId: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/training-plans/${planId}`);
  }

  /**
   * Pole exercises that can be selected for the video analysis
   */
  getAnalyzableExercises(): Observable<AnalyzableExercise[]> {
    return this.http.get<AnalyzableExercise[]>(`${this.apiUrl}/video-analysis/exercises`);
  }

  /**
   * Upload a training video and get feedback on the execution
   * (multipart/form-data – the browser sets the boundary header itself)
   */
  analyzeVideo(request: VideoAnalysisRequest): Observable<VideoAnalysisResult> {
    const form = new FormData();
    form.append('video', request.video, request.video.name);
    const optional: Record<string, string | number | boolean | undefined> = {
      exercise_id: request.exercise_id,
      exercise_name: request.exercise_name,
      experience_level: request.experience_level,
      user_notes: request.user_notes,
      num_frames: request.num_frames,
      frame_mode: request.frame_mode,
      use_pose: request.use_pose,
      start_s: request.start_s,
      end_s: request.end_s,
    };
    Object.entries(optional).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        form.append(key, String(value));
      }
    });
    return this.http.post<VideoAnalysisResult>(`${this.apiUrl}/video-analysis/analyze`, form);
  }
}
