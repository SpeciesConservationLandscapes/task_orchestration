VM_IMAGE=scl/orchestration-vm

run:
	python src/task.py --pipeline_file="tests/pipeline.json" --exit_on_error

run_error:
	python src/task.py --pipeline_file="tests/pipeline_w_error.json" --exit_on_error

build_shell:
	docker build -t $(VM_IMAGE) .

shell:
	docker run -w /app --env-file=.env -v `pwd`/vm:/app --rm -it --entrypoint bash $(VM_IMAGE)

cleanup:
	isort `pwd`/src/*.py
	black `pwd`/src/*.py
	flake8 `pwd`/src/*.py
	mypy `pwd`/src/*.py