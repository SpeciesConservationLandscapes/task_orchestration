# task_orchestration

Manage running task pipeline



## Usage

usage: task.py [-h] [-p PIPELINE] [-f PIPELINE_FILE] [--raiseonfail]

optional arguments:
  -h, --help            show this help message and exit
  -p PIPELINE, --pipeline PIPELINE
  -f PIPELINE_FILE, --pipeline_file PIPELINE_FILE
  --raiseonfail         Stop running pipeline if any task has an exception.


## Pipeline Schema

```
[
    [
        {
            "image": string,
            "cmd": string,
            "args": object
        }
    ]
]
```