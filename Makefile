.PHONY: up down logs restart test-scan rules-update

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

restart:
	docker compose restart

# Verifies the whole pipeline end-to-end: Suricata -> eve.json -> backend ->
# alert -> dashboard/TUI, using the local self-test signature (sid:1000001).
test-scan:
	curl -s -A "NetSentinel-Test" http://example.com/ -o /dev/null
	@echo "Sent test request. Check the Alerts page/TUI for 'NETSENTINEL TEST self-check signature'."

rules-update:
	./scripts/setup_suricata_rules.sh
