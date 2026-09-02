import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators, AbstractControl, ValidationErrors } from '@angular/forms';
import { Router } from '@angular/router';
import { UserProfile, TrainingPlanRequest } from '../../models/index';
import { TrainingPlanService } from '../../services/training-plan.service';
import { ApiService } from '../../services/api.service';

function atLeastOneGoalValidator(control: AbstractControl): ValidationErrors | null {
  const group = control as FormGroup;
  const hasGoal = ['strength', 'flexibility', 'new_moves', 'endurance']
    .some(key => group.get(key)?.value === true);
  return hasGoal ? null : { noGoalSelected: true };
}

@Component({
  selector: 'app-user-profile',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule],
  templateUrl: './user-profile.component.html',
  styleUrl: './user-profile.component.css'
})
export class UserProfileComponent implements OnInit {
  profileForm!: FormGroup;
  isLoading = false;
  errorMessage: string | null = null;

  constructor(
    private fb: FormBuilder,
    private trainingPlanService: TrainingPlanService,
    private apiService: ApiService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.initializeForm();
    this.loadSavedProfile();
  }

  initializeForm(): void {
    this.profileForm = this.fb.group(
      {
        age: ['', [Validators.required, Validators.min(18)]],
        gender: [''],
        experience_level: ['', Validators.required],
        fitness_level: [5, Validators.required],
        available_days_per_week: ['', Validators.required],
        hours_per_session: [''],
        strength: [false],
        flexibility: [false],
        new_moves: [false],
        endurance: [false],
        injuries_or_limitations: ['']
      },
      { validators: atLeastOneGoalValidator }
    );
  }

  loadSavedProfile(): void {
    const savedProfile = this.trainingPlanService.getUserProfile();
    if (savedProfile) {
      this.profileForm.patchValue(savedProfile);
    }
  }

  onReset(): void {
    this.profileForm.reset({ fitness_level: 5 });
    this.errorMessage = null;
  }

  onSubmit(): void {
    this.errorMessage = null;

    if (!this.profileForm.valid) {
      this.profileForm.markAllAsTouched();
      return;
    }

    const formValue = this.profileForm.value;

    const goals: string[] = [];
    if (formValue.strength) goals.push('strength');
    if (formValue.flexibility) goals.push('flexibility');
    if (formValue.new_moves) goals.push('new_moves');
    if (formValue.endurance) goals.push('endurance');

    const trainingPlanRequest: TrainingPlanRequest = {
      age: formValue.age,
      experience_level: formValue.experience_level,
      fitness_level: formValue.fitness_level,
      available_days_per_week: formValue.available_days_per_week,
      goals: goals,
      injuries_or_limitations: formValue.injuries_or_limitations
    };

    const userProfile: UserProfile = {
      age: formValue.age,
      gender: formValue.gender,
      experience_level: formValue.experience_level,
      fitness_level: formValue.fitness_level,
      available_days_per_week: formValue.available_days_per_week,
      hours_per_session: Number(formValue.hours_per_session) || 1,
      goals: goals,
      injuries_or_limitations: formValue.injuries_or_limitations
    };

    this.trainingPlanService.setUserProfile(userProfile);

    this.isLoading = true;
    this.apiService.generateTrainingPlan(trainingPlanRequest).subscribe({
      next: (plan) => {
        this.isLoading = false;
        this.trainingPlanService.setCurrentPlan(plan);
        this.router.navigate(['/training-plan']);
      },
      error: (error) => {
        this.isLoading = false;
        console.error('Error generating training plan:', error);
        this.errorMessage = 'Fehler beim Erstellen des Trainingsplans. Bitte versuche es später erneut.';
      }
    });
  }
}
