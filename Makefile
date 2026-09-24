# Applied NLP book — local workflow
# Requires: quarto (https://quarto.org), python deps from requirements.txt,
# node (for check-ojs)

.PHONY: preview preview-tr render serve glossary glossary-check check-links check-glossary-use check-ojs check-numbering check-themes check-tables check-markdown renumber readability check clean

## Rebuild the glossary tables from en/appendices/glossary.csv
glossary:
	python3 scripts/build-glossary.py

## Fail if the glossary tables are out of sync with the CSV
glossary-check:
	python3 scripts/build-glossary.py --check

## Fail on dead @sec- refs, unknown citations, or stale hard-coded chapter links
check-links:
	python3 scripts/check-links.py

## Fail if a margin term-gloss names a term the glossary does not carry
check-glossary-use:
	python3 scripts/check-glossary-use.py

## Fail on an ojs widget that does not parse, or two cells sharing a name
check-ojs:
	node scripts/check-ojs.mjs

## Fail if a chapter's NN- prefix disagrees with its position in _quarto.yml
check-numbering:
	python3 scripts/renumber-chapters.py --check

## Fail if the editions' theme stylesheets have drifted apart
check-themes:
	python3 scripts/check-themes.py

check-tables:
	python3 scripts/check-tables.py

## Fail on a reflowed line pandoc will read as a list marker
check-markdown:
	python3 scripts/check-markdown.py

## Renumber chapters to match _quarto.yml, fixing links in both editions
renumber:
	python3 scripts/renumber-chapters.py

## Report prose difficulty per chapter (advisory — never fails the build)
readability:
	python3 scripts/check-readability.py

## Every fast check CI runs, without the full render.
## Numbering runs before links: bad numbers cause dead links, so reporting
## the root cause first saves chasing the symptom.
check: glossary-check check-numbering check-links check-glossary-use check-ojs check-themes check-tables check-markdown

## Live-preview the English edition (auto-reloads on save)
preview:
	quarto preview en

## Live-preview the Turkish edition
preview-tr:
	quarto preview tr

## Render both editions and assemble the combined site into ./site
render:
	quarto render en
	quarto render tr
	rm -rf site && mkdir -p site
	cp -r en/_book site/en
	cp -r tr/_book site/tr
	cp index.html site/index.html
	@echo "→ combined site in ./site (run 'make serve')"

## Serve the assembled site locally at http://localhost:4200
serve:
	python3 -m http.server 4200 -d site

clean:
	rm -rf en/_book tr/_book site public en/.quarto tr/.quarto
