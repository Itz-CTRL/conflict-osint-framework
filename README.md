# SOKO AERIAL OSINT Platform

A full-stack OSINT investigation platform for username tracking and misinformation attribution.

---

## Project Structure

```
soko-osint/
├── backend/           ← Flask Python API
│   ├── app.py
│   ├── analyzer.py
│   ├── database.py
│   ├── scraper.py
│   └── requirements.txt
├── src/               ← React frontend
│   ├── App.jsx
│   ├── themes.js
│   ├── index.js
│   ├── index.css
│   ├── utils/
│   │   └── api.js
│   └── components/
│       ├── Header.jsx
│       ├── Ticker.jsx
│       ├── Dashboard.jsx
## SOKO AERIAL OSINT Platform

A full-stack OSINT investigation platform (Flask backend + React frontend).

---

**Repository layout (actual)**

```
soko-osint/
├── backend/               # Flask API (Python)
│   ├── app.py
│   ├── analyzer.py
│   ├── database.py
│   ├── scraper.py
│   ├── network_builder.py
│   ├── requirements.txt
│   └── Pipfile
├── Frontend/              # React app (create-react-app)
│   ├── package.json
│   ├── public/
│   │   └── index.html
│   └── src/
│       ├── App.jsx
│       ├── index.js
│       ├── index.css
│       ├── themes.js
│       ├── components/
│       └── utils/
└── README.md
```

---

## Requirements

- Python 3.9+ (backend)
- Node.js 18+ and npm (frontend)

On Linux the instructions below assume a POSIX shell (bash/zsh).

---

## Quick start (Linux / macOS)

1. Backend (API):

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

This starts the Flask backend on http://127.0.0.1:5000. Health: http://127.0.0.1:5000/api/health

2. Frontend (React):

```bash
cd ../Frontend
npm install
npm start
```

The React dev server starts on http://localhost:3000 and is proxied to the backend (see `Frontend/package.json`).

Notes:
- The backend also includes a `Pipfile` if you prefer `pipenv`.
- `Frontend/package.json` sets a proxy to `http://127.0.0.1:5000` for API calls.

---

## VS Code (recommended)

1. Open the project folder in VS Code.
2. Open an integrated terminal and run the backend steps in one terminal and the frontend steps in another.

---

## Endpoints (examples)

- Frontend: http://localhost:3000
- Backend API: http://127.0.0.1:5000
- Health check: http://127.0.0.1:5000/api/health

---

## Notes & Ethics

Use this project only with public data and for lawful, ethical research. Do not attempt to access private accounts, bypass authentication, or otherwise violate platform terms of service.

If you'd like, I can also add a short development checklist or startup scripts to simplify running both services concurrently.
