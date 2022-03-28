#!/bin/bash

set -eux

which pip3
which python3

cd visualizer && pip3 install -r "requirements.txt"

pip install gdown
pip install --upgrade gdown
