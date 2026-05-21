# S.U.K.U API — use port 8080 if 8000 gives WinError 10013
$port = if ($args[0]) { [int]$args[0] } else { 8080 }
& "$PSScriptRoot\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port $port
