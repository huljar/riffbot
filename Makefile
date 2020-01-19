install:
	@pip3 install -U -r requirements.txt

run:
	@python3 src/__main__.py

help:
	@echo "Usage:"
	@echo "  help     Print this help"
	@echo "  install  Install the required python3 packages"
	@echo "           (recommended: use a virtual environment)"
	@echo "  run      Initialize and run the bot"

.PHONY: install run help
