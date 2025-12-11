clean:
	rm db/local.db

load:
	uv run main.py load-txt

full-start:
	uv sync
	uv run main.py load-txt
	uv run main.py scrap-urls --recursive --ignore-type

start-only-parents:
	uv run main.py load-txt
	uv run main.py scrap-urls --recursive --ignore-type --only-parents

scrap-urls:
	uv run main.py scrap-urls --recursive --ignore-type

continue:
	uv run main.py scrap-urls --recursive --ignore-type

continue-only-parents:
	uv run main.py scrap-urls --recursive --ignore-type --only-parents

export:
	uv run main.py export
	uv run main.py export --file=output/urls-simplified.csv --simplify
	uv run main.py report

ai:
	python main.py process-with-ai

seed:
	python main.py seed

merge_dbs:
	python main.py merge_dbs

start:
	make load
	make scrap-urls
	make export
