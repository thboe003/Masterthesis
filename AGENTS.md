# AGENTS.md – Hinweise für KI-Coding-Assistenten

Gilt für alle Assistenten (Claude, Copilot, OpenCode, Codex, …). Ausführliche
Projektbeschreibung: `.github/copilot-instructions.md`.

## Projekt

Masterarbeit (angewandte KI): Anwendung zur Erstellung von Pole-Sport-Trainingsplänen
mit LLMs sowie Videoanalyse ausgeführter Pole-Übungen und darauf basierender
Überarbeitung der Trainingspläne.

- Backend: FastAPI (`backend/`), Python 3.10+, Pydantic 2.4
- Frontend: Angular 17, Standalone Components (`frontend/`)
- LLM-Schicht: `backend/app/services/llm/` – Provider über `.env` austauschbar
- Doku: `docs/LLM_INTEGRATION.md` (Trainingspläne), `docs/VIDEO_ANALYSIS.md` (Videoanalyse)

## Regeln

1. **Niemals automatisch committen oder pushen.** Nur auf ausdrückliche Anweisung.
2. Tests: `cd backend && pytest`. Neue Logik mit Tests ohne Netzwerk/echtes Modell absichern.
3. Prompts an Modelle auf Englisch, nutzersichtbare Texte auf Deutsch.
4. LLM-Ausgaben immer gegen Pydantic-Schemas validieren (mit einem Retry), nie ungeprüft an das Frontend geben.
5. Neue Umgebungsvariablen in `backend/.env.example` und der Doku ergänzen.

## Videoanalyse (Ausführungs-Feedback)

- Ablauf: Upload (`POST /api/v1/video-analysis/analyze`) → Temp-Datei → Keyframes
  (`services/video/frames.py`) → optional Pose-Winkel (`services/video/pose.py`) →
  Vision-LLM (`complete_json_with_images`) → `LLMVideoFeedback` → `VideoAnalysisResult`.
- Modelle sehen **Bilder, keine Videos**: Das Video wird in N scharfe, gleichmäßig verteilte
  JPEG-Frames zerlegt. Rohbytes eines Videos an ein LLM zu schicken ist kein sinnvoller Weg.
- Vision-Modell über `VISION_LLM_PROVIDER` / `VISION_LLM_MODEL` (z. B. Ollama `qwen2.5vl:7b`).
- Pose-Schätzung ist optional und darf die Analyse nie abbrechen.
- Videos werden nicht gespeichert (Datenschutz).
- Evaluations-Metadaten (`VideoAnalysisInfo`) erhalten.
- Nächster Schritt: Trainingsplan auf Basis des Feedbacks überarbeiten.
