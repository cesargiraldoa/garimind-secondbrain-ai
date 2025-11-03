# GariMind MVP Starter (2025-11-03)

Estructura mínima para **GariMind CésarStyle™** con:

- **Backend**: FastAPI + SQLAlchemy (PostgreSQL o SQLite), Uvicorn.
- **Frontend**: Streamlit (Daily Magnet, Diario, Memoria/Tareas, Proyectos).
- **Infra**: `docker-compose.yml` con PostgreSQL, variables `.env`.
- **Proyecto/Folders**: endpoint y UI para crear carpetas por proyecto en `data/projects/<slug>`.

## 1) Requisitos rápidos

- Python 3.10+
- Node *no requerido* (Streamlit)
- Docker opcional para Postgres

## 2) Variables de entorno

Copia `.env.example` a `.env` y ajusta si vas a usar Postgres.
Por defecto usamos SQLite (`sqlite+aiosqlite:///./garimind.db`) para correr inmediato.

```
cp .env.example .env
```

## 3) Levantar en local (modo rápido, sin Docker)

Ventana 1 (backend):
```
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Ventana 2 (frontend):
```
cd frontend
pip install -r requirements.txt
streamlit run Home.py
```

## 4) Con Postgres (opcional)

```
cd infra
docker compose up -d
```

Luego configura `DATABASE_URL` en `.env` como:
```
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/garimind
```

## 5) Endpoints MVP

- `POST /api/tareas`, `GET /api/tareas`
- `POST /api/recuerdos`, `GET /api/recuerdos`
- `GET /api/daily-magnet`
- `GET /api/diario`
- `POST /api/inbox/capturar` (texto→tarea/recuerdo)
- `POST /api/projects` (crea proyecto y carpeta `data/projects/<slug>`)
- `GET /api/projects`

## 6) Páginas Streamlit

- **Home (Daily Magnet)**
- **Diario**
- **Memoria & Tareas**
- **Proyectos** (crear carpeta, listar proyectos)

## 7) Notas

- Modelo de datos mínimo con 4 tablas: `proyectos`, `tareas`, `recuerdos`, `interacciones`.
- El backend acepta SQLite por defecto; para producción, usa PostgreSQL.
- La carpeta `data/projects` simula el *file storage* por proyecto.
