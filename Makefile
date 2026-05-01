.PHONY: test phase1a-smoke

test:
	python3 -m pytest tests/ -q

phase1a-smoke:
	python3 -m pytest tests/test_phase1a_smoke.py -q
