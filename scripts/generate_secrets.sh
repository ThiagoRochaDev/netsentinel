#!/usr/bin/env bash
# Generates SECRET_KEY and ADMIN_PASSWORD_HASH into .env.
# Run this once after copying .env.example to .env, before first `docker compose up`.
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "No .env found — copying from .env.example first."
  cp .env.example .env
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required to generate secrets." >&2
  exit 1
fi

SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

echo "Choose the initial admin password for the NetSentinel dashboard."
read -r -s -p "Admin password: " ADMIN_PASSWORD
echo
read -r -s -p "Confirm password: " ADMIN_PASSWORD_CONFIRM
echo

if [ "$ADMIN_PASSWORD" != "$ADMIN_PASSWORD_CONFIRM" ]; then
  echo "Passwords did not match. Aborting." >&2
  exit 1
fi

ADMIN_PASSWORD_HASH=$(python3 - "$ADMIN_PASSWORD" <<'PYEOF'
import sys
try:
    import bcrypt
except ImportError:
    sys.stderr.write(
        "The 'bcrypt' python package is not installed on this host.\n"
        "That's fine — it's a dependency of the backend container, not the host.\n"
        "Re-run this script with: docker compose run --rm backend python -m app.gen_hash\n"
    )
    sys.exit(2)
pw = sys.argv[1].encode("utf-8")
print(bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8"))
PYEOF
)
status=$?
if [ $status -eq 2 ]; then
  exit 1
fi

# docker compose interpolates `$...` in .env values (it's read both as the
# project's own interpolation source AND passed through via `env_file:`), so
# a raw bcrypt hash like `$2b$12$...` gets silently mangled/truncated on
# `docker compose up`. Doubling each `$` to `$$` here is what makes compose
# hand the container back the literal, correct hash.
ADMIN_PASSWORD_HASH_ESCAPED=${ADMIN_PASSWORD_HASH//\$/\$\$}

# Replace placeholders in .env (portable sed -i for macOS/Linux)
tmp=$(mktemp)
sed \
  -e "s#^SECRET_KEY=.*#SECRET_KEY=${SECRET_KEY}#" \
  -e "s#^ADMIN_PASSWORD_HASH=.*#ADMIN_PASSWORD_HASH=${ADMIN_PASSWORD_HASH_ESCAPED}#" \
  .env > "$tmp"
mv "$tmp" .env

echo "Done. SECRET_KEY and ADMIN_PASSWORD_HASH written to .env."
