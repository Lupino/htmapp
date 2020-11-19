#!/usr/bin/env bash

ROOT=$(cd $(dirname $0); pwd)
INSTALL_LOCK=${ROOT}/.installed
VENV_PATH=${ROOT}/venv

install_required() {
    pip install -U -r requirements.txt
    shasum -a 256 requirements.txt > ${INSTALL_LOCK}
}


PYTHON=python3.8
${PYTHON} -c 'print()' >/dev/null 2>/dev/null || PYTHON=python3
${PYTHON} -c 'print()' >/dev/null 2>/dev/null || PYTHON=python

[ -d ${VENV_PATH} ] || ${PYTHON} -m venv ${VENV_PATH}

source ${VENV_PATH}/bin/activate

if [ -e ${INSTALL_LOCK} ]; then
    shasum -a 256 -c ${INSTALL_LOCK} >/dev/null 2>/dev/null || install_required
else
    install_required
fi

if [ "$1" == "yapf" ]; then
    $@
elif [ "$1" == "flake8" ]; then
    $@
elif [ "$1" == "cli" ]; then
    shift
    ${PYTHON} script.py htmapp/cli.py $@
else
    ${PYTHON} script.py $@
fi
