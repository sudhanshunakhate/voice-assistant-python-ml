# S.U.K.U — setup, install, and run

**Smart Universal Knowledge Utility** — local voice assistant with FastAPI backend and React (Vite) frontend.

---

## 1. What you need installed

| Tool | Notes |
|------|--------|
| **Python** | 3.10+ recommended (3.11+ ideal). Must be on `PATH` as `python` / `python3`. |
| **Node.js** | 18+ LTS. Includes `npm`. |
| **Git** (optional) | To clone the repository. |

Verify:

```bash
python --version
# or: python3 --version

node --version
npm --version
```

---

## 2. Get the project

**With Git:**

```bash
git clone <your-repo-url> alexa
cd alexa
```

**Without Git:** download the ZIP, extract it, and open a terminal in the project folder (the one that contains `backend/` and `frontend/`).

---

## 3. Install all dependencies (one command)

This installs **Python packages** into `backend/.venv` and **npm packages** into `frontend/node_modules`.

### Windows (PowerShell)

From the project root:

```powershell
powershell -ExecutionPolicy Bypass -File .\install-dependencies.ps1
```

If you prefer step-by-step instead of the script, see **section 7**.

### macOS / Linux

```bash
chmod +x install-dependencies.sh
./install-dependencies.sh
```

### What gets installed

- **Backend:** packages listed in `backend/requirements.txt` (also referenced from root `requirements.txt`).
- **Frontend:** packages listed in `frontend/package.json` (React, Vite, TypeScript, etc.).

---

## 4. Optional: environment variables (`.env`)

Create **`backend/.env`** if you want AI search or cloud features (all optional for basic local use):

```env
# Optional — Google Gemini (AI skill)
GEMINI_API_KEY=

# Optional — OpenAI (if your code path uses it)
OPENAI_API_KEY=

# Optional — Google Programmable Search (Search page)
GOOGLE_SEARCH_API_KEY=
GOOGLE_CSE_ID=
```

The app runs without these; skills that need keys will show a clear error or fallback.

---

## 5. Run the backend (API)

The Vite dev server proxies `/api` to **`http://127.0.0.1:8080`**, so the API should listen on **port 8080**.

### Windows (PowerShell)

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

### macOS / Linux

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

Leave this terminal open. You should see Uvicorn logs.

**Quick check (new terminal):**

```bash
curl -s http://127.0.0.1:8080/api/health
```

---

## 6. Run the frontend (UI)

Open a **second** terminal at the **project root**:

```bash
cd frontend
npm run dev
```

Open a browser: **http://localhost:5173**

The UI talks to the API through the Vite proxy (`/api` → `127.0.0.1:8080`). Keep **both** backend and frontend running.

---

## 7. Manual install (if you skip the install script)

### Backend

```bash
cd backend
python -m venv .venv
```

Activate the venv, then:

**Windows:** `.\.venv\Scripts\Activate.ps1`  
**Unix:** `source .venv/bin/activate`

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Or from **repo root**:

```bash
pip install -r requirements.txt
```
(Still activate `backend/.venv` first, or use `backend/.venv/Scripts/pip` / `backend/.venv/bin/pip` explicitly.)

### Frontend

```bash
cd frontend
npm install
```

---

## 8. Example API requests (“queries”)

With the backend running on **8080**, you can test with **curl** or **Invoke-WebRequest**.

### Health

```bash
curl -s http://127.0.0.1:8080/api/health
```

### Send a command (JSON)

Skip wake-word check (same as dashboard “Skip wake word”):

```bash
curl -s -X POST http://127.0.0.1:8080/api/assistant/command ^
  -H "Content-Type: application/json" ^
  -d "{\"text\": \"what time is it\", \"skip_wake_check\": true}"
```

**PowerShell** (single line):

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/assistant/command" -Method Post -ContentType "application/json" -Body '{"text":"what time is it","skip_wake_check":true}'
```

### List conversation history

```bash
curl -s http://127.0.0.1:8080/api/history
```

### List reminders

```bash
curl -s http://127.0.0.1:8080/api/reminders
```

### Settings (GET)

```bash
curl -s http://127.0.0.1:8080/api/settings
```

---

## 9. Production-style build (frontend only)

```bash
cd frontend
npm run build
```

Serve the `frontend/dist` folder with any static host, and configure that host to proxy `/api` to your backend, or set the frontend’s API base URL to the real backend origin. For local development, **`npm run dev` + uvicorn** is enough.

---

## 10. Troubleshooting

| Issue | What to try |
|--------|-------------|
| **Port 8080 in use** | Stop the other app, or run uvicorn with another port and update `frontend/vite.config.ts` proxy `target` to match. |
| **`python` not found** | On Windows, install Python from python.org and tick “Add to PATH”, or use `py -3` instead of `python` in the install script (edit `install-dependencies.ps1` if needed). |
| **CORS errors** | Ensure backend `cors_origins` in `backend/app/config.py` includes `http://localhost:5173` (default). |
| **npm errors** | Delete `frontend/node_modules` and `frontend/package-lock.json`, then `npm install` again. |

---

## File reference

| File | Purpose |
|------|--------|
| `install-dependencies.ps1` | One-shot install (Windows). |
| `install-dependencies.sh` | One-shot install (macOS/Linux). |
| `requirements.txt` | Root pip file; includes `backend/requirements.txt`. |
| `backend/requirements.txt` | Authoritative Python dependency list. |
| `frontend/package.json` | Node dependencies and `npm run dev` / `build` scripts. |
