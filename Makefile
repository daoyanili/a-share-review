.PHONY: install test collect help

help:
	@echo "make install        Install Python dependencies"
	@echo "make test           Run tests"
	@echo "make collect DATE=2026-06-02  Collect daily data"

install:
	python3 -m pip install -r requirements.txt

test:
	PYTHONPATH=tools python3 -m unittest discover -s tools/tests

collect:
	@if [ -z "$(DATE)" ]; then echo "Usage: make collect DATE=2026-06-02"; exit 1; fi
	PYTHONPATH=tools python3 tools/collect_daily_data.py "$(DATE)" --out-dir . --allow-insecure

