import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TrainingPlan, TrainingPlanExercise } from '../../models/index';
import { TrainingPlanService } from '../../services/training-plan.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-training-plan',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './training-plan.component.html',
  styleUrl: './training-plan.component.css'
})
export class TrainingPlanComponent implements OnInit {
  plan: TrainingPlan | null = null;
  exercises: TrainingPlanExercise[] = [];

  constructor(
    private trainingPlanService: TrainingPlanService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.trainingPlanService.currentPlan$.subscribe((plan) => {
      this.plan = plan;
      if (plan) {
        this.exercises = plan.exercises;
      }
    });
  }

  savePlan(): void {
    if (this.plan) {
      this.trainingPlanService.savePlan(this.plan);
      alert('Trainingsplan wurde gespeichert!');
    }
  }

  downloadPlan(): void {
    if (this.plan) {
      const dataStr = JSON.stringify(this.plan, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `trainingsplan-${this.plan.name.replace(/\s+/g, '-')}.json`;
      link.click();
      URL.revokeObjectURL(url);
    }
  }

  newPlan(): void {
    this.router.navigate(['/profile']);
  }

  createNewPlan(): void {
    this.router.navigate(['/profile']);
  }

  back(): void {
    this.router.navigate(['/']);
  }

  getIntensityWidth(intensity: string): string {
    const widths: { [key: string]: string } = {
      low: '33%',
      medium: '66%',
      high: '100%'
    };
    return widths[intensity] || '50%';
  }
}
