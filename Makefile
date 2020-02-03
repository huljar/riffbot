install:
	@pip3 install wheel
	@pip3 install -r requirements.txt

install-dev:
	@pip3 install -r requirements-dev.txt

run:
	@python3 src/__main__.py

test:
	@PYTHONPATH=src python3 -m unittest discover -s tests/unit

help:
	@echo "Usage:"
	@echo "  help         Print this help"
	@echo "  install      Install the required python3 packages"
	@echo "               (recommended: use a virtual environment)"
	@echo "  install-dev  Install the development dependencies"
	@echo "               (Python Language Server)"
	@echo "  run          Initialize and run the bot"
	@echo "  test         Run all tests in the tests/ directory"

.PHONY: install install-dev run test help
