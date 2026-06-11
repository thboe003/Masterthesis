<!-- AI-Powered Pole Sport Training Plan Generator - Master's Thesis Project -->

# Copilot Workspace Instructions

## Projektkontext
Diese Anwendung ist eine KI-gestützte Trainingsplan-Generierungsplattform für Pole Sport. Das Projekt besteht aus:
- **Backend**: FastAPI (Python) - REST API mit ML-Integration
- **Frontend**: Angular - Benutzeroberfläche
- **ML-Pipeline**: Fine-tuned Modell für Trainingsplan-Generierung
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

## Conventions

- **Language**: Python 3.10+ (Backend), TypeScript (Frontend)
- **API-Style**: RESTful mit JSON
- **Naming**: snake_case (Python), camelCase (TypeScript)
- **Versionierung**: Semantic Versioning

## Häufige Befehle

### Backend
- Starten: `cd backend && python -m uvicorn main:app --reload`
- Datenbank init: `python manage.py init-db`
- Daten laden: `python manage.py migrate-data`
- Tests: `pytest`

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
