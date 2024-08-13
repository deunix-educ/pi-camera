#!/bin/bash
rm -rf .venv
python3 -m venv .venv
source $(pwd)/.venv/bin/activate
echo "Activate virtual environment .venv"
echo "PIP path: $(command -v pip)"

pip install -U pip wheel setuptools
pip install -r $1


