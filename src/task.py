import argparse
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from posix import environ
from typing import Any, Dict, List, Union

import docker  # type: ignore
from task_base import Task  # type: ignore


logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)


class PipelineError(Exception):
    pass


class OrchestrationTask(Task):
    """

    PIPELINE

    Pipeline schema:
        [
            [task1],
            [task2, task3],
            [task4],
            [task5, task6, task7],
            ...
            [taskN]
        ]

    Task schema:
        {
            "image": <DOCKER IMAGE>,
            "cmd": <COMMAND TO RUN IN DOCKER>,
            "args": <DICT/JSON object of keyword arguments and values>
        }

    Task example:
        {
            "image": "python:slim-buster",
            "cmd": "/usr/local/bin/python",
            "args": {
                "-c": "'import os, time;time.sleep(3);print(os.environ)'"
            }
        }

    """

    pipeline = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.pipeline = self._get_pipeline(kwargs)
        self.exit_on_error = kwargs.get("exit_on_error") or False

    def _get_pipeline(self, kwargs: Dict[str, Any]):
        if kwargs.get("pipeline") is not None:
            pipeline: Union[str, bytes] = kwargs["pipeline"]
        elif kwargs.get("pipeline_file") is not None:
            pipeline_file: Union[str, Path] = kwargs["pipeline_file"]
            with open(pipeline_file, "r") as f:
                pipeline = f.read()
        else:
            raise ValueError("pipeline or pipeline_file required")

        try:
            return json.loads(pipeline)
        except (ValueError, TypeError):
            raise ValueError("Pipeline required")

    def run_pipeline_task(self, pipeline_task: Dict[str, Any]):
        client = docker.from_env()
        cmd = pipeline_task["cmd"]
        args = " ".join(f"{k} {v}" for k, v in pipeline_task["args"].items())

        return client.containers.run(
            image=pipeline_task["image"],
            command=f"{cmd} {args}",
            remove=True,
            environment=os.environ
        )

    def run_task_group(self, task_group: List[dict]):
        futures = []
        with ThreadPoolExecutor(max_workers=len(task_group)) as exc:
            for task in task_group:
                future = exc.submit(self.run_pipeline_task, task)
                futures.append(future)

        has_errors = False
        for future in futures:
            try:
                logging.info(future.result())
            except Exception as err:
                logging.error(err)
                has_errors = True

        return not has_errors or not self.exit_on_error

    def calc(self):
        for task_group in self.pipeline:
            if self.run_task_group(task_group) is False:
                raise PipelineError("Task error")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--pipeline")
    parser.add_argument("-f", "--pipeline_file")
    parser.add_argument(
        "--exit_on_error",
        action="store_true",
        help="Stop running pipeline if any task has an exception.",
    )

    options = parser.parse_args()
    task = OrchestrationTask(**vars(options))
    task.run()
