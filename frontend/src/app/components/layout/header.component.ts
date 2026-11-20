import { Component, OnInit } from '@angular/core';
import { RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <header class="header">
      <nav class="navbar">
        <div class="navbar-container">
          <div class="navbar-brand">
            <a routerLink="/" class="logo">
              <span class="logo-icon">🎯</span>
              <span class="logo-text">Pole AI Trainer</span>
            </a>
          </div>
          
          <ul class="nav-links">
            <li><a routerLink="/" routerLinkActive="active" [routerLinkActiveOptions]="{ exact: true }">Home</a></li>
            <li><a routerLink="/exercises" routerLinkActive="active">Übungen</a></li>
            <li><a routerLink="/training-plan" routerLinkActive="active">Trainingsplan</a></li>
            <li><a routerLink="/my-plans" routerLinkActive="active">Meine Pläne</a></li>
            <li><a routerLink="/video-analysis" routerLinkActive="active">Videoanalyse</a></li>
          </ul>
          
          <div class="nav-actions">
            <button class="btn-help" title="Hilfe">?</button>
          </div>
        </div>
      </nav>
    </header>
  `,
  styles: [`
    .header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
      position: sticky;
      top: 0;
      z-index: 1000;
    }

    .navbar {
      padding: 1rem 0;
    }

    .navbar-container {
      max-width: 1200px;
      margin: 0 auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0 2rem;
    }

    .navbar-brand {
      flex-shrink: 0;
    }

    .logo {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      color: white;
      text-decoration: none;
      font-size: 1.5rem;
      font-weight: 600;
      transition: opacity 0.3s ease;
    }

    .logo:hover {
      opacity: 0.8;
    }

    .logo-icon {
      font-size: 2rem;
    }

    .logo-text {
      display: none;
    }

    @media (min-width: 768px) {
      .logo-text {
        display: inline;
      }
    }

    .nav-links {
      display: flex;
      list-style: none;
      gap: 2rem;
      margin: 0;
      padding: 0;
      flex: 1;
      justify-content: center;
    }

    .nav-links a {
      color: white;
      text-decoration: none;
      font-weight: 500;
      transition: opacity 0.3s ease;
      padding: 0.5rem 0;
      border-bottom: 2px solid transparent;
    }

    .nav-links a:hover {
      opacity: 0.8;
    }

    .nav-links a.active {
      border-bottom-color: white;
    }

    .nav-actions {
      display: flex;
      gap: 1rem;
    }

    .btn-help {
      background: rgba(255, 255, 255, 0.2);
      color: white;
      border: 2px solid white;
      border-radius: 50%;
      width: 2.5rem;
      height: 2.5rem;
      font-size: 1rem;
      font-weight: bold;
      cursor: pointer;
      transition: all 0.3s ease;
    }

    .btn-help:hover {
      background: white;
      color: #667eea;
    }

    @media (max-width: 768px) {
      .nav-links {
        gap: 1rem;
        font-size: 0.9rem;
      }

      .navbar-container {
        padding: 0 1rem;
      }
    }
  `]
})
export class HeaderComponent {}
