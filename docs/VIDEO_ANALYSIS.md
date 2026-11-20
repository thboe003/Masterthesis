# Videoanalyse: Feedback zur Ausführung von Pole-Übungen

Nutzer:innen laden ein Trainingsvideo hoch und bekommen strukturiertes Feedback
zur Ausführung (Stärken, Fehler mit Frame-Bezug, Korrekturen, Sicherheitshinweise,
empfohlene Übungen). Das Feature baut auf der bestehenden, austauschbaren
LLM-Schicht auf (siehe `LLM_INTEGRATION.md`).

## Grundidee: Video → Schlüsselbilder → Vision-LLM

Die verwendeten Modelle verarbeiten Bilder, aber keine Videodateien. Deshalb wird
das Video im Backend in wenige, aussagekräftige Einzelbilder (Keyframes) zerlegt,
die als Bilder an ein multimodales Modell gehen.

**Warum nicht die Binärdaten des Videos?** Ein LLM interpretiert die Rohbytes
einer MP4-Datei nicht als Bild oder Bewegung – das sind komprimierte Codec-Daten,
für das Modell nur bedeutungsloser Text. Base64 ist lediglich das
*Transportformat* der APIs: Das JPEG eines Frames wird Base64-kodiert übertragen,
der Anbieter dekodiert es wieder und das Modell „sieht“ das Bild über seinen
Vision-Encoder. Genau das macht `ImageInput` in `services/llm/base.py`.

### Betrachtete Ansätze (für die Thesis)

| Ansatz | Idee | Vorteile | Nachteile |
|---|---|---|---|
| **A: Keyframes → Vision-LLM** (umgesetzt) | N Frames extrahieren, als Bilder senden | funktioniert mit allen Providern (lokal & Cloud), gut erklärbar, Frames referenzierbar | Bewegung zwischen Frames geht verloren, Token-Kosten pro Bild |
| **B: Pose-Schätzung + LLM** (optional zuschaltbar) | MediaPipe liefert Keypoints → Gelenkwinkel als Zahlen in den Prompt | objektive Messwerte (Kniestreckung, Beinspreizung), günstig | Pose-Modelle sind auf aufrechte Personen trainiert → bei Inverts unzuverlässig, Verdeckung durch die Stange |
| **C: Hybrid A + B** (umgesetzt, `VIDEO_POSE_ESTIMATION=true`) | Bilder **und** Winkel an das LLM | LLM kann Winkel mit Bild abgleichen | mehr Abhängigkeiten |
| **D: Native Video-Modelle** | z. B. Gemini (Video-Upload) oder Qwen2.5-VL (Video-Input) | zeitlicher Kontext | an bestimmte Modelle gebunden; intern wird ebenfalls mit Frames gesampelt; schwerer vergleichbar |

Ansatz D lässt sich später als weiterer Provider ergänzen, ohne den Rest der
Pipeline zu ändern. Für die Evaluation ist A vs. C (mit/ohne Pose) und
Einzelbilder vs. Kontaktbogen ein gut messbarer Vergleich.

## Ablauf

```
Angular /video-analysis
   │  multipart: Video + Übung + Level + Notizen (+ Frames, Modus, Pose, Ausschnitt)
   ▼
POST /api/v1/video-analysis/analyze           (api/video_analysis.py)
   1. Upload in Temp-Datei streamen (Größenlimit, Formatprüfung)
   2. prepare_video  (Worker-Thread, services/video_analysis.py)
        video/frames.py  → N Segmente, pro Segment schärfster Kandidat (Laplace-Varianz),
                            verkleinert auf VIDEO_FRAME_MAX_SIDE, JPEG
        video/pose.py    → optional MediaPipe → Gelenkwinkel je Frame
   3. Temp-Datei löschen (das Video wird nie gespeichert)
   4. Grounding: Soll-Ausführung der Übung aus dem Katalog (instructions)
                 + Kandidaten-Übungen für Empfehlungen
   5. LLMProvider.complete_json_with_images  (Ollama | OpenAI | Anthropic)
   6. Validierung gegen LLMVideoFeedback, bei Fehler 1 Retry mit Fehlermeldung
   7. Nachbearbeitung: Frame-Nummern → Zeitstempel, Empfehlungen → Katalog-IDs
   ▼
VideoAnalysisResult (Feedback + Thumbnails + Analyse-Metadaten für die Evaluation)
```

| Datei | Aufgabe |
|---|---|
| `backend/app/services/llm/base.py` | `ImageInput`, `complete_json_with_images` in der Provider-Schnittstelle |
| `backend/app/services/llm/providers.py` | Bild-Payloads für Ollama, OpenAI, Anthropic (`*_messages`, testbar) |
| `backend/app/services/llm/__init__.py` | `create_vision_provider` / `get_vision_provider` |
| `backend/app/services/video/frames.py` | Keyframe-Extraktion, Kontaktbogen, Thumbnails (OpenCV) |
| `backend/app/services/video/pose.py` | optionale Pose-Schätzung, Gelenkwinkel |
| `backend/app/services/video_analysis.py` | Prompts, Retry, Validierung, Nachbearbeitung |
| `backend/app/api/video_analysis.py` | Endpoints |
| `backend/app/schemas.py` | `LLMVideoFeedback`, `VideoAnalysisResult`, … |
| `frontend/src/app/components/video-analysis/` | Upload, Einstellungen, Ergebnisansicht |
| `backend/tests/test_video_analysis.py` | Tests mit synthetischem Video und Fake-Provider |

