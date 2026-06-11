# Pole Sport AI Training Plan Generator
## Master's Thesis - Applied Artificial Intelligence

Ein KI-gesteuertes System zur automatischen Generierung personalisierter Trainingspläne für Pole Sport mit Fine-tuned Transformer-Modellen.

---

## 📋 Projektübersicht

Diese Anwendung nutzt Machine Learning und Deep Learning, um auf Basis von Benutzerprofilen optimale Trainingspläne für Pole Sport zu generieren. Die Lösung besteht aus:

- **FastAPI Backend**: REST API für Plan-Generierung und Datenverwaltung
- **Angular Frontend**: Responsive Benutzeroberfläche
- **ML Pipeline**: Fine-tuned Transformer-Modell für intelligente Planerstellung
- **PostgreSQL Datenbank**: Persistent Storage für Benutzer und Pläne
- **Docker**: Vollständige Containerisierung für Deployment

## 🚀 Quick Start

👉 **[GETTING_STARTED.md](docs/GETTING_STARTED.md)** - Vollständige Setup Anleitung

### Schnellstart mit Docker (Empfohlen)

```bash
# 1. Environment konfigurieren
cp docker/.env.example docker/.env

# 2. Stack starten
docker-compose -f docker/docker-compose.yml up -d

# 3. Im Backend Container Daten laden
docker-compose exec backend python manage.py migrate-data

# Services verfügbar:
# Frontend: http://localhost:4200
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Frontend Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate-data
python -m uvicorn main:app --reload
```

**Frontend:** ✨ Vollständig implementiert mit 5 Komponenten!
```bash
cd frontend
npm install
npm start
# Frontend läuft auf http://localhost:4200
```

---

## 📁 Projektstruktur

```
Masterthesis/
├── backend/                  # FastAPI Backend
│   ├── main.py              # Application entry point
│   ├── app/
│   │   ├── api/             # API routes
│   │   │   └── training_plans.py
│   │   ├── models/          # Database models
│   │   └── services/        # Business logic
│   ├── requirements.txt      # Python dependencies
│   └── .env.example         # Environment template
│
├── frontend/                # Angular Frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/  # UI components
│   │   │   └── services/    # HTTP services
│   │   ├── styles.scss      # Global styles
│   │   └── main.ts
│   ├── package.json
│   ├── angular.json
│   └── tsconfig.json
│
├── ml/                      # Machine Learning Pipeline
│   ├── config.py            # ML configuration
│   ├── model.py             # Model architecture
│   ├── train.py             # Training script
│   ├── inference.py         # Inference engine
│   ├── data/                # Training data
│   └── models/              # Saved model weights
│
├── docker/                  # Docker configuration
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   ├── docker-compose.yml
│   ├── nginx.conf
│   └── .env.example
│
├── docs/                    # Documentation & Thesis
│   ├── README.md
│   └── thesis/
│
└── README.md
```

---

## 🔧 Konfiguration

### Backend (.env)
```env
DATABASE_URL=postgresql://user:password@localhost:5432/pole_ai_db
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
SECRET_KEY=your-secret-key
MODEL_PATH=./models/pole_trainer_model
```

### Frontend (environment.ts)
```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api'
};
```

---

## 🧠 Machine Learning

### Modellarchitektur
- **Base**: Distilbert (Pre-trained Transformer)
- **Fine-tuning**: Adapter-based für effizientes Training
- **Output**: Trainingsplan-Sequenzen (max 200 Tokens)

### Training
```bash
cd ml
python train.py --epochs 10 --batch_size 32 --learning_rate 1e-4
```

### Inference
```python
from inference import TrainingPlanInference

inference = TrainingPlanInference(model_path="models/pole_trainer_v1.pth")
plan = inference.generate_plan({
    "age": 28,
    "experience_level": "intermediate",
    "fitness_level": 7,
    "available_days_per_week": 4,
    "goals": ["strength", "flexibility"]
})
```

---

## 📊 Datenverwaltung

Das Projekt integriert drei Datenquellen:

1. **free-exercise-db** - 800+ Open Source Trainingsübungen
2. **Pole Sport Spezifisch** - Pole-Tanz spezifische Moves
3. **Custom Data** - Benutzerdefinierte Übungen

### Daten laden

```bash
cd backend

# Komplette Datenmigration (empfohlen)
python manage.py migrate-data

# Oder einzelne Schritte:
python manage.py init-db              # Datenbank initialisieren
python manage.py fetch-exercises      # free-exercise-db laden
python manage.py import-exercises     # In DB importieren
```

### API für Übungen

