"""
Data import documentation and guides.
"""

# DATENVERWALTUNGS-GUIDE für Pole Sport AI Training Generator

## Übersicht

Das Projekt integriert drei Datenquellen:

1. **free-exercise-db** - Open Source Trainingsübungen (800+)
2. **Pole Sport Specific Data** - Pole-Tanz spezifische Moves und Übungen
3. **Custom Data** - Benutzerdefinierte Trainingsübungen

---

## Getting Started

### 1. Datenbank initialisieren

```bash
cd backend

# Mit CLI-Tool
python manage.py init-db

# Oder mit Python
python -c "from app.core.database import init_db; init_db()"
```

### 2. Übungen vom free-exercise-db laden

Es gibt zwei Optionen:

**Option A: Automatischer Download (Online)**
```bash
python manage.py fetch-exercises
```
Dies lädt die Daten online von GitHub und speichert sie lokal.

**Option B: Manuelle Integration**
```bash
# Manuell das Repository klonen
git clone https://github.com/yuhonas/free-exercise-db.git
cp free-exercise-db/dist/exercises.json ml/data/exercises.json
```

### 3. Daten in Datenbank importieren

```bash
python manage.py import-exercises
```

### 4. Komplette Migration (All-in-One)

```bash
python manage.py migrate-data
```

Dies führt alle Schritte automatisch aus:
- Initialisiert die Datenbank
- Lädt free-exercise-db Daten
- Importiert allgemeine Übungen
- Importiert Pole Sport spezifische Übungen

---

## Datenstruktur

### Exercise Model

```json
{
  "id": "unique_exercise_id",
  "name": "Exercise Name",
  "description": "Description",
  "category": "strength",           // strength, flexibility, endurance, etc.
  "level": "beginner",              // beginner, intermediate, advanced
  "force": "push",                  // push, pull, static
  "mechanic": "compound",           // compound, isolation
  "equipment": "dumbbell",          // optional
  "primary_muscles": ["biceps"],
  "secondary_muscles": ["forearms"],
  "instructions": ["step 1", "step 2"],
  "images": ["path/to/image.jpg"],
  "is_pole_sport": false,
  "source": "free-exercise-db",
  "source_url": "https://..."
}
```

### Pole Sport Moves

Pole-spezifische Moves sind hierarchisch strukturiert:

```python
{
  "id": "invert",
  "name": "Invert",
  "level": "advanced",
  "prerequisites": ["pole_sit", "spin"],
  "progression_steps": ["shoulder_shrug", "partial_invert", "full_invert"],
  "primary_muscles": ["core", "shoulder"],
  "conditioning_exercises": ["pole_invert_strength", "shoulder_exercises"]
}
```

---

## API Endpoints

### Übungen auflisten
```bash
GET /api/v1/exercises?skip=0&limit=10&category=strength&level=beginner
```

### Pole Sport Übungen filtern
```bash
GET /api/v1/exercises/pole-sport?level=intermediate
```

### Nach Muskelgruppe suchen
```bash
GET /api/v1/exercises/by-muscle/biceps
```

### Statistiken
```bash
GET /api/v1/exercises/stats
```

---

## Benutzerdefinierte Daten hinzufügen

### Neue Pole Sport Übung in CLI Integrieren

Bearbeite `backend/app/core/data_loader.py`:

```python
POLE_EXERCISES = [
    {
        "id": "my_new_move",
        "name": "My New Pole Move",
        "description": "Description here",
        "level": "intermediate",
        "category": "strength",
        "primary_muscles": ["arm", "core"],
        ...
    },
    # ... weitere Übungen
]
```

Dann erneut importieren:
```bash
python manage.py import-exercises
```

### Direkt in DB hinzufügen

```python
from app.core.database import SessionLocal
from app.models import Exercise

db = SessionLocal()

new_exercise = Exercise(
    id="custom_move_001",
    name="Custom Pole Move",
    category="strength",
    level="advanced",
    is_pole_sport=True,
    source="custom"
)

db.add(new_exercise)
db.commit()
db.close()
```

---

## Fehlerbehebung

### free-exercise-db kann nicht geladen werden

1. Internet-Verbindung prüfen
2. GitHub ist erreichbar: `curl https://github.com`
3. Manuell herunterladen und lokal speichern:
   ```bash
   wget https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json -O ml/data/exercises.json
   ```

### Datenbank-Fehler

1. PostgreSQL läuft (falls in Benutzung):
   ```bash
   docker-compose exec postgres psql -U pole_user -d pole_ai_db
   ```

2. SQLite (default für Entwicklung) prüfen:
   ```bash
   ls -la pole_ai.db
   ```

### Duplikate beim Import

Der Importer überspringt automatisch existierende Übungen. Um erneut zu importieren:

```bash
# Backup erstellen
cp pole_ai.db pole_ai.db.backup

# Datenbank löschen und neu initialisieren
rm pole_ai.db
python manage.py migrate-data
```

---

## Performance-Tipps

- Der erste Datenbankzugriff ist langsam (~3-5s für 800+ Übungen)
- Indexe auf `category`, `level`, `is_pole_sport` sind erstellt
- Pagination verwenden: `/exercises?skip=0&limit=20`

---

## Weitere Ressourcen

- free-exercise-db: https://github.com/yuhonas/free-exercise-db
- FastAPI ORM: https://fastapi.tiangolo.com/
- SQLAlchemy: https://www.sqlalchemy.org/
