# Getting Started - Quick Start Guide

## 5-Minuten Setup

### Schritt 1: Projekt klonen (bereits geschehen)
```bash
cd c:\Users\boehm\OneDrive\Dokumente\GitHub\Masterthesis
```

### Schritt 2: Docker Setup (Empfohlen - Einfachster Weg)

```bash
# Environment Datei erstellen
cd docker
cp .env.example .env

# Stack starten
cd ..
docker-compose -f docker/docker-compose.yml up -d

# Verfügbar:
# Frontend:  http://localhost:4200
# Backend:   http://localhost:8000
# API Docs:  http://localhost:8000/docs
# Database:  postgres on localhost:5432
```

### Schritt 3: Daten laden

```bash
# Mit Docker Shell
docker-compose exec backend python manage.py migrate-data

# Oder lokal (siehe unten)
```

---

## Lokale Entwicklung (Ohne Docker)

### Backend Setup

```bash
# Terminal 1: Backend
cd backend

# Python 3.10+ erforderlich
python --version

# Virtual Environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Dependencies
pip install -r requirements.txt

# Environment Datei
cp .env.example .env

# Datenbank initialisieren
python manage.py init-db

# Daten laden
python manage.py migrate-data

# Server starten
python -m uvicorn main:app --reload
# → Backend läuft auf http://localhost:8000
```

### Frontend Setup (Neues Terminal)

```bash
# Terminal 2: Frontend
cd frontend

# Node.js 18+ erforderlich
node --version
npm --version

# Dependencies
npm install

# Development Server
npm start
# → Frontend läuft auf http://localhost:4200
```

### ML Pipeline (Neues Terminal)

```bash
# Terminal 3: ML
cd ml

# Falls noch nicht installiert:
pip install torch transformers scikit-learn numpy pandas

# Training (optional)
python train.py

# Inference testen
python inference.py
```

---

## Erste Tests

### Test 1: API Health Check
```bash
curl http://localhost:8000/health
```

Output sollte sein:
```json
{"status": "healthy"}
```

### Test 2: Übungen auflisten
```bash
curl http://localhost:8000/api/v1/exercises?limit=5
```

### Test 3: Pole Sport Übungen
```bash
curl http://localhost:8000/api/v1/exercises/pole-sport?level=intermediate
```

### Test 4: Swagger Documentation
Öffne im Browser:
```
http://localhost:8000/docs
```

---

## CLI Befehle

```bash
# Aus dem backend/ Verzeichnis:

# Datenbank initialisieren
python manage.py init-db

# Übungen von GitHub laden
python manage.py fetch-exercises

# In Datenbank importieren
python manage.py import-exercises

# Alles auf einmal (empfohlen)
python manage.py migrate-data

# Hilfe anzeigen
python manage.py --help
```

---

## Datenbankverbindung

### Mit Docker (PostgreSQL)
```bash
docker-compose exec postgres psql -U pole_user -d pole_ai_db

# Im psql prompt:
\dt                  # Show tables
SELECT COUNT(*) FROM exercises;
\q                   # Quit
```

### Lokal (SQLite)
```bash
# SQLite Datei ist im Projektroot: pole_ai.db
# Mit SQLite Browser oder CLI öffnen:
sqlite3 pole_ai.db
sqlite> SELECT COUNT(*) FROM exercises;
sqlite> .quit
```

---

## Häufige Probleme

### Problem: "Module not found"
```bash
# Sicherstellen dass Virtual Environment aktiviert ist
source venv/bin/activate  # oder: venv\Scripts\activate

# Dependencies neu installieren
pip install -r requirements.txt
```

### Problem: "Port already in use"
```bash
# Port 8000 (Backend) ändern:
python -m uvicorn main:app --reload --port 8001

# Port 4200 (Frontend) ist schwieriger, prüfe:
ng serve --port 4201
```

### Problem: "Cannot fetch free-exercise-db"
```bash
# Offline? Manuell laden:
wget https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json -O ml/data/exercises.json

# Dann importieren:
python manage.py import-exercises
```

### Problem: "Database locked" (SQLite)
```bash
# Lösche die alte DB und starten von vorne
rm pole_ai.db
python manage.py init-db
python manage.py migrate-data
```

---

## Nächste Schritte

1. **Frontend-Komponenten entwickeln**
   - User Profile Form
   - Training Plan Display
   - Exercise Browser

2. **ML-Modell trainieren**
   - Training-Daten sammeln
   - Modell fine-tunen
   - Inferenz optimieren

3. **Erweiterte Funktionen**
   - Benutzer-Authentifizierung
   - Progress Tracking
   - Performance Analytics

4. **Deployment vorbereiten**
   - Production Secrets managen
   - HTTPS konfigurieren
   - Monitoring setup

---

## Projekt-Struktur erkunden

```bash
# Wichtigste Dateien zum Anfang:
README.md                    # Überblick
docs/DATA_MANAGEMENT.md      # Datenverwaltung
docs/ARCHITECTURE.md         # Technische Details
backend/main.py              # FastAPI Entry Point
ml/model.py                  # ML Modell
```

---

## Hilfreiche Links

- **FastAPI**: https://fastapi.tiangolo.com/
- **Angular**: https://angular.io/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **PyTorch**: https://pytorch.org/
- **free-exercise-db**: https://github.com/yuhonas/free-exercise-db

---

## Support & Debugging

### Verbose Logging aktivieren
```bash
# Im Backend .env:
LOG_LEVEL=DEBUG

# Und restart
python -m uvicorn main:app --reload --log-level debug
```

### Alle Abhängigkeiten prüfen
```bash
pip list
npm list
```

### Git Status prüfen
```bash
git status
git log --oneline -5
```

---

**Du bist startklar! Happy coding! 🚀**

Wenn Fragen auftauchen, checke [DATA_MANAGEMENT.md](DATA_MANAGEMENT.md) und [ARCHITECTURE.md](ARCHITECTURE.md).
