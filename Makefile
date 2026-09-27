PYTHON ?= /usr/bin/python
LATEXMK ?= latexmk

GRAMMAR_SOURCES := $(wildcard grammar/*.tex)
STYLE_SOURCES := $(wildcard style/*)
INTRODUCTION_SOURCES := $(wildcard verbs/introductions/*.tex)
GENERATOR_SOURCES := scripts/generate_verbs.py scripts/verb_data.py

.PHONY: all generate check test clean

all: GermanBook.pdf

generate: verbs/verb-list.tex

verbs/verb-list.tex: verbs/verbs.yaml $(GENERATOR_SOURCES) $(INTRODUCTION_SOURCES)
	$(PYTHON) scripts/generate_verbs.py

GermanBook.pdf: main.tex verbs/verb-list.tex $(GRAMMAR_SOURCES) $(STYLE_SOURCES)
	$(LATEXMK) -pdf -interaction=nonstopmode -halt-on-error -jobname=GermanBook main.tex

check:
	$(PYTHON) scripts/generate_verbs.py --check

test: check
	$(PYTHON) -m unittest discover -s tests -v

clean:
	$(LATEXMK) -C -jobname=GermanBook main.tex