```bash
# Alle Übungen auflisten
GET /api/v1/exercises?skip=0&limit=20

# Pole Sport Übungen filtern
GET /api/v1/exercises/pole-sport?level=intermediate

# Nach Muskelgruppe suchen
GET /api/v1/exercises/by-muscle/biceps

# Kategorien auflisten
GET /api/v1/exercises/categories

# Statistiken
GET /api/v1/exercises/stats
```

---

## 📋 Datenbank-Schema

### Exercise
```
- id (Primary Key)
- name
- category (strength, flexibility, endurance)
- level (beginner, intermediate, advanced)
- primary_muscles []
- secondary_muscles []
- instructions []
- is_pole_sport (boolean)
- source (free-exercise-db, pole-sport, custom)
```

### Pole Sport Move
```
- id
- name
- level (basic, intermediate, advanced, elite)
- prerequisites []
- progression_steps []
- conditioning_exercises []
- safety_tips []
```

### Training Plan
```
- id
- user_id
- name
- duration_weeks
- exercises []
```

Weitere Details: [DATA_MANAGEMENT.md](docs/DATA_MANAGEMENT.md)

---

## 📚 Dokumentation

- [Projektsstatus](docs/PROJECT_STATUS.md) - Aktueller Stand & Implementierungsbericht
- [Datenverwaltung](docs/DATA_MANAGEMENT.md) - Detaillierte Anleitung für Exercise DB Integration
- [Systemarchitektur](docs/ARCHITECTURE.md) - Technische Architektur und Datenfluss
- Thesis (in `/docs/thesis`) - Die Masterarbeit selbst

---

## 📚 API Dokumentation

### Swagger UI
Beim Starten des Backends verfügbar unter:
```
http://localhost:8000/docs
```

### Wichtigste Endpoints

#### 🔧 Trainingsplan-Verwaltung

**Trainingsplan generieren**
```http
POST /api/v1/training-plans/generate
Content-Type: application/json

{
  "age": 28,
  "experience_level": "intermediate",
  "fitness_level": 7,
  "available_days_per_week": 4,
  "goals": ["improve strength", "learn new moves"],
  "injuries_or_limitations": null
}
```

**Trainingsplan abrufen**
```http
GET /api/v1/training-plans/{plan_id}
```

#### 💪 Übungs-Management

**Alle Übungen auflisten (mit Filterung)**
```http
GET /api/v1/exercises?skip=0&limit=20&category=strength&level=beginner
```

**Pole Sport Übungen**
```http
GET /api/v1/exercises/pole-sport?level=intermediate
```

**Nach Muskelgruppe suchen**
```http
GET /api/v1/exercises/by-muscle/biceps
```

**Einzelne Übung abrufen**
```http
GET /api/v1/exercises/{exercise_id}
```

**Verfügbare Kategorien**
```http
GET /api/v1/exercises/categories
```

**Statistiken**
```http
GET /api/v1/exercises/stats

Response:
{
  "total_exercises": 850,
  "pole_sport_exercises": 5,
  "general_exercises": 845,
  "sources": ["free-exercise-db", "pole-sport"]
}
```

---

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm run test
```

---

## 🐳 Docker Commands

```bash
# Services starten
docker-compose -f docker/docker-compose.yml up -d

# Services stoppen
docker-compose -f docker/docker-compose.yml down

# Logs anzeigen
docker-compose -f docker/docker-compose.yml logs -f backend

# Database in Shell betreten
docker-compose exec postgres psql -U pole_user -d pole_ai_db

# Images bauen
docker-compose build
```

---

## 📊 Datenbankmigrationen

```bash
cd backend

# Migration erstellen
alembic revision --autogenerate -m "Description"

# Migration anwenden
alembic upgrade head

# Migration rückgängig machen
alembic downgrade -1
```

---

## 🔐 Sicherheit

- JWT-basierte Authentifizierung
- CORS-Konfiguration für Frontend
- Environment-basierte Secrets
- Passwort-Hashing mit bcrypt
- HTTPS-Unterstützung in Production

---

## 📖 Weitere Ressourcen

- [FastAPI Dokumentation](https://fastapi.tiangolo.com/)
- [Angular Dokumentation](https://angular.io/docs)
- [PyTorch](https://pytorch.org/)
- [HuggingFace Transformers](https://huggingface.co/docs/transformers/)

---

## 👤 Autor

Master's Thesis in Applied Artificial Intelligence

---

## 📝 Lizenz

TBD - Masterarbeit

---

## 🤝 Unterstützung

Bei Fragen oder Problemen:
1. Checke die Dokumentation in `/docs`
2. Öffne ein Issue im Repository
3. Kontaktiere den Autor

---

**Zuletzt aktualisiert**: 2026-06-11
