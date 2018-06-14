#!/bin/bash

if ! command -v python3 &>/dev/null; then
    echo "python3 not found - is it installed and in your path?"
    exit 1
fi

if ! command -v pip3 &>/dev/null; then
    echo "pip3 not found - is it installed and in your path?"
    exit 1
fi

if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "python3 virtual environment NOT detected."
    echo "We recommend you install this software in a python3 virtual environment, e.g.:"
    echo -e "\t> python3 -m venv ~/.virtualenvs/dashit"
    echo -e "\t> source ~/.virtualenvs/dashit/bin/activate"
    echo -e "\t(dashit)> make install"
    read -p "Install DASHit without a virtual environment [Y/N]? " yn
    case $yn in
        [Yy]* ) exit 0;;
        [Nn]* ) exit 1;;
        * ) echo "Please answer Y or N.";;
    esac
else
    echo "Installing DASHit in the current virtual environment $VIRTUAL_ENV"
fi
