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
│       ├── CasePage.jsx
│       ├── ThemeButton.jsx
│       └── UI.jsx
├── public/
│   └── index.html
└── package.json
```

---

## Prerequisites

- **Python 3.9+** — https://python.org/downloads
- **Node.js 18+** — https://nodejs.org

---

## Setup & Run

### ── CMD (Windows Command Prompt) ──────────────────────

```cmd
REM 1. Open CMD, navigate to the project root
cd path\to\soko-osint

REM 2. Set up and run the backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py

REM 3. Open a SECOND CMD window, go back to root
cd path\to\soko-osint
npm install
npm start
```

### ── PowerShell (Windows) ──────────────────────────────

```powershell
# 1. Navigate to project root
cd C:\path\to\soko-osint

# 2. Backend - run in THIS window
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py

# 3. Frontend - open a NEW PowerShell window
cd C:\path\to\soko-osint
npm install
npm start
```

> **PowerShell Execution Policy Fix** (if you get an error on Activate.ps1):
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### ── VS Code (Recommended) ────────────────────────────

1. Open the `soko-osint` folder in VS Code (`File → Open Folder`)
2. Open the **integrated terminal** (`Ctrl+`` ` ``)
3. **Terminal 1 — Backend:**
   ```bash
   cd backend
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Mac/Linux:
   source venv/bin/activate

   pip install -r requirements.txt
   python app.py
   ```
4. Click the **+** icon in the terminal panel to open **Terminal 2 — Frontend:**
   ```bash
   npm install
   npm start
   ```
5. Browser will auto-open at **http://localhost:3000**

---

## URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://127.0.0.1:5000 |
| Health check | http://127.0.0.1:5000/api/health |

---

## Features

- **Username investigation** across 10 platforms simultaneously
- **Behavioral analysis** with risk scoring (LOW / MEDIUM / HIGH)
- **Keyword detection** for conflict-related terms
- **Platform presence** map with profile links and avatars
- **Reddit & GitHub** deep data via public APIs
- **4 themes**: Dark Intel, Light Ops, Red Alert, Ghost Protocol
- **Draggable theme switcher** — drag anywhere on screen
- **Persistent theme** across page reloads
- **Responsive** layout (desktop + mobile)

---

## Legal & Ethics

This platform uses **public data only**. No private APIs, no authentication bypassing.
All findings are for educational and research purposes.
Confirmed threats should be handed over to appropriate authorities.
