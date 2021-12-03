run:
	python src/task.py --pipeline_file="tests/pipeline.json" --raiseonfail

run_error:
	python src/task.py --pipeline_file="tests/pipeline_w_error.json" --raiseonfail

run_error_skip:
	python src/task.py --pipeline_file="tests/pipeline_w_error.json"

cleanup:
	isort `pwd`/src/*.py
	black `pwd`/src/*.py
	flake8 `pwd`/src/*.py
	mypy `pwd`/src/*.py