import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { UserProfile, TrainingPlanRequest } from '../../models/index';
import { TrainingPlanService } from '../../services/training-plan.service';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-user-profile',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule],
  template: `
    <div class="container">
      <div class="form-container">
        <h1>Dein Profil</h1>
        <p class="subtitle">Erzähle uns von dir, um personalisierte Trainingspläne zu erhalten</p>

        <form [formGroup]="profileForm" (ngSubmit)="onSubmit()">
          <!-- Persönliche Informationen -->
          <fieldset class="form-section">
            <legend>Persönliche Informationen</legend>

            <div class="form-group">
              <label for="age">Alter *</label>
              <input
                type="number"
                id="age"
                formControlName="age"
                min="18"
                max="100"
                placeholder="z.B. 28"
                required
              />
              <span class="error" *ngIf="profileForm.get('age')?.hasError('required')">
                Alter ist erforderlich
              </span>
            </div>

            <div class="form-group">
              <label for="gender">Geschlecht</label>
              <select id="gender" formControlName="gender">
                <option value="">-- Nicht angeben --</option>
                <option value="male">Männlich</option>
                <option value="female">Weiblich</option>
                <option value="other">Sonstige</option>
              </select>
            </div>
          </fieldset>

          <!-- Pole Sport Erfahrung -->
          <fieldset class="form-section">
            <legend>Pole Sport Erfahrung</legend>

            <div class="form-group">
              <label for="experience">Erfahrungslevel *</label>
              <select id="experience" formControlName="experience_level" required>
                <option value="">-- Bitte wählen --</option>
                <option value="beginner">Anfänger (0-6 Monate)</option>
                <option value="intermediate">Fortgeschrittene (6-24 Monate)</option>
                <option value="advanced">Fortgeschrittene (2+ Jahre)</option>
              </select>
              <span class="error" *ngIf="profileForm.get('experience_level')?.hasError('required')">
                Erfahrungslevel ist erforderlich
              </span>
            </div>

            <div class="form-group">
              <label for="fitness">
                Fitness Level: <strong>{{ profileForm.get('fitness_level')?.value || 5 }}/10</strong> *
              </label>
              <input
                type="range"
                id="fitness"
                formControlName="fitness_level"
                min="1"
                max="10"
                required
              />
              <div class="range-labels">
                <span>Sehr niedrig</span>
                <span>Durchschnitt</span>
                <span>Sehr hoch</span>
              </div>
              <span class="error" *ngIf="profileForm.get('fitness_level')?.hasError('required')">
                Fitness Level ist erforderlich
              </span>
            </div>
          </fieldset>

          <!-- Verfügbarkeit -->
          <fieldset class="form-section">
            <legend>Verfügbarkeit & Ziele</legend>

            <div class="form-group">
              <label for="days">Trainingstage pro Woche *</label>
              <select id="days" formControlName="available_days_per_week" required>
                <option value="">-- Bitte wählen --</option>
                <option value="1">1 Tag</option>
                <option value="2">2 Tage</option>
                <option value="3">3 Tage</option>
                <option value="4">4 Tage</option>
                <option value="5">5 Tage</option>
                <option value="6">6 Tage</option>
                <option value="7">7 Tage (täglich)</option>
              </select>
              <span class="error" *ngIf="profileForm.get('available_days_per_week')?.hasError('required')">
                Trainingstage sind erforderlich
              </span>
            </div>

            <div class="form-group">
              <label for="duration">Trainingsdauer pro Session (Stunden)</label>
              <select id="duration" formControlName="hours_per_session">
                <option value="">-- Bitte wählen --</option>
                <option value="0.5">30 Minuten</option>
                <option value="1">1 Stunde</option>
                <option value="1.5">1,5 Stunden</option>
                <option value="2">2 Stunden</option>
                <option value="2.5">2,5+ Stunden</option>
              </select>
            </div>

            <div class="form-group">
              <label>Trainingsziele * (Mehrfachauswahl möglich)</label>
              <div class="checkbox-group">
                <label class="checkbox-label">
                  <input type="checkbox" value="strength" formControlName="strength" />
                  <span>Kraft aufbauen</span>
                </label>
                <label class="checkbox-label">
                  <input type="checkbox" value="flexibility" formControlName="flexibility" />
                  <span>Flexibilität verbessern</span>
                </label>
                <label class="checkbox-label">
                  <input type="checkbox" value="new_moves" formControlName="new_moves" />
                  <span>Neue Moves lernen</span>
                </label>
                <label class="checkbox-label">
                  <input type="checkbox" value="endurance" formControlName="endurance" />
                  <span>Ausdauer verbessern</span>
                </label>
              </div>
              <span class="error" *ngIf="profileForm.get('goals')?.hasError('required')">
                Mindestens ein Ziel erforderlich
              </span>
            </div>
          </fieldset>

          <!-- Gesundheit -->
          <fieldset class="form-section">
            <legend>Gesundheit & Verletzungen</legend>

            <div class="form-group">
              <label for="limitations">
                Verletzungen oder Einschränkungen
              </label>
              <textarea
                id="limitations"
                formControlName="injuries_or_limitations"
                placeholder="z.B. Schulterverletzung, Knie-Probleme..."
                rows="4"
              ></textarea>
            </div>
          </fieldset>

          <!-- Buttons -->
          <div class="form-actions">
            <button type="submit" class="btn btn-primary" [disabled]="!profileForm.valid || isLoading">
              {{ isLoading ? 'Trainingsplan wird erstellt...' : 'Trainingsplan erstellen' }}
            </button>
            <button type="reset" class="btn btn-secondary">
              Zurücksetzen
            </button>
          </div>
        </form>

        <div class="info-box">
          <strong>Tipp:</strong> Deine Antworten helfen uns, einen perfekten Trainingsplan für dich zu erstellen.
          Du kannst diese Informationen später jederzeit aktualisieren.
        </div>
      </div>
    </div>
  `,
  styles: [`
    .container {
      max-width: 600px;
      margin: 0 auto;
      padding: 2rem;
    }

    .form-container {
      background: white;
      padding: 2rem;
      border-radius: 0.5rem;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }

    h1 {
      font-size: 2rem;
      margin: 0 0 0.5rem 0;
      color: #2c3e50;
    }

    .subtitle {
      color: #666;
      margin-bottom: 2rem;
      font-size: 0.95rem;
    }

    .form-section {
      margin-bottom: 2rem;
      padding-bottom: 2rem;
      border-bottom: 1px solid #ecf0f1;
    }

    .form-section:last-of-type {
      border-bottom: none;
    }

    legend {
      font-size: 1.1rem;
      font-weight: 600;
      color: #2c3e50;
      margin-bottom: 1rem;
    }

    .form-group {
      margin-bottom: 1.5rem;
    }

    label {
      display: block;
      margin-bottom: 0.5rem;
      font-weight: 500;
      color: #2c3e50;
    }

    input[type="text"],
    input[type="email"],
    input[type="number"],
    input[type="tel"],
    select,
    textarea {
      width: 100%;
      padding: 0.75rem;
      font-size: 1rem;
      border: 1px solid #bdc3c7;
      border-radius: 0.3rem;
      font-family: inherit;
      transition: border-color 0.3s ease;
    }

    input[type="text"]:focus,
    input[type="email"]:focus,
    input[type="number"]:focus,
    input[type="tel"]:focus,
    select:focus,
    textarea:focus {
      outline: none;
      border-color: #667eea;
      box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }

    textarea {
      resize: vertical;
      min-height: 100px;
    }

    input[type="range"] {
      width: 100%;
      height: 6px;
      border-radius: 3px;
      background: #bdc3c7;
      outline: none;
      -webkit-appearance: none;
    }

    input[type="range"]::-webkit-slider-thumb {
      -webkit-appearance: none;
      appearance: none;
      width: 20px;
      height: 20px;
      border-radius: 50%;
      background: #667eea;
      cursor: pointer;
      transition: background 0.3s ease;
    }

    input[type="range"]::-webkit-slider-thumb:hover {
      background: #764ba2;
    }

    input[type="range"]::-moz-range-thumb {
      width: 20px;
      height: 20px;
      border-radius: 50%;
      background: #667eea;
      cursor: pointer;
      border: none;
      transition: background 0.3s ease;
    }

    input[type="range"]::-moz-range-thumb:hover {
      background: #764ba2;
    }

    .range-labels {
      display: flex;
      justify-content: space-between;
      font-size: 0.85rem;
      color: #666;
      margin-top: 0.5rem;
    }

    .checkbox-group {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }

    .checkbox-label {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      cursor: pointer;
      font-weight: normal;
      margin: 0;
    }

    input[type="checkbox"] {
      width: 1.1rem;
      height: 1.1rem;
      cursor: pointer;
      accent-color: #667eea;
    }

    .error {
      display: block;
      color: #e74c3c;
      font-size: 0.85rem;
      margin-top: 0.3rem;
    }

    .form-actions {
      display: flex;
      gap: 1rem;
      margin-top: 2rem;
      margin-bottom: 1rem;
    }

    .btn {
      flex: 1;
      padding: 0.75rem 1.5rem;
      font-size: 1rem;
      font-weight: 600;
      border: none;
      border-radius: 0.3rem;
      cursor: pointer;
      transition: all 0.3s ease;
      text-decoration: none;
      display: inline-flex;
      justify-content: center;
      align-items: center;
    }

    .btn-primary {
      background-color: #667eea;
      color: white;
    }

    .btn-primary:hover:not(:disabled) {
      background-color: #764ba2;
      transform: translateY(-2px);
      box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
    }

    .btn-primary:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .btn-secondary {
      background-color: #ecf0f1;
      color: #2c3e50;
    }

    .btn-secondary:hover {
      background-color: #bdc3c7;
    }

    .info-box {
      background-color: #e8f4f8;
      border-left: 4px solid #3498db;
      padding: 1rem;
      margin-top: 1rem;
      border-radius: 0.3rem;
      font-size: 0.95rem;
      color: #2c3e50;
    }

    .info-box strong {
      color: #3498db;
    }

    @media (max-width: 600px) {
      .container {
        padding: 1rem;
      }

      .form-container {
        padding: 1rem;
      }

      h1 {
        font-size: 1.5rem;
      }

      .form-actions {
        flex-direction: column;
      }
    }
  `]
})
export class UserProfileComponent implements OnInit {
  profileForm!: FormGroup;
  isLoading = false;

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
    this.profileForm = this.fb.group({
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
    });
  }

  loadSavedProfile(): void {
    const savedProfile = this.trainingPlanService.getUserProfile();
    if (savedProfile) {
      this.profileForm.patchValue(savedProfile);
    }
  }

  onSubmit(): void {
    if (!this.profileForm.valid) {
      return;
    }

    const formValue = this.profileForm.value;
    
    // Build goals array
    const goals: string[] = [];
    if (formValue.strength) goals.push('strength');
    if (formValue.flexibility) goals.push('flexibility');
    if (formValue.new_moves) goals.push('new_moves');
    if (formValue.endurance) goals.push('endurance');

    if (goals.length === 0) {
      this.profileForm.get('goals')?.setErrors({ 'required': true });
      return;
    }

    // Create training plan request
    const trainingPlanRequest: TrainingPlanRequest = {
      age: formValue.age,
      experience_level: formValue.experience_level,
      fitness_level: formValue.fitness_level,
      available_days_per_week: formValue.available_days_per_week,
      goals: goals,
      injuries_or_limitations: formValue.injuries_or_limitations
    };

    // Save user profile
    const userProfile: UserProfile = {
      age: formValue.age,
      gender: formValue.gender,
      experience_level: formValue.experience_level,
      fitness_level: formValue.fitness_level,
      available_days_per_week: formValue.available_days_per_week,
      hours_per_session: formValue.hours_per_session || 1,
      goals: goals,
      injuries_or_limitations: formValue.injuries_or_limitations
    };

    this.trainingPlanService.setUserProfile(userProfile);

    // Generate training plan
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
        alert('Fehler beim Erstellen des Trainingsplans. Bitte versuche es später erneut.');
      }
    });
  }
}
