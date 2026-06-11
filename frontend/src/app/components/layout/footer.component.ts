import { Component } from '@angular/core';

@Component({
  selector: 'app-footer',
  standalone: true,
  template: `
    <footer class="footer">
      <div class="footer-container">
        <div class="footer-section">
          <h4>Pole AI Trainer</h4>
          <p>KI-gestützte Trainingspläne für Pole Sport</p>
        </div>
        
        <div class="footer-section">
          <h4>Links</h4>
          <ul>
            <li><a href="#">Datenschutz</a></li>
            <li><a href="#">Nutzungsbedingungen</a></li>
            <li><a href="#">Kontakt</a></li>
          </ul>
        </div>
        
        <div class="footer-section">
          <h4>Über</h4>
          <p>Masterarbeit in Angewandter Künstlicher Intelligenz</p>
          <p>© 2026 - Alle Rechte vorbehalten</p>
        </div>
      </div>
    </footer>
  `,
  styles: [`
    .footer {
      background-color: #2c3e50;
      color: #ecf0f1;
      padding: 3rem 2rem;
      margin-top: 4rem;
      border-top: 1px solid #34495e;
    }

    .footer-container {
      max-width: 1200px;
      margin: 0 auto;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 2rem;
    }

    .footer-section h4 {
      margin-top: 0;
      margin-bottom: 1rem;
      color: #3498db;
    }

    .footer-section ul {
      list-style: none;
      padding: 0;
      margin: 0;
    }

    .footer-section ul li {
      margin-bottom: 0.5rem;
    }

    .footer-section a {
      color: #ecf0f1;
      text-decoration: none;
      transition: color 0.3s ease;
    }

    .footer-section a:hover {
      color: #3498db;
    }

    .footer-section p {
      margin: 0.5rem 0;
      font-size: 0.95rem;
      line-height: 1.6;
    }
  `]
})
export class FooterComponent {}
