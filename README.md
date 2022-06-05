# task_orchestration

Manage running task pipeline. For more information see 
[gcp_pipeline_devops](https://github.com/SpeciesConservationLandscapes/gcp-pipeline-devops).

## Usage

usage: task.py [-h] [-p PIPELINE] [-f PIPELINE_FILE] [-e {gcp,local}] [--raiseonfail]

options:
  -h, --help            show this help message and exit
  -p PIPELINE, --pipeline PIPELINE
  -f PIPELINE_FILE, --pipeline_file PIPELINE_FILE
  -e {gcp,local}, --environment {gcp,local}
  --raiseonfail         Stop running pipeline if any task has an exception.


## Environment Variables

Need to set the following environment variables in order to fetch secrets from GCP secrets manager:

```
PROJECT_ID=<PROJECT ID>
# if IAM role isn't setup up
GOOGLE_APPLICATION_CREDENTIALS=<path to service account json file>
```

## Pipeline Schema

```
[
    [
        {
            "image": string,
            "cmd": string,
            "args": object
            "volumes": object
            "env_vars": object
        }
    ]
]
```

**Note:**

* For `volumes` definition the host path can use use the variables `$PWD` (current directory) or `$HOME` (users home directory).  Example: `"$PWD/src": "/my_code"`

### License
Copyright (C) 2022 Wildlife Conservation Society
The files in this repository  are part of the task framework for calculating 
Human Impact Index and Species Conservation Landscapes (https://github.com/SpeciesConservationLandscapes) 
and are released under the GPL license:
https://www.gnu.org/licenses/#GPL
See [LICENSE](./LICENSE) for details.
