.PHONY: test phase1a-smoke setup-hooks check-identity

test:
	python3 -m pytest tests/ -q

phase1a-smoke:
	python3 -m pytest tests/test_phase1a_smoke.py -q

setup-hooks:
	mkdir -p .githooks
	chmod +x .githooks/commit-msg scripts/check_commit_identity.sh
	git config core.hooksPath .githooks
	@echo "Installed repo hooks via core.hooksPath=.githooks"

check-identity:
	bash scripts/check_commit_identity.sh
