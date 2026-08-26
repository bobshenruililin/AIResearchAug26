# Paper

```bash
# from repo root, after make setup
PYTHONPATH=src .venv/bin/python scripts/stats_and_summary.py
PYTHONPATH=src .venv/bin/python scripts/make_paper_numbers.py
PYTHONPATH=src .venv/bin/python figures/make_all.py
sudo apt-get install -y texlive-latex-base texlive-latex-recommended \
  texlive-latex-extra texlive-fonts-recommended texlive-bibtex-extra latexmk
cd paper && latexmk -pdf main.tex
```

`numbers.tex` is generated; do not edit it.
`verified.bib` is generated from API verification; do not add unverified keys.