## Endpoints

| Methode | Pfad | Zweck |
|---|---|---|
| `POST` | `/api/v1/video-analysis/analyze` | Video hochladen → Feedback |
| `POST` | `/api/v1/video-analysis/frames-preview` | zeigt Bilder + Prompts, **ohne** LLM-Aufruf (Debugging, Anhang der Thesis) |
| `GET` | `/api/v1/video-analysis/exercises` | Pole-Übungen für die Auswahl (ohne Datenbank) |
| `GET` | `/api/v1/video-analysis/info` | konfiguriertes Vision-Modell und Limits |

Formularfelder für `analyze`: `video` (Pflicht), `exercise_id` oder `exercise_name`,
`experience_level`, `user_notes`, `num_frames` (1–16), `frame_mode` (`frames`|`grid`),
`use_pose`, `start_s`, `end_s`.

```bash
curl -F video=@invert.mp4 -F exercise_id=move_invert -F experience_level=intermediate \
     http://localhost:8000/api/v1/video-analysis/analyze
```

## Konfiguration (`backend/.env`)

```bash
# Vision-Modell – leer = LLM_PROVIDER mit Vision-Standardmodell
VISION_LLM_PROVIDER=ollama
VISION_LLM_MODEL=qwen2.5vl:7b        # ollama pull qwen2.5vl:7b  (Alternative: llama3.2-vision)
VISION_LLM_TIMEOUT_SECONDS=300
VISION_OLLAMA_NUM_CTX=16384          # Ollama-Standard (4096) reicht für mehrere Bilder nicht

VIDEO_NUM_FRAMES=8                   # Standard-Anzahl Keyframes
VIDEO_MAX_FRAMES=16
VIDEO_FRAME_MAX_SIDE=768             # kleiner = weniger Tokens
VIDEO_FRAME_MODE=frames              # frames | grid
VIDEO_POSE_ESTIMATION=false          # true → pip install mediapipe
VIDEO_MAX_UPLOAD_MB=200
```

Das Text-Modell für die Trainingspläne (`LLM_MODEL`) wird bewusst **nicht** für
die Videoanalyse verwendet, weil z. B. `llama3.1:8b` keine Bilder versteht.

Installation: `pip install opencv-python-headless` (steht in `requirements.txt`),
optional `pip install mediapipe`.

## Aufnahmetipps für Nutzer:innen

- seitlich bzw. schräg von vorne filmen, ganzer Körper **und** Stange im Bild
- Kamera fest aufstellen, gutes Licht, kontrastreiche Kleidung
- ein Move pro Video, kurze Clips (5–30 s) oder Ausschnitt setzen

## Datenschutz

Trainingsvideos zeigen Körper und Gesicht und sind personenbezogene Daten
(teils mit Gesundheitsbezug, z. B. Verletzungsangaben). Das Backend speichert
das Video nicht, nur die Frames werden an das Modell geschickt. Mit Ollama bleibt
alles lokal; bei Cloud-Providern verlassen die Frames den Rechner – das sollte
im UI bzw. in der Thesis transparent gemacht werden.

## Evaluation (Vorschläge für die Thesis)

`VideoAnalysisInfo` liefert pro Analyse Provider, Modell, Laufzeit (Vorverarbeitung
und Modell), Versuche, gesendete Bilder, Tokens und Warnungen. Damit lassen sich
vergleichen:

- Modelle (lokal vs. Cloud) bei gleichem Video
- Anzahl Frames (4 / 8 / 16) und Einzelbilder vs. Kontaktbogen: Qualität vs. Tokens/Latenz
- mit vs. ohne Pose-Winkel
- Übereinstimmung mit dem Feedback einer Trainerin auf einem kleinen, gelabelten Videoset
  (z. B. erkannte Fehler: Precision/Recall, Score-Abweichung)
- JSON-Validität / Retry-Rate

## Nächste Schritte

1. **Trainingsplan überarbeiten:** Feedback (`issues`, `recommended_exercises`) zusammen
   mit dem bestehenden Plan an den Plan-Generator geben und einen angepassten Plan
   erzeugen (Endpoint z. B. `POST /training-plans/{id}/revise`).
2. Analysen in der Datenbank speichern → Fortschritt über die Zeit.
3. Bewegungsbasierte Keyframe-Auswahl (Haltephasen erkennen statt gleichmäßig verteilen).
4. Skelett-Overlay auf die Frames zeichnen, bevor sie ans LLM gehen.
5. Provider für native Video-Modelle (Ansatz D) als Vergleich.
