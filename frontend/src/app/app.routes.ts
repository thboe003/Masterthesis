import { Routes } from '@angular/router';
import { HomeComponent } from './components/home/home.component';
import { ExerciseListComponent } from './components/exercise-list/exercise-list.component';
import { UserProfileComponent } from './components/user-profile/user-profile.component';
import { TrainingPlanComponent } from './components/training-plan/training-plan.component';
import { VideoAnalysisComponent } from './components/video-analysis/video-analysis.component';

export const routes: Routes = [
  {
    path: '',
    component: HomeComponent
  },
  {
    path: 'exercises',
    component: ExerciseListComponent
  },
  {
    path: 'training-plan',
    component: UserProfileComponent
  },
  {
    path: 'my-plans',
    component: TrainingPlanComponent
  },
  {
    path: 'video-analysis',
    component: VideoAnalysisComponent
  },
  {
    path: '**',
    redirectTo: ''
  }
];
