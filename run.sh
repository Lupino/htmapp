#!/usr/bin/env bash

ROOT=$(cd "$(dirname "$0")" || exit; pwd)
INSTALL_LOCK=${ROOT}/.installed
VENV_PATH=${ROOT}/venv

cd "${ROOT}" || exit

PYTHON=python3.8
${PYTHON} -c 'print()' >/dev/null 2>/dev/null || PYTHON=python3
${PYTHON} -c 'print()' >/dev/null 2>/dev/null || PYTHON=python

install_required() {
    ${PYTHON} -m pip install -U -r "${ROOT}/requirements.txt"
    shasum -a 256 "${ROOT}/requirements.txt" > "${INSTALL_LOCK}"
}

if [ -z "${SYSTEM_PYTHON}" ]; then
    [ -d "${VENV_PATH}" ] || ${PYTHON} -m venv "${VENV_PATH}"
    # shellcheck source=/dev/null
    source "${VENV_PATH}/bin/activate"
fi

if [ -e "${INSTALL_LOCK}" ]; then
    shasum -a 256 -c "${INSTALL_LOCK}" >/dev/null 2>/dev/null || install_required
else
    install_required
fi

VALIDCOMMAND=(
    yapf
    flake8
    pip
    pip3
    python
)

for cmd in "${VALIDCOMMAND[@]}"; do
    if [ "$1" == "${cmd}" ]; then
        "$@"
        exit 0
    fi
done

if [ -z "$1" ]; then
    ${PYTHON}
elif [ "$1" == "cli" ]; then
    shift
    ${PYTHON} run.py htmapp/cli.py "$@"
else
    ${PYTHON} run.py "$@"
fi
