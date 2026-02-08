RUNNER=uv run src/ohmyscrapper/__init__.py
.PHONY: clean, ai, start

clean_db:
	rm -f db/local.db

load:
	$(RUNNER) load

scrap-urls:
	$(RUNNER) scrap-urls --recursive --ignore-type

scrap-urls-only-parents:
	$(RUNNER) scrap-urls --recursive --ignore-type --only-parents

load-single-url:
	$(RUNNER) load -input=https://cesarcardoso.cc/

export:
	$(RUNNER) export
	$(RUNNER) export --file=output/urls-simplified.csv --simplify
	$(RUNNER) report

ai:
	$(RUNNER) ai

seed:
	$(RUNNER) seed

merge_dbs:
	$(RUNNER) merge_dbs

start:
	uv sync
	make load
	make scrap-urls
	make ai
	make export

build:
	uv sync
	rm -rf dist
	uv build

prepare:
	rm -rf dist
	rm -rf build
	git log v0.9.4..HEAD --oneline --format="* %h %s (%an)" > CHANGELOG.md
