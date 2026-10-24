# A4A Learn

A4A Learn is an accessible AI-powered learning platform designed for deaf and hard-of-hearing learners. The project combines structured learning content, curriculum-grounded AI tutoring, ISL practice, learner progress tracking, and teacher review workflows into a single experience.

## Project focus

This repository currently implements the core MVP for:

- Accessible learner experience with protected routes and a responsive web app
- AI tutor grounded in learning content, with evidence-aware responses
- ISL alphabet practice and prediction workflow
- Learner dashboards and progress analytics
- Assessments and learning progression
- Teacher review and escalation flows
- Accessibility preference management
- Backend API services, authentication, and persistence

## Current implementation status

The codebase has moved beyond a conceptual prototype and includes working application structure in both the frontend and backend.

### Frontend

The frontend is a React + TypeScript + Vite app with route-based screens for:

- Home
- Login
- Dashboard
- Learn
- Assessment
- Tutor
- ISL Practice
- Progress
- Reviews
- Accessibility Preferences

Implemented route structure includes protected learner pages and a shared app shell for consistent navigation.

### Backend

The backend is a FastAPI service with modular APIs for:

- Authentication and user management
- Learning content and lesson access
- Assessments
- Tutor / RAG interactions
- ISL prediction and practice workflows
- Progress tracking
- Teacher review flows
- Health and database checks

The code organization reflects the system currently being built around:

- app/api/routes
- app/auth
- app/core
- app/database
- app/rag
- app/isl
- app/services
- app/repositories
- app/schemas

## Architecture overview

```text
Frontend (React + TypeScript)
        │
        ▼
FastAPI backend
        │
        ├── Authentication + RBAC
        ├── Learning APIs
        ├── Assessment APIs
        ├── RAG / Tutor APIs
        ├── ISL APIs
        ├── Progress / Analytics APIs
        └── Review / Teacher Support APIs
        │
        ▼
Data and AI services
        ├── SQLAlchemy / PostgreSQL patterns
        ├── RAG + vector retrieval
        ├── LLM integration (Ollama / model-based workflows)
        └── ISL recognition pipeline (MediaPipe + ML classification)
```

## Tech stack

### Frontend

- React 19
- TypeScript
- Vite
- React Router

### Backend

- Python
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic
- Pytest

### AI / ML

- Retrieval-augmented generation
- Embedding-based retrieval
- Local LLM workflows
- MediaPipe-based hand landmark processing
- ML classification for ISL alphabet recognition

## Repository structure

```text
A4A-Learn/
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── ai/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── core/
│   │   ├── database/
│   │   ├── isl/
│   │   ├── rag/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── utils/
│   ├── reports/
│   ├── scripts/
│   ├── tests/
│   ├── .env.example
│   ├── alembic.ini
│   ├── requirements.txt
│   └── structure.txt
├── frontend/
│   ├── src/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── package-lock.json
├── CHANGELOG.md
├── LICENSE
├── README.md
├── docker-compose.yml
├── requirements.txt
├── alembic.ini
└── structure.txt
```

## Key user flows now represented in code

- Learner login and authenticated experience
- Learning page with content access
- Tutor page for question asking and AI support
- Assessment page for evaluation flow
- ISL practice page for sign learning interaction
- Progress page for learner analytics
- Reviews page for teacher review workflow
- Accessibility page for personalization and usage accommodations

## Run locally

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create or update your environment configuration as needed from `.env.example` and then run:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

### 3. Validate frontend build

```bash
cd frontend
npm run typecheck
npm run build
```

## Testing

The repository includes a backend test suite covering:

- RAG and retrieval behavior
- Tutor intent and prompt strategies
- Assessment and lesson workflows
- ISL-related behaviors
- Review and escalation logic
- API and repository behaviors

Examples of test areas in the repo include:

- `backend/tests/test_rag_service.py`
- `backend/tests/test_tutor_intent_classifier.py`
- `backend/tests/test_tutor_prompt_strategy.py`
- `backend/tests/test_assessment_service.py`
- `backend/tests/test_python_intent.py`

Run tests with:

```bash
cd backend
pytest
```

## Design principles reflected in the code

- Accessibility first in the learner experience
- Grounded AI responses rather than unsupported generation
- Evidence-aware behavior and abstentions when knowledge is insufficient
- Human oversight and teacher accountability
- Progress and analytics for learning improvement
- Clear separation between frontend, API, domain services, and AI/ML logic

## Current maturity

This repo is not just a planning document; it contains an active MVP implementation with:

- a functional backend service layer
- a route-driven frontend app
- AI-assisted tutoring workflows
- ISL practice capabilities
-assessment / learning experience integration
- progress and review tracking

## Roadmap

The codebase already reflects substantial progress toward the MVP, and the next high-value work is likely to be:

- UI completion and polish across learner-touch surfaces
- tighter integration between frontend and API workflows
- production deployment and environment hardening
- stronger observability, testing, and security validation
- expanded ISL and accessibility testing
- scaling the model and retrieval pipeline for broader usage

## License

This project is licensed under the terms of the repository license file.

## Acknowledgement

A4A Learn is being developed as an academic and engineering project focused on accessible, trustworthy AI for learning experiences for deaf and hard-of-hearing learners.
