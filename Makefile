RUNNER=uv run src/ohmyscrapper/__init__.py
.PHONY: clean, ai, start

clean:
	rm db/local.db

load: db/local.db
	$(RUNNER) load-txt

scrap-urls: db/local.db
	$(RUNNER) scrap-urls --recursive --ignore-type

scrap-urls-only-parents: db/local.db
	$(RUNNER) scrap-urls --recursive --ignore-type --only-parents

export: output/urls.csv output/urls-simplified.csv output/report.csv output/urls.csv-preview.html output/urls-simplified.csv-preview.html output/report.csv-preview.html
	$(RUNNER) export
	$(RUNNER) export --file=output/urls-simplified.csv --simplify
	$(RUNNER) report

ai:
	$(RUNNER) process-with-ai

seed: db/local.db
	$(RUNNER) seed

merge_dbs: db/local.db
	$(RUNNER) merge_dbs

start:
	uv sync
	make load
	make scrap-urls
	make export

build:
	uv build
