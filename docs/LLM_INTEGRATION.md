# LLM-Integration: Trainingsplan-Generierung

Der Endpoint `POST /api/v1/training-plans/generate` erzeugt aus den Parametern des
Profilformulars einen Trainingsplan mit einem Large Language Model. Das Modell ist
austauschbar und wird nur über Umgebungsvariablen gewählt.

## Ablauf

```
Profilformular (Angular)
   │  TrainingPlanRequest: Alter, Level, Fitness, Tage/Woche, Dauer, Ziele, Einschränkungen
   ▼
plan_generator.generate_training_plan
   1. exercise_catalog.select_candidates  → passende Übungen aus DB/JSON (Grounding)
   2. build_user_prompt + SYSTEM_PROMPT   → Prompt mit Profil + Übungskatalog
   3. LLMProvider.complete_json           → Ollama | OpenAI-kompatibel | Anthropic
   4. Validierung gegen LLMPlan (Pydantic), bei Fehler 1 Retry mit Fehlermeldung
   5. Nachbearbeitung: Übungen auf Katalog-IDs mappen, Plausibilität prüfen
   ▼
TrainingPlan (+ generation: Provider, Modell, Latenz, Tokens, Warnungen)
```

| Datei | Aufgabe |
|---|---|
| `backend/app/services/llm/base.py` | Abstrakte Schnittstelle `LLMProvider`, JSON-Extraktion, Fehlerklassen |
| `backend/app/services/llm/providers.py` | Ollama, OpenAI-kompatibel, Anthropic (nur `httpx`, kein SDK) |
| `backend/app/services/llm/__init__.py` | Factory: wählt den Provider über `LLM_PROVIDER` |
| `backend/app/services/exercise_catalog.py` | Lädt Übungen, filtert nach Level, Equipment und Zielen |
| `backend/app/services/plan_generator.py` | Prompts, Retry, Validierung, Nachbearbeitung |
| `backend/app/schemas.py` | Request-, LLM- und Response-Schemas |

## Provider wählen

In `backend/.env` (Vorlage: `backend/.env.example`):

```bash
# Lokal mit Ollama (Standard)
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1:8b          # oder qwen2.5:7b, mistral, ...

# OpenAI-kompatibel, z. B. LM Studio
LLM_PROVIDER=openai
OPENAI_BASE_URL=http://localhost:1234/v1
LLM_MODEL=<name des geladenen modells>

# Anthropic
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=...
```

Ollama lokal starten:

```bash
ollama pull llama3.1:8b
ollama serve          # läuft auf http://localhost:11434
```

Im Docker-Setup erreicht das Backend Ollama auf dem Host über
`http://host.docker.internal:11434` (bereits in `docker-compose.yml` eingetragen).

## Hilfreiche Endpoints

- `GET  /api/v1/training-plans/llm-info` – aktiver Provider und Modell
- `POST /api/v1/training-plans/prompt-preview` – zeigt die Prompts, ohne das Modell aufzurufen (z. B. für den Anhang der Arbeit)

## Fehlerverhalten

| HTTP | Bedeutung |
|---|---|
| 503 | LLM-Server nicht erreichbar, Timeout oder fehlender API-Key |
| 502 | Modell hat auch nach dem Retry kein gültiges JSON / keinen gültigen Plan geliefert |
| 422 | Ungültige Eingabe aus dem Formular |

## Tests

```bash
cd backend
pytest tests/test_plan_generator.py
```

Die Tests verwenden einen Fake-Provider und brauchen weder Modell noch Netzwerk.

## Ansatzpunkte für die Evaluation

`generation` in der Antwort enthält Provider, Modell, Latenz, Token-Zahlen, Anzahl der
Versuche, nicht im Katalog gefundene Übungen und Plausibilitätswarnungen (falsche Anzahl
an Einheiten, überschrittene Session-Dauer). Damit lassen sich verschiedene Modelle
direkt vergleichen.
