<!-- AI-Powered Pole Sport Training Plan Generator - Master's Thesis Project -->

# Copilot Workspace Instructions

## Projektkontext
Diese Anwendung ist eine KI-gestützte Trainingsplan-Generierungsplattform für Pole Sport. Das Projekt besteht aus:
- **Backend**: FastAPI (Python) - REST API mit ML-Integration
- **Frontend**: Angular - Benutzeroberfläche
- **ML-Pipeline**: Fine-tuned Modell für Trainingsplan-Generierung
- **LLM-Schicht**: austauschbare Provider (Ollama lokal, OpenAI-kompatibel, Anthropic) in `backend/app/services/llm/`
- **Videoanalyse**: Feedback zur Ausführung von Pole-Übungen aus hochgeladenen Trainingsvideos (Keyframes → Vision-LLM)
- **Datenbank**: PostgreSQL mit SQLAlchemy ORM
- **Ziel**: Masterarbeit in angewandter Künstlicher Intelligenz

## Projektstruktur

```
masterthesis-pole-ai/
├── backend/              # FastAPI Backend
├── frontend/             # Angular Frontend
├── ml/                   # Machine Learning Pipeline
├── docs/                 # Dokumentation & Thesis
├── docker/               # Docker Setup
└── configs/              # Konfigurationsdateien
```

## Features

### 1. Trainingsplan-Generierung (`docs/LLM_INTEGRATION.md`)
`POST /api/v1/training-plans/generate` – Profilformular → Prompt mit Übungskatalog (Grounding) → LLM → Validierung gegen `LLMPlan` → `TrainingPlan`.

### 2. Videoanalyse / Ausführungs-Feedback (`docs/VIDEO_ANALYSIS.md`)
`POST /api/v1/video-analysis/analyze` (multipart) – Trainingsvideo hochladen, Feedback zur Ausführung erhalten.

Wichtige Designentscheidungen – bitte beibehalten:
- **LLMs bekommen nie die Videodatei oder deren Rohbytes**, sondern extrahierte JPEG-Keyframes als Bilder. Base64 ist nur das Transportformat der APIs.
- Frame-Extraktion in `backend/app/services/video/frames.py` (OpenCV): Video in N Segmente teilen, pro Segment den schärfsten Frame (Laplace-Varianz) wählen, auf `VIDEO_FRAME_MAX_SIDE` verkleinern. Modus `frames` (Einzelbilder) oder `grid` (ein Kontaktbogen).
- Pose-Schätzung (`video/pose.py`, MediaPipe) ist **optional** (`VIDEO_POSE_ESTIMATION`) und darf die Analyse nie abbrechen; Winkel sind nur Zusatzkontext für das LLM (bei Inverts unzuverlässig).
- Vision-Modell separat konfigurieren: `VISION_LLM_PROVIDER` / `VISION_LLM_MODEL` (Fallback: `LLM_PROVIDER` + Vision-Standardmodell, nie `LLM_MODEL`). Neue Provider müssen `complete_json_with_images` implementieren; Payloads über die reinen Funktionen `*_messages` in `providers.py` bauen.
- Grounding: Soll-Ausführung (`instructions`) der Übung aus dem Katalog in den Prompt; empfohlene Übungen nur aus dem mitgegebenen Katalog, IDs werden in der Nachbearbeitung gemappt.
- LLM-Antwort immer gegen `LLMVideoFeedback` (Pydantic) validieren, bei Fehler ein Retry mit Fehlermeldung; Frame-Nummern → Zeitstempel mappen, unbekannte verwerfen und als Warnung melden.
- Prompts auf Englisch, alle nutzersichtbaren Texte auf Deutsch. Sicherheit (Schultern, Griff, Nacken, Rücken) hat Vorrang.
- Hochgeladene Videos nur als Temp-Datei verarbeiten und danach löschen (Datenschutz). CPU-lastige Vorverarbeitung per `asyncio.to_thread`.
- Metadaten für die Evaluation (`VideoAnalysisInfo`: Modell, Laufzeiten, Tokens, Bilder, Warnungen) nicht entfernen.
- Geplant: Trainingsplan anhand des Video-Feedbacks überarbeiten (`issues` + `recommended_exercises` → Plan-Generator).

## Arbeitsregeln für KI-Assistenten

- **Nicht automatisch committen oder pushen.** Änderungen lokal vornehmen; Commit/Push nur auf ausdrückliche Anweisung.
- Bestehende Tests müssen weiter laufen; neue Logik mit Tests absichern, die ohne Netzwerk und ohne echtes Modell auskommen (Fake-Provider, synthetisches Video wie in `backend/tests/test_video_analysis.py`).
- Pydantic-Version aus `requirements.txt` beachten (2.4) – keine neueren APIs verwenden.
- Bei neuen Umgebungsvariablen `backend/.env.example` und die passende Doku in `docs/` ergänzen.
- Diese Datei und `AGENTS.md` aktuell halten, wenn sich Architektur oder Konventionen ändern.

## Conventions

- **Language**: Python 3.10+ (Backend), TypeScript (Frontend)
- **API-Style**: RESTful mit JSON (Video-Upload als `multipart/form-data`)
- **Naming**: snake_case (Python), camelCase (TypeScript)
- **Versionierung**: Semantic Versioning

## Häufige Befehle

### Backend
- Starten: `cd backend && python -m uvicorn main:app --reload`
- Datenbank init: `python manage.py init-db`
- Daten laden: `python manage.py migrate-data`
- Tests: `pytest` (nur Videoanalyse: `pytest tests/test_video_analysis.py`)
- Vision-Modell lokal: `ollama pull qwen2.5vl:7b`

### Frontend
- Starten: `cd frontend && ng serve`
- Build: `ng build`
- Tests: `ng test`

### Machine Learning
- Training: `python ml/train.py`
- Inference testen: `python ml/inference.py`

### Docker
- Stack starten: `docker-compose -f docker/docker-compose.yml up -d`
- Logs: `docker-compose logs -f backend`
- Stoppen: `docker-compose down`
