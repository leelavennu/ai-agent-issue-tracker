# AI-Agent-Ready Full-Stack Issue Tracker

## Demo
No public hosted demo yet. Run locally with the setup steps below.

**Status:** In progress — local full-stack project; no production deployment claimed.

## Tech Stack
- Python FastAPI
- React TypeScript + Vite + React Router
- SQLite with SQLAlchemy
- Pydantic
- Pytest
- Jest + React Testing Library
- Docker and Docker Compose
- Git

## Features
- CRUD, filtering, pagination, search, header-based role gating (`X-User-Role`) as a development authorization stub, and validation
- Responsive issue list, create, edit, and detail screens
- Loading, empty, network error, validation, and success-through-navigation states
- API sorting by id, title, priority, status, created_at, or updated_at
- Optimistic locking using an integer `version`; stale edits return `409` with a refresh warning

## Setup
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Docker
docker-compose up
```

### API examples
```bash
# Create
curl -X POST http://localhost:8000/issues -H 'Content-Type: application/json' \
  -d '{"title":"Add keyboard shortcuts","description":"Improve navigation","priority":"high"}'

# List with filters, pagination, and sorting
curl 'http://localhost:8000/issues?status=open&priority=high&search=keyboard&page=1&limit=10&sort=updated_at&order=desc'

# Admin-only delete
curl -X DELETE http://localhost:8000/issues/1 -H 'X-User-Role: admin'
```

## Edge Cases and Validation
- **Empty and long titles:** Pydantic rejects blank titles and titles over 200 characters. The UI also validates before sending.
- **Duplicate issues:** Titles are unique and duplicates return `409 Conflict`.
- **Invalid IDs:** Missing records, including `999999`, return `404 Not Found`.
- **Permissions and expired sessions:** `DELETE` requires `X-User-Role: admin`; missing or `user` headers return `403`. Unsupported roles return `401`.
- **Special characters:** `<script>`, emoji, and SQL-like input are treated as plain values. React renders text, not HTML, and SQLAlchemy uses bound parameters.
- **Failed API / slow response:** The UI has explicit loading and error states; fetch errors display “Failed to load”.
- **Empty database:** The list displays “No issues found”.
- **Page refresh after submission:** Created and edited issues navigate to a URL-backed detail page, so refresh loads from the API.
- **Concurrent edits:** Each update can include the loaded `version`. A stale version returns `409` and warns the user instead of silently overwriting newer work. Updates without a version use last-write-wins for simple clients.
- **Accessibility:** Every form control has a label, actions are keyboard focusable, status messages use alert semantics, and color is supplemented by text.

## Testing
```bash
cd backend
pytest -q

cd ../frontend
npm install
npm test -- --runInBand
npm run build
```

## Verified test run

Run on 2026-10-04:

- Backend: **12 passed**
- Deterministic verifier: **7 passed**
- Frontend Jest: **2 passed**
- Frontend production build: **passed**

The API contract uses `/issues` routes. The `X-User-Role` header is development authorization gating, not production authentication.

## Project structure
```text
backend/              FastAPI app, SQLAlchemy model, Pydantic schemas, Pytest tests
frontend/src/         React + TypeScript + React Router UI and Jest tests
docker-compose.yml    Local full-stack orchestration
```
