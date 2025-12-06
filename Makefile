clean:
	rm db/local.db

load:
	python3 main.py load-txt

full-start:
	pip install -r requirements.txt
	python3 main.py load-txt
	python3 main.py scrap-urls --recursive --ignore-type

start-only-parents:
	python3 main.py load-txt
	python3 main.py scrap-urls --recursive --ignore-type --only-parents

start:
	python3 main.py load-txt
	python3 main.py scrap-urls --recursive --ignore-type

continue:
	python3 main.py scrap-urls --recursive --ignore-type

continue-only-parents:
	python3 main.py scrap-urls --recursive --ignore-type --only-parents

export:
	python3 main.py export
	python3 main.py export --file=output/urls-simplified.csv --simplify
	python3 main.py report

ai:
	python main.py process-with-ai

seed:
	python main.py seed

merge_dbs:
	python main.py merge_dbs
