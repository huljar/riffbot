RED=\033[0;31m
NC=\033[0m

PROJECT_ROOT=$(shell readlink -e "$(dir $(firstword $(MAKEFILE_LIST)))")
SERVICE_SOURCE=${PROJECT_ROOT}/systemd-service/riffbot.service.template
SERVICE_TARGET_USER=~/.config/systemd/user/riffbot.service
SERVICE_TARGET_SYSTEM=/etc/systemd/system/riffbot.service
EUID=$(shell id -u)

install:
	@pip3 install -U wheel
	@pip3 install -U -r requirements.txt

install-dev:
	@pip3 install -U -r requirements-dev.txt

run:
	@python3 -m riffbot

run-debug:
	@python3 -m riffbot -l DEBUG

test:
	@PYTHONPATH=riffbot python3 -m unittest discover -s tests/unit

typecheck:
	@pyre --preserve-pythonpath check

uml:
	@plantuml -o out diagrams/*.uml

service:
	@test -n "${VENV}" || (echo "${RED}VENV not set, please set it to the path of your virtual environment.${NC}" && /bin/false)
	@readlink -qe "${VENV}" > /dev/null || (echo "${RED}\"${VENV}\" does not exist.${NC}" && /bin/false)
ifeq (${EUID},0)
	@test -n "${XUSER}" || (echo "${RED}XUSER not set, please set it to the name of the user Riffbot shall run as.${NC}" && /bin/false)
	@mkdir -p $(dir ${SERVICE_TARGET_SYSTEM})
	@cp ${SERVICE_SOURCE} ${SERVICE_TARGET_SYSTEM}
	@chown root:root ${SERVICE_TARGET_SYSTEM}
	@chmod 644 ${SERVICE_TARGET_SYSTEM}
	@sed -i "s/{VENV_PATH}/$(shell readlink -e "${VENV}" | sed 's_/_\\/_g')/g" ${SERVICE_TARGET_SYSTEM}
	@sed -i "s/{PROJECT_ROOT}/$(shell echo ${PROJECT_ROOT} | sed 's_/_\\/_g')/g" ${SERVICE_TARGET_SYSTEM}
	@sed -i "s/{USER_DIRECTIVE}/User=${XUSER}\\n/g" ${SERVICE_TARGET_SYSTEM}
	@echo "Successfully installed system service to ${SERVICE_TARGET_SYSTEM}"
else
	@mkdir -p $(dir ${SERVICE_TARGET_USER})
	@cp ${SERVICE_SOURCE} ${SERVICE_TARGET_USER}
	@chown ${EUID}:${EUID} ${SERVICE_TARGET_USER}
	@chmod 644 ${SERVICE_TARGET_USER}
	@sed -i "s/{VENV_PATH}/$(shell readlink -e "${VENV}" | sed 's_/_\\/_g')/g" ${SERVICE_TARGET_USER}
	@sed -i "s/{PROJECT_ROOT}/$(shell echo ${PROJECT_ROOT} | sed 's_/_\\/_g')/g" ${SERVICE_TARGET_USER}
	@sed -i "s/{USER_DIRECTIVE}//g" ${SERVICE_TARGET_USER}
	@echo "Successfully installed user service to ${SERVICE_TARGET_USER}"
endif

help:
	@echo "Usage:"
	@echo "  help         Print this help"
	@echo "  install      Install the required python3 packages"
	@echo "               (recommended: use a virtual environment)"
	@echo "  install-dev  Install the development dependencies"
	@echo "               (e.g. Python Language Server)"
	@echo "  run          Initialize and run the bot"
	@echo "  run-debug    Run the bot with debug output"
	@echo "  test         Run all tests in the tests/ directory"
	@echo "  typecheck    Run pyre, the static type checker (may take a long time)"
	@echo "  uml          Generate UML diagrams with PlantUML"
	@echo "  service      Install systemd service for Riffbot"
	@echo "                 as normal user: install to $(dir ${SERVICE_TARGET_USER})"
	@echo "                 as root: install to $(dir ${SERVICE_TARGET_SYSTEM})"

.PHONY: install install-dev run run-debug test typecheck uml service help
