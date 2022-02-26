# task_orchestration

Manage running task pipeline. For more information see 
[gcp_pipeline_devops](https://github.com/SpeciesConservationLandscapes/gcp-pipeline-devops).

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

### License
Copyright (C) 2022 Wildlife Conservation Society
The files in this repository  are part of the task framework for calculating 
Human Impact Index and Species Conservation Landscapes (https://github.com/SpeciesConservationLandscapes) 
and are released under the GPL license:
https://www.gnu.org/licenses/#GPL
See [LICENSE](./LICENSE) for details.
