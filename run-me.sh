#!/usr/bin/env bash

set -e

BASEDIR=$(realpath $(dirname $0))
cd $BASEDIR
source ./.venv/bin/activate && python3 bot.py

