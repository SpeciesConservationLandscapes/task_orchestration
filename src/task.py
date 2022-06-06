import argparse
import base64
import json
import logging
import os
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Union

import docker  # type: ignore
from task_base import Task  # type: ignore

try:
    import googleapiclient.discovery
    from googleapiclient.errors import HttpError
except Exception as err:
    print(err)


LOCAL_ENV = "local"
GCP_ENV = "gcp"  # Google Cloud Platform
ENVIRONMENTS = [GCP_ENV, LOCAL_ENV,]


logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)


def _get_google_secret(secret_key):
    project_id = os.environ.get("PROJECT_ID")

    if project_id is None:
        raise ValueError(f"{GCP_ENV} requires 'PROJECT_ID' environment variable to be set")

    secrets_manager = googleapiclient.discovery.build("secretmanager", "v1")
    secret_versions = secrets_manager.projects().secrets().versions()
    try:
        resp = secret_versions.access(name=f"projects/{project_id}/secrets/{secret_key}/versions/latest").execute()
    except HttpError as err:
        err_json = json.loads(err.content.decode("utf-8"))
        raise ValueError(f"[{err_json['code']}] {err['message']}") from err

    payload = resp.get("payload") or {}
    val = payload.get("data")
    return base64.b64decode(val).decode("utf-8")


def _get_local_secret(secret_key):
    return os.environ[secret_key]


def get_secret(env, secret_key):
    if env == LOCAL_ENV:
        return _get_local_secret(secret_key)
    elif env == GCP_ENV:
        return _get_google_secret(secret_key)
    
    raise ValueError(f"'{env}': Invalid enviroment")


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
            "volumes": <DICT/JSON object of host paths and container paths>
            "env_args": <DICT/JSON environment variables name and aliased name>
        }

    Task example:
        {
            "image": "python:slim-buster",
            "cmd": "/usr/local/bin/python",
            "args": {
                "-c": "'import os, time;time.sleep(3);print(os.environ)'"
            },
            "volumes": {
                "$PWD/src": "/my_code",
                "/home/user1/data": "/data"
            },
            "env_vars": {
                "PROJECT_ID": "PROJECT"
            }
        }

    """

    pipeline = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.environment = kwargs["environment"]
        self.pipeline = self._get_pipeline(kwargs)
        self.raiseonfail = kwargs.get("raiseonfail") or False

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
        except (ValueError, TypeError) as err:
            raise ValueError("Pipeline required") from err

    def _get_dict(self, d, key):
        val = d.get(key)
        return val if isinstance(val, dict) else {}

    def _swap_variables(self, path):
        if "$PWD" in path:
            pwd = os.getcwd()
            path = path.replace("$PWD", pwd)
        
        if "$HOME" in path:
            home = os.path.expanduser('~')
            path = path.replace("$HOME", home)

        return path

    def _prepare_volumes(self, volumes):
        docker_volumes = {}
        for host_path, container_path in volumes.items():
            host_path = self._swap_variables(host_path)
            if not os.path.exists(host_path):
                os.makedirs(host_path)
            elif os.path.isdir(host_path) is False:
                raise ValueError("Host path is not a directory")
            
            docker_volumes[host_path] = {"bind": container_path, "mode": "rw"}
        
        return docker_volumes

    def _get_environment_variables(self, env_vars):
        env_var_sets = []
        for env_var, container_env_var in env_vars.items():
            secret = get_secret(self.environment, env_var)
            env_var_sets.append(f"{container_env_var}={secret}")
        return env_var_sets

    def run_pipeline_task(self, pipeline_task: Dict[str, Any]):
        client = docker.from_env()
        cmd = pipeline_task["cmd"]
        args = " ".join(f"{k} {v}" for k, v in self._get_dict(pipeline_task, "args").items())
        volumes = self._prepare_volumes(self._get_dict(pipeline_task, "volumes"))
        env_vars = self._get_environment_variables(self._get_dict(pipeline_task, "env_vars"))

        log_stream = client.containers.run(
            image=pipeline_task["image"],
            command=f"{cmd} {args}",
            remove=True,
            stdout=True,
            stream=True,
            environment=env_vars,
            volumes=volumes
        )

        for log in log_stream:
            logging.info(log)

        return True

    def run_task_group(self, task_group: List[dict]):
        futures = []
        with ThreadPoolExecutor(max_workers=len(task_group)) as exc:
            for task in task_group:
                future = exc.submit(self.run_pipeline_task, task)
                futures.append(future)

        has_errors = False
        exceptions = []
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as err:
                logging.error(err)
                exceptions.append(err)
                has_errors = True

        return not has_errors or not self.raiseonfail, exceptions

    def calc(self):
        for task_group in self.pipeline:
            result, exceptions = self.run_task_group(task_group)
            if result is False:
                msg = "\n".join(str(e) for e in exceptions)
                raise PipelineError(f"Task error:\n {msg}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--pipeline")
    parser.add_argument("-f", "--pipeline_file")
    parser.add_argument("-e", "--environment", choices=ENVIRONMENTS, default=GCP_ENV)
    parser.add_argument(
        "--raiseonfail",
        action="store_true",
        help="Stop running pipeline if any task has an exception.",
    )

    options = parser.parse_args()
    task = OrchestrationTask(**vars(options))
    task.run()
