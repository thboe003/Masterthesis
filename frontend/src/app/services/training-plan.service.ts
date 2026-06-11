import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { TrainingPlan, UserProfile } from '../models/index';

@Injectable({
  providedIn: 'root'
})
export class TrainingPlanService {
  private currentPlanSubject = new BehaviorSubject<TrainingPlan | null>(null);
  private userProfileSubject = new BehaviorSubject<UserProfile | null>(null);
  private savedPlansSubject = new BehaviorSubject<TrainingPlan[]>([]);
  private isLoadingSubject = new BehaviorSubject<boolean>(false);

  public currentPlan$ = this.currentPlanSubject.asObservable();
  public userProfile$ = this.userProfileSubject.asObservable();
  public savedPlans$ = this.savedPlansSubject.asObservable();
  public isLoading$ = this.isLoadingSubject.asObservable();

  constructor() {
    this.loadFromLocalStorage();
  }

  /**
   * Set the current training plan
   */
  setCurrentPlan(plan: TrainingPlan): void {
    this.currentPlanSubject.next(plan);
    this.saveToLocalStorage('currentPlan', plan);
  }

  /**
   * Get the current training plan
   */
  getCurrentPlan(): TrainingPlan | null {
    return this.currentPlanSubject.value;
  }

  /**
   * Set user profile
   */
  setUserProfile(profile: UserProfile): void {
    this.userProfileSubject.next(profile);
    this.saveToLocalStorage('userProfile', profile);
  }

  /**
   * Get user profile
   */
  getUserProfile(): UserProfile | null {
    return this.userProfileSubject.value;
  }

  /**
   * Add plan to saved plans
   */
  savePlan(plan: TrainingPlan): void {
    const savedPlans = this.savedPlansSubject.value;
    const exists = savedPlans.some(p => p.id === plan.id);
    if (!exists) {
      savedPlans.push(plan);
      this.savedPlansSubject.next([...savedPlans]);
      this.saveToLocalStorage('savedPlans', [...savedPlans]);
    }
  }

  /**
   * Remove plan from saved plans
   */
  removePlan(planId: string): void {
    const savedPlans = this.savedPlansSubject.value.filter(p => p.id !== planId);
    this.savedPlansSubject.next(savedPlans);
    this.saveToLocalStorage('savedPlans', savedPlans);
  }

  /**
   * Get saved plans
   */
  getSavedPlans(): TrainingPlan[] {
    return this.savedPlansSubject.value;
  }

  /**
   * Set loading state
   */
  setLoading(isLoading: boolean): void {
    this.isLoadingSubject.next(isLoading);
  }

  /**
   * Clear all data
   */
  clearAll(): void {
    this.currentPlanSubject.next(null);
    this.userProfileSubject.next(null);
    this.savedPlansSubject.next([]);
    localStorage.removeItem('currentPlan');
    localStorage.removeItem('userProfile');
    localStorage.removeItem('savedPlans');
  }

  /**
   * Save to local storage
   */
  private saveToLocalStorage(key: string, value: any): void {
    try {
      localStorage.setItem(`poleAI_${key}`, JSON.stringify(value));
    } catch (error) {
      console.error(`Error saving to localStorage: ${key}`, error);
    }
  }

  /**
   * Load from local storage
   */
  private loadFromLocalStorage(): void {
    try {
      const currentPlan = localStorage.getItem('poleAI_currentPlan');
      if (currentPlan) {
        this.currentPlanSubject.next(JSON.parse(currentPlan));
      }

      const userProfile = localStorage.getItem('poleAI_userProfile');
      if (userProfile) {
        this.userProfileSubject.next(JSON.parse(userProfile));
      }

      const savedPlans = localStorage.getItem('poleAI_savedPlans');
      if (savedPlans) {
        this.savedPlansSubject.next(JSON.parse(savedPlans));
      }
    } catch (error) {
      console.error('Error loading from localStorage', error);
    }
  }
}
