#!/usr/bin/env bash
# Optional system packages for Ubuntu/Debian (requires sudo).
set -euo pipefail
sudo apt-get update -qq
sudo apt-get install -y -qq python3.12-venv python3-pip python3-dev
# LaTeX is optional until P5:
# sudo apt-get install -y -qq texlive-latex-base texlive-latex-recommended \
#   texlive-latex-extra texlive-fonts-recommended latexmk texlive-bibtex-extra
