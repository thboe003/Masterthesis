import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Exercise, ExerciseFilterOptions } from '../../models/index';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-exercise-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="container">
      <div class="header">
        <h1>Übungs-Datenbank</h1>
        <p>Durchsuche 800+ allgemeine und Pole-spezifische Übungen</p>
      </div>

      <div class="filters">
        <div class="filter-group">
          <label for="search">Suche</label>
          <input
            type="text"
            id="search"
            placeholder="Übung suchen..."
            [(ngModel)]="searchTerm"
            (ngModelChange)="onSearch()"
          />
        </div>

        <div class="filter-group">
          <label for="category">Kategorie</label>
          <select
            id="category"
            [(ngModel)]="selectedCategory"
            (ngModelChange)="loadExercises()"
          >
            <option value="">-- Alle --</option>
            <option value="strength">Kraft</option>
            <option value="flexibility">Flexibilität</option>
            <option value="endurance">Ausdauer</option>
            <option value="technique">Technik</option>
            <option value="pole-sport">Pole Sport</option>
          </select>
        </div>

        <div class="filter-group">
          <label for="level">Level</label>
          <select
            id="level"
            [(ngModel)]="selectedLevel"
            (ngModelChange)="loadExercises()"
          >
            <option value="">-- Alle --</option>
            <option value="beginner">Anfänger</option>
            <option value="intermediate">Fortgeschrittene</option>
            <option value="advanced">Profis</option>
          </select>
        </div>

        <div class="filter-group">
          <label for="poles">
            <input type="checkbox" id="poles" [(ngModel)]="showPoleOnly" (ngModelChange)="loadExercises()" />
            <span>Nur Pole Sport</span>
          </label>
        </div>
      </div>

      <div class="exercise-grid" *ngIf="!isLoading">
        <ng-container *ngIf="exercises.length > 0">
          <div class="exercise-card" *ngFor="let exercise of exercises">
            <div class="card-header">
              <h3>{{ exercise.name }}</h3>
              <span class="badge" [ngClass]="'badge-' + exercise.level">
                {{ exercise.level }}
              </span>
            </div>

            <div class="card-body">
              <p class="description">{{ exercise.description || 'Keine Beschreibung verfügbar' }}</p>

              <div class="exercise-meta">
                <div class="meta-item" *ngIf="exercise.category">
                  <strong>Kategorie:</strong>
                  <span>{{ exercise.category }}</span>
                </div>

                <div class="meta-item" *ngIf="exercise.equipment">
                  <strong>Equipment:</strong>
                  <span>{{ exercise.equipment }}</span>
                </div>

                <div class="meta-item" *ngIf="exercise.primary_muscles.length > 0">
                  <strong>Ziele:</strong>
                  <div class="muscle-tags">
                    <span class="tag" *ngFor="let muscle of exercise.primary_muscles">
                      {{ muscle }}
                    </span>
                  </div>
                </div>

                <div class="meta-item" *ngIf="exercise.is_pole_sport">
                  <strong>🧗 Pole Sport spezifisch</strong>
                </div>
              </div>

              <div class="card-footer">
                <button class="btn-info" (click)="toggleDetails(exercise)">
                  {{ expandedExercise?.id === exercise.id ? 'Weniger ▲' : 'Mehr Details ▼' }}
                </button>
              </div>
            </div>

            <div class="card-details" *ngIf="expandedExercise?.id === exercise.id">
              <div class="details-section" *ngIf="exercise.instructions && exercise.instructions.length > 0">
                <h4>Anleitung:</h4>
                <ol>
                  <li *ngFor="let instruction of exercise.instructions">
                    {{ instruction }}
                  </li>
                </ol>
              </div>

              <div class="details-section" *ngIf="exercise.secondary_muscles && exercise.secondary_muscles.length > 0">
                <h4>Sekundäre Muskelgruppen:</h4>
                <div class="muscle-tags">
                  <span class="tag" *ngFor="let muscle of exercise.secondary_muscles">
                    {{ muscle }}
                  </span>
                </div>
              </div>

              <div class="details-section" *ngIf="exercise.source">
                <h4>Quelle:</h4>
                <p>{{ exercise.source }}</p>
              </div>
            </div>
          </div>
        </ng-container>

        <div class="no-results" *ngIf="exercises.length === 0 && !isLoading">
          <p>Keine Übungen gefunden. Versuche, deine Filter anzupassen.</p>
        </div>
      </div>

      <div class="loading" *ngIf="isLoading">
        <div class="spinner"></div>
        <p>Übungen werden geladen...</p>
      </div>

      <div class="pagination">
        <button
          class="btn-pagination"
          (click)="previousPage()"
          [disabled]="currentPage === 1"
        >
          ← Vorherige
        </button>
        <span class="page-info">
          Seite {{ currentPage }} von {{ totalPages }}
        </span>
        <button
          class="btn-pagination"
          (click)="nextPage()"
          [disabled]="currentPage >= totalPages"
        >
          Nächste →
        </button>
      </div>
    </div>
  `,
  styles: [`
    .container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 2rem;
    }

    .header {
      margin-bottom: 2rem;
      text-align: center;
    }

    .header h1 {
      font-size: 2.5rem;
      margin: 0 0 0.5rem 0;
      color: #2c3e50;
    }

    .header p {
      color: #666;
      font-size: 1.1rem;
    }

    .filters {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem;
      margin-bottom: 2rem;
      background: white;
      padding: 1.5rem;
      border-radius: 0.5rem;
      box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
    }

    .filter-group {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .filter-group label {
      font-weight: 600;
      color: #2c3e50;
      font-size: 0.95rem;
    }

    .filter-group input[type="text"],
    .filter-group select {
      padding: 0.6rem;
      border: 1px solid #bdc3c7;
      border-radius: 0.3rem;
      font-size: 0.95rem;
      font-family: inherit;
    }

    .filter-group input[type="text"]:focus,
    .filter-group select:focus {
      outline: none;
      border-color: #667eea;
      box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }

    .filter-group input[type="checkbox"] {
      accent-color: #667eea;
    }

    .exercise-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
      gap: 1.5rem;
      margin-bottom: 2rem;
    }

    .exercise-card {
      background: white;
      border-radius: 0.5rem;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
      overflow: hidden;
      transition: transform 0.3s ease, box-shadow 0.3s ease;
      display: flex;
      flex-direction: column;
    }

    .exercise-card:hover {
      transform: translateY(-5px);
      box-shadow: 0 5px 20px rgba(0, 0, 0, 0.15);
    }

    .card-header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 1.5rem;
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 1rem;
    }

    .card-header h3 {
      margin: 0;
      font-size: 1.2rem;
    }

    .badge {
      background-color: rgba(255, 255, 255, 0.3);
      color: white;
      padding: 0.3rem 0.8rem;
      border-radius: 20px;
      font-size: 0.8rem;
      font-weight: 600;
      text-transform: uppercase;
      white-space: nowrap;
    }

    .badge-beginner {
      background-color: #27ae60;
    }

    .badge-intermediate {
      background-color: #f39c12;
    }

    .badge-advanced {
      background-color: #e74c3c;
    }

    .card-body {
      padding: 1.5rem;
      flex-grow: 1;
    }

    .description {
      color: #555;
      line-height: 1.6;
      margin: 0 0 1rem 0;
    }

    .exercise-meta {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }

    .meta-item {
      font-size: 0.9rem;
    }

    .meta-item strong {
      color: #2c3e50;
      margin-right: 0.5rem;
    }

    .muscle-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      margin-top: 0.3rem;
    }

    .tag {
      display: inline-block;
      background-color: #ecf0f1;
      color: #2c3e50;
      padding: 0.3rem 0.7rem;
      border-radius: 15px;
      font-size: 0.85rem;
    }

    .card-footer {
      border-top: 1px solid #ecf0f1;
      padding: 1rem 1.5rem;
    }

    .btn-info {
      background-color: #3498db;
      color: white;
      border: none;
      padding: 0.5rem 1rem;
      border-radius: 0.3rem;
      cursor: pointer;
      font-size: 0.9rem;
      font-weight: 600;
      transition: background-color 0.3s ease;
    }

    .btn-info:hover {
      background-color: #2980b9;
    }

    .card-details {
      background-color: #f8f9fa;
      padding: 1.5rem;
      border-top: 1px solid #ecf0f1;
    }

    .details-section {
      margin-bottom: 1rem;
    }

    .details-section:last-child {
      margin-bottom: 0;
    }

    .details-section h4 {
      margin: 0 0 0.75rem 0;
      color: #2c3e50;
      font-size: 0.95rem;
    }

    .details-section ol {
      margin: 0;
      padding-left: 1.5rem;
    }

    .details-section li {
      margin-bottom: 0.5rem;
      line-height: 1.6;
      color: #555;
    }

    .loading {
      text-align: center;
      padding: 3rem;
    }

    .spinner {
      display: inline-block;
      width: 40px;
      height: 40px;
      border: 4px solid #f3f3f3;
      border-top: 4px solid #667eea;
      border-radius: 50%;
      animation: spin 1s linear infinite;
      margin-bottom: 1rem;
    }

    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }

    .no-results {
      text-align: center;
      padding: 3rem;
      color: #666;
      font-size: 1.1rem;
    }

    .pagination {
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 2rem;
      margin-top: 2rem;
      padding: 2rem;
      background: white;
      border-radius: 0.5rem;
      box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
    }

    .btn-pagination {
      background-color: #667eea;
      color: white;
      border: none;
      padding: 0.75rem 1.5rem;
      border-radius: 0.3rem;
      cursor: pointer;
      font-weight: 600;
      transition: background-color 0.3s ease;
    }

    .btn-pagination:hover:not(:disabled) {
      background-color: #764ba2;
    }

    .btn-pagination:disabled {
      background-color: #bdc3c7;
      cursor: not-allowed;
    }

    .page-info {
      color: #2c3e50;
      font-weight: 600;
    }

    @media (max-width: 768px) {
      .exercise-grid {
        grid-template-columns: 1fr;
      }

      .filters {
        grid-template-columns: 1fr;
      }

      .header h1 {
        font-size: 1.8rem;
      }
    }
  `]
})
export class ExerciseListComponent implements OnInit {
  exercises: Exercise[] = [];
  isLoading = false;
  expandedExercise: Exercise | null = null;

  searchTerm = '';
  selectedCategory = '';
  selectedLevel = '';
  showPoleOnly = false;

  currentPage = 1;
  totalPages = 1;
  pageSize = 12;

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.loadExercises();
  }

  loadExercises(): void {
    this.isLoading = true;
    const skip = (this.currentPage - 1) * this.pageSize;

    const options: ExerciseFilterOptions = {
      skip: skip,
      limit: this.pageSize,
      category: this.selectedCategory || undefined,
      level: this.selectedLevel || undefined,
      search: this.searchTerm || undefined
    };

    this.apiService.getExercises(options).subscribe({
      next: (data) => {
        this.exercises = this.showPoleOnly
          ? data.filter(e => e.is_pole_sport)
          : data;
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading exercises:', error);
        this.isLoading = false;
      }
    });
  }

  onSearch(): void {
    this.currentPage = 1;
    this.loadExercises();
  }

  nextPage(): void {
    this.currentPage++;
    this.loadExercises();
  }

  previousPage(): void {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.loadExercises();
    }
  }

  toggleDetails(exercise: Exercise): void {
    this.expandedExercise = this.expandedExercise?.id === exercise.id ? null : exercise;
  }
}
