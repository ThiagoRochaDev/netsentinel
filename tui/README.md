# NetSentinel TUI

Terminal dashboard, same API as the web frontend. Works locally or over SSH.

```bash
cd tui
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
NETSENTINEL_API_URL=http://localhost:8000 netsentinel-tui
```

First run asks for username/password and stores the session cookie at
`~/.config/netsentinel/tui_session_cookie` (mode 600). Delete that file to
log out.
