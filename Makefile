RUNNER=uv run src/ohmyscrapper/__init__.py
.PHONY: clean, ai, start

clean:
	rm db/local.db

load:
	$(RUNNER) load

scrap-urls:
	$(RUNNER) scrap-urls --recursive --ignore-type

scrap-urls-only-parents:
	$(RUNNER) scrap-urls --recursive --ignore-type --only-parents

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
	uv build
