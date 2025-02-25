#!/usr/bin/env bash
BASEDIR=$(realpath $(dirname $0))
cd $BASEDIR
python3 -m venv ./.venv
source ./.venv/bin/activate && python3 -m pip install --upgrade pip && python3 -m pip install -r requirements.txt
