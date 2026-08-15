"""Standalone helper to bcrypt-hash a password without needing bcrypt on the
host. Run inside the built backend image:

    docker compose run --rm backend python -m app.gen_hash
"""

import getpass

import bcrypt


def main() -> None:
    password = getpass.getpass("Admin password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Passwords did not match.")
        raise SystemExit(1)
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    # docker compose interpolates `$...` in .env values, so a raw hash gets
    # silently mangled on `docker compose up` — double every `$` to `$$` so
    # compose hands the container back the literal hash. generate_secrets.sh
    # does this automatically; only matters if you're pasting by hand.
    escaped = hashed.replace("$", "$$")
    print("\nPaste this into .env as ADMIN_PASSWORD_HASH (already escaped for docker compose):\n")
    print(escaped)


if __name__ == "__main__":
    main()
