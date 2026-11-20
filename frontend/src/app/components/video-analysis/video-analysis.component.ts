import { Component, ElementRef, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { TrainingPlanService } from '../../services/training-plan.service';
import {
  AnalyzableExercise,
  AnalyzedFrame,
  ExecutionIssue,
  IssueSeverity,
  VideoAnalysisRequest,
  VideoAnalysisResult,
} from '../../models/index';

const SEVERITY_ORDER: Record<IssueSeverity, number> = { safety: 0, major: 1, moderate: 2, minor: 3 };

@Component({
  selector: 'app-video-analysis',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './video-analysis.component.html',
  styleUrl: './video-analysis.component.css'
})
export class VideoAnalysisComponent implements OnInit, OnDestroy {
  @ViewChild('player') player?: ElementRef<HTMLVideoElement>;

  readonly maxUploadMb = 200;
  readonly severityLabels: Record<IssueSeverity, string> = {
    safety: 'Sicherheit',
    major: 'Wichtig',
    moderate: 'Mittel',
    minor: 'Gering',
  };
  readonly confidenceLabels = { low: 'niedrig', medium: 'mittel', high: 'hoch' };

  exercises: AnalyzableExercise[] = [];
  selectedFile: File | null = null;
  videoUrl: string | null = null;
  dragOver = false;

  exerciseId = '';
  exerciseName = '';
  experienceLevel: '' | 'beginner' | 'intermediate' | 'advanced' = '';
  userNotes = '';
  numFrames = 8;
  frameMode: 'frames' | 'grid' = 'frames';
  usePose = false;
  startS: number | null = null;
  endS: number | null = null;
  showAdvanced = false;

  isLoading = false;
  errorMessage: string | null = null;
  result: VideoAnalysisResult | null = null;

  constructor(private api: ApiService, private trainingPlanService: TrainingPlanService) {}

  ngOnInit(): void {
    const profile = this.trainingPlanService.getUserProfile();
    if (profile?.experience_level) {
      this.experienceLevel = profile.experience_level;
    }
    this.api.getAnalyzableExercises().subscribe({
      next: (items) => (this.exercises = items),
      error: () => (this.exercises = []),
    });
  }

  ngOnDestroy(): void {
    this.revokeUrl();
  }

  // ------------------------------------------------------------------ upload
  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files?.length) {
      this.setFile(input.files[0]);
    }
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    this.dragOver = false;
    const file = event.dataTransfer?.files?.[0];
    if (file) {
      this.setFile(file);
    }
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.dragOver = true;
  }

  private setFile(file: File): void {
    this.errorMessage = null;
    if (!file.type.startsWith('video/')) {
      this.errorMessage = 'Bitte eine Videodatei auswählen (z. B. .mp4 oder .mov).';
      return;
    }
    if (file.size > this.maxUploadMb * 1024 * 1024) {
      this.errorMessage = `Das Video ist größer als ${this.maxUploadMb} MB.`;
      return;
    }
    this.revokeUrl();
    this.selectedFile = file;
    this.videoUrl = URL.createObjectURL(file);
    this.result = null;
    this.startS = null;
    this.endS = null;
  }

  removeFile(): void {
    this.revokeUrl();
    this.selectedFile = null;
    this.result = null;
  }

  private revokeUrl(): void {
    if (this.videoUrl) {
      URL.revokeObjectURL(this.videoUrl);
      this.videoUrl = null;
    }
  }

  // ------------------------------------------------------------------ trimming
  setStartFromPlayer(): void {
    this.startS = this.currentTime();
  }

  setEndFromPlayer(): void {
    this.endS = this.currentTime();
  }

  private currentTime(): number | null {
    const t = this.player?.nativeElement.currentTime;
    return t === undefined ? null : Math.round(t * 10) / 10;
  }

  seekTo(seconds: number): void {
    const video = this.player?.nativeElement;
    if (video) {
      video.currentTime = seconds;
      video.pause();
      video.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }

  // ------------------------------------------------------------------ analysis
  get trimInvalid(): boolean {
    return this.startS !== null && this.endS !== null && this.endS <= this.startS;
  }

  analyze(): void {
    if (!this.selectedFile || this.trimInvalid) {
      return;
    }
    const request: VideoAnalysisRequest = {
      video: this.selectedFile,
      exercise_id: this.exerciseId || undefined,
      exercise_name: this.exerciseId ? undefined : this.exerciseName.trim() || undefined,
      experience_level: this.experienceLevel || undefined,
      user_notes: this.userNotes.trim() || undefined,
      num_frames: this.numFrames,
      frame_mode: this.frameMode,
      use_pose: this.usePose,
      start_s: this.startS ?? undefined,
      end_s: this.endS ?? undefined,
    };

    this.isLoading = true;
    this.errorMessage = null;
    this.result = null;
    this.api.analyzeVideo(request).subscribe({
      next: (result) => {
        this.isLoading = false;
        this.result = result;
      },
      error: (error) => {
        this.isLoading = false;
        console.error('Video analysis failed:', error);
        const detail = typeof error?.error?.detail === 'string' ? error.error.detail : null;
        switch (error?.status) {
          case 503:
            this.errorMessage = detail ?? 'Das Vision-Modell ist nicht erreichbar. Läuft der LLM-Server bzw. ist ein Vision-Modell konfiguriert?';
            break;
          case 502:
            this.errorMessage = 'Das Modell hat kein gültiges Feedback geliefert. Bitte versuche es erneut.';
            break;
          case 413:
          case 415:
          case 422:
            this.errorMessage = detail ?? 'Das Video konnte nicht verarbeitet werden.';
            break;
          default:
            this.errorMessage = 'Fehler bei der Videoanalyse. Bitte versuche es später erneut.';
        }
      },
    });
  }

  // ------------------------------------------------------------------ view helpers
  get sortedIssues(): ExecutionIssue[] {
    return [...(this.result?.feedback.issues ?? [])].sort(
      (a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity]
    );
  }

  framesFor(issue: ExecutionIssue): AnalyzedFrame[] {
    return (this.result?.frames ?? []).filter((f) => issue.frame_numbers.includes(f.number));
  }

  scoreClass(score: number | null | undefined): string {
    if (score === null || score === undefined) return 'score-none';
    if (score >= 8) return 'score-good';
    if (score >= 5) return 'score-medium';
    return 'score-low';
  }

  formatSeconds(value: number): string {
    return `${value.toFixed(1)} s`;
  }

  formatSize(bytes: number): string {
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }
}
