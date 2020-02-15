RED=\033[0;31m
NC=\033[0m

PROJECT_ROOT=$(shell readlink -e "$(dir $(firstword $(MAKEFILE_LIST)))")
SERVICE_SOURCE=${PROJECT_ROOT}/systemd-service/riffbot.service
SERVICE_TARGET_DIR=~/.config/systemd/user
SERVICE_TARGET=${SERVICE_TARGET_DIR}/riffbot.service

install:
	@pip3 install -U wheel
	@pip3 install -U -r requirements.txt

install-dev:
	@pip3 install -U -r requirements-dev.txt

run:
	@python3 src/__main__.py

test:
	@PYTHONPATH=src python3 -m unittest discover -s tests/unit

uml:
	@plantuml -o out diagrams/*.uml

service:
	@test -n "${VENV}" || (echo "${RED}VENV not set, please set it to the path of your virtual environment.${NC}" && /bin/false)
	@readlink -qe "${VENV}" > /dev/null || (echo "${RED}\"${VENV}\" does not exist.${NC}" && /bin/false)
	@mkdir -p ${SERVICE_TARGET_DIR}
	@cp ${SERVICE_SOURCE} ${SERVICE_TARGET}
	@sed -i "s/{VENV_PATH}/$(shell readlink -e "${VENV}" | sed 's_/_\\/_g')/g" ${SERVICE_TARGET}
	@sed -i "s/{PROJECT_ROOT}/$(shell echo ${PROJECT_ROOT} | sed 's_/_\\/_g')/g" ${SERVICE_TARGET}

help:
	@echo "Usage:"
	@echo "  help         Print this help"
	@echo "  install      Install the required python3 packages"
	@echo "               (recommended: use a virtual environment)"
	@echo "  install-dev  Install the development dependencies"
	@echo "               (Python Language Server)"
	@echo "  run          Initialize and run the bot"
	@echo "  test         Run all tests in the tests/ directory"
	@echo "  uml          Generate UML diagrams with PlantUML"
	@echo "  service      Install systemd user service"

.PHONY: install install-dev run test uml service help
