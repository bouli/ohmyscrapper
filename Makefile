clean:
	rm db/local.db

load:
	python3 main.py load-txt

start:
	pip install -r requirements.txt
	python3 main.py load-txt
	python3 main.py scrap-urls --recursive --ignore-type

continue:
	python3 main.py scrap-urls --recursive --ignore-type

export:
	python3 main.py export
