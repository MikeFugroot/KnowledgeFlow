# KnowledgeFlow

KnowledgeFlow is an AI-powered knowledge management web application. It provides document import, LLM-assisted organization, semantic search, knowledge profiling, background task tracking, and a Vue-based dashboard for managing personal learning materials.

This repository keeps only the core web application code:

- `backend/`: FastAPI backend, database models, API routes, document processing, LLM integration, search, and task workers.
- `frontend/`: Vue 3 + Vite frontend, pages, stores, API clients, and UI components.

Local data, uploaded files, models, test documents, generated indexes, and private environment files are intentionally ignored.

## Features

- Import and process documents and web content
- Organize content with Qwen or DeepSeek-compatible LLM APIs
- Manage documents, sections, tags, categories, and summaries
- Build semantic search indexes with sentence-transformers and FAISS
- Track background processing tasks through WebSocket updates
- Generate and view knowledge profile insights
- Configure runtime settings from the web UI

## Tech Stack

Backend:

- FastAPI
- SQLAlchemy + Alembic
- SQLite by default
- Pydantic settings
- sentence-transformers + FAISS
- faster-whisper / openai-whisper for media transcription

Frontend:

- Vue 3
- Vite
- TypeScript
- Pinia
- Vue Router
- Element Plus
- ECharts

## Project Structure

```text
KnowledgeFlow/
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── utils/
│   │   └── workers/
│   ├── migrations/
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── composables/
│   │   ├── layouts/
│   │   ├── router/
│   │   ├── stores/
│   │   ├── styles/
│   │   └── views/
│   ├── .env.example
│   └── package.json
├── .gitignore
└── README.md
```

## Setup

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Edit `backend/.env` and set your local values:

```env
API_PROVIDER=qwen
DASHSCOPE_API_KEY=your-dashscope-api-key-here
DEEPSEEK_API_KEY=
FERNET_KEY=your-fernet-key-here
```

Generate a Fernet key with:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Start the backend:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```powershell
cd frontend
npm install
copy .env.example .env
npm run dev
```

The frontend runs at:

```text
http://localhost:5173
```

The backend runs at:

```text
http://localhost:8000
```

## Common Commands

Backend:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```powershell
npm run dev
npm run type-check
npm run build
```

## Environment Files

Real environment files are not committed:

- `backend/.env`
- `frontend/.env`

Use the included example files instead:

- `backend/.env.example`
- `frontend/.env.example`

## Notes

- Uploaded files, generated indexes, databases, local models, and test documents are ignored by Git.
- Do not commit real API keys, cookies, database files, or model weights.
- The default backend database is SQLite under the backend data directory.
