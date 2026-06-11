import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { ExerciseStats } from '../../models/index';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <main class="hero">
      <section class="hero-content">
        <div class="hero-text">
          <h1>Personalisierte Pole Sport Trainingspläne</h1>
          <p>Erstelle mit künstlicher Intelligenz maßgeschneiderte Trainingspläne für deine Fitness-Ziele</p>
          
          <div class="hero-buttons">
            <button class="btn btn-primary" routerLink="/training-plan">
              Trainingsplan erstellen
            </button>
            <button class="btn btn-secondary" routerLink="/exercises">
              Übungen durchsuchen
            </button>
          </div>
        </div>
        
        <div class="hero-image">
          <div class="image-placeholder">
            <span>🧗</span>
          </div>
        </div>
      </section>

      <section class="features">
        <h2>Features</h2>
        <div class="features-grid">
          <div class="feature-card">
            <div class="feature-icon">🤖</div>
            <h3>KI-gestützt</h3>
            <p>Personalisierte Pläne basierend auf dein Niveau und deine Ziele</p>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon">📊</div>
            <h3>800+ Übungen</h3>
            <p>Umfangreiche Datenbank mit allgemeinen und Pole-spezifischen Übungen</p>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon">🎯</div>
            <h3>Gezielte Workouts</h3>
            <p>Fokussiere dich auf Kraft, Flexibilität oder neue Moves</p>
          </div>
          
          <div class="feature-card">
            <div class="feature-icon">📈</div>
            <h3>Progression</h3>
            <p>Strukturierte Progression vom Anfänger zum Fortgeschrittenen</p>
          </div>
        </div>
      </section>

      <section class="stats" *ngIf="stats">
        <h2>Datenbank-Übersicht</h2>
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-number">{{ stats.total_exercises }}</div>
            <div class="stat-label">Übungen insgesamt</div>
          </div>
          
          <div class="stat-card pole-specific">
            <div class="stat-number">{{ stats.pole_sport_exercises }}</div>
            <div class="stat-label">Pole Sport Übungen</div>
          </div>
          
          <div class="stat-card">
            <div class="stat-number">{{ stats.general_exercises }}</div>
            <div class="stat-label">Allgemeine Übungen</div>
          </div>
        </div>
      </section>

      <section class="cta">
        <h2>Bereit zu starten?</h2>
        <p>Erstelle jetzt deinen ersten personalisierten Trainingsplan</p>
        <button class="btn btn-primary" routerLink="/training-plan">
          Jetzt beginnen →
        </button>
      </section>
    </main>
  `,
  styles: [`
    main {
      min-height: calc(100vh - 200px);
    }

    .hero {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding-bottom: 0;
    }

    .hero-content {
      max-width: 1200px;
      margin: 0 auto;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 3rem;
      align-items: center;
      padding: 4rem 2rem;
    }

    .hero-text h1 {
      font-size: 3rem;
      font-weight: 700;
      margin: 0 0 1rem 0;
      line-height: 1.2;
    }

    .hero-text p {
      font-size: 1.1rem;
      margin: 0 0 2rem 0;
      opacity: 0.95;
      line-height: 1.6;
    }

    .hero-buttons {
      display: flex;
      gap: 1rem;
      flex-wrap: wrap;
    }

    .btn {
      padding: 1rem 2rem;
      font-size: 1rem;
      font-weight: 600;
      border: none;
      border-radius: 0.5rem;
      cursor: pointer;
      transition: all 0.3s ease;
      text-decoration: none;
      display: inline-block;
    }

    .btn-primary {
      background-color: #3498db;
      color: white;
    }

    .btn-primary:hover {
      background-color: #2980b9;
      transform: translateY(-2px);
      box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
    }

    .btn-secondary {
      background-color: transparent;
      color: white;
      border: 2px solid white;
    }

    .btn-secondary:hover {
      background-color: white;
      color: #667eea;
    }

    .hero-image {
      display: flex;
      justify-content: center;
      align-items: center;
      height: 400px;
    }

    .image-placeholder {
      width: 300px;
      height: 300px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 1rem;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 10rem;
      border: 2px dashed rgba(255, 255, 255, 0.3);
    }

    .features {
      max-width: 1200px;
      margin: 4rem auto;
      padding: 0 2rem;
    }

    .features h2,
    .stats h2,
    .cta h2 {
      font-size: 2rem;
      text-align: center;
      margin-bottom: 3rem;
      color: #2c3e50;
    }

    .features-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 2rem;
      margin-bottom: 4rem;
    }

    .feature-card {
      background: white;
      padding: 2rem;
      border-radius: 0.5rem;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
      text-align: center;
      transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    .feature-card:hover {
      transform: translateY(-5px);
      box-shadow: 0 5px 20px rgba(0, 0, 0, 0.15);
    }

    .feature-icon {
      font-size: 3rem;
      margin-bottom: 1rem;
    }

    .feature-card h3 {
      font-size: 1.3rem;
      margin: 0 0 0.5rem 0;
      color: #2c3e50;
    }

    .feature-card p {
      color: #666;
      margin: 0;
      line-height: 1.5;
    }

    .stats {
      max-width: 1200px;
      margin: 4rem auto;
      padding: 0 2rem;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 2rem;
    }

    .stat-card {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 2rem;
      border-radius: 0.5rem;
      text-align: center;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }

    .stat-card.pole-specific {
      background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }

    .stat-number {
      font-size: 2.5rem;
      font-weight: 700;
      margin-bottom: 0.5rem;
    }

    .stat-label {
      font-size: 0.95rem;
      opacity: 0.9;
    }

    .cta {
      max-width: 1200px;
      margin: 4rem auto;
      padding: 3rem 2rem;
      background: #f8f9fa;
      border-radius: 0.5rem;
      text-align: center;
    }

    .cta h2 {
      margin-top: 0;
    }

    .cta p {
      font-size: 1.1rem;
      color: #666;
      margin-bottom: 2rem;
    }

    @media (max-width: 768px) {
      .hero-content {
        grid-template-columns: 1fr;
        padding: 2rem 1rem;
      }

      .hero-text h1 {
        font-size: 2rem;
      }

      .image-placeholder {
        font-size: 5rem;
        width: 200px;
        height: 200px;
      }

      .hero-buttons {
        flex-direction: column;
      }

      .btn {
        width: 100%;
      }
    }
  `]
})
export class HomeComponent implements OnInit {
  stats: ExerciseStats | null = null;

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.apiService.getExerciseStats().subscribe({
      next: (data) => {
        this.stats = data;
      },
      error: (error) => {
        console.error('Error loading exercise stats:', error);
      }
    });
  }
}
