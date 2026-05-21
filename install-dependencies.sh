<<<<<<< HEAD
#!/usr/bin/env bash
# Install all project dependencies: Python (backend) + npm (frontend).
#   chmod +x install-dependencies.sh && ./install-dependencies.sh

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "== S.U.K.U dependency install =="
echo "Root: $ROOT"

BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"

if [[ ! -d "$BACKEND" ]]; then echo "error: backend not found" >&2; exit 1; fi
if [[ ! -d "$FRONTEND" ]]; then echo "error: frontend not found" >&2; exit 1; fi

echo ""
echo "Python venv + pip..."
cd "$BACKEND"
if [[ ! -d .venv ]]; then python3 -m venv .venv; fi
# shellcheck source=/dev/null
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "Backend OK."

echo ""
echo "npm install..."
cd "$FRONTEND"
npm install
echo "Frontend OK."

echo ""
echo "Done. Read SETUP_AND_RUN.md to start servers."
=======
#!/usr/bin/env bash
# Install all project dependencies: Python (backend) + npm (frontend).
#   chmod +x install-dependencies.sh && ./install-dependencies.sh

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "== S.U.K.U dependency install =="
echo "Root: $ROOT"

BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"

if [[ ! -d "$BACKEND" ]]; then echo "error: backend not found" >&2; exit 1; fi
if [[ ! -d "$FRONTEND" ]]; then echo "error: frontend not found" >&2; exit 1; fi

echo ""
echo "Python venv + pip..."
cd "$BACKEND"
if [[ ! -d .venv ]]; then python3 -m venv .venv; fi
# shellcheck source=/dev/null
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "Backend OK."

echo ""
echo "npm install..."
cd "$FRONTEND"
npm install
echo "Frontend OK."

echo ""
echo "Done. Read SETUP_AND_RUN.md to start servers."
>>>>>>> b346c3a8e19d05c455a7bc7287e9f775bcd3a589
