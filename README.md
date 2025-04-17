# Survival Estimation Analysis (Kaplan-Meier) Service

## General
[Kaplan-Meier](https://en.wikipedia.org/wiki/Kaplan%E2%80%93Meier_estimator) survival estimation analysis service wrapperd with web API.


## Configuration
To configure the application, change environment variables as required in [commands](https://github.com/dkfz-unite/unite-commands/blob/main/README.md#configuration) web service:
- `UNITE_COMMAND` - command to run the analysis package (`python`).
- `UNITE_COMMAND_ARGUMENS` - command arguments (`app.py {data}/{proc}`).
- `UNITE_SOURCE_PATH` - location of the source code in docker container (`/src`).
- `UNITE_DATA_PATH` - location of the data in docker container (`/mnt/data`).
- `UNITE_LIMIT` - maximum number of concurrent jobs (`10`).


## Installation

### Docker Compose
The easiest way to install the application is to use docker-compose:
- Environment configuration and installation scripts: https://github.com/dkfz-unite/unite-environment
- Survival estimation analysis service configuration and installation scripts: https://github.com/dkfz-unite/unite-environment/tree/main/applications/unite-analysis-kmeier

### Docker
[Dockerfile](Dockerfile) is used to build an image of the application.
To build an image run the following command:
```
docker build -t unite.analysis.kmeier:latest .
```

All application components should run in the same docker network.
To create common docker network if not yet available run the following command:
```bash
docker network create unite
```

To run application in docker run the following command:
```bash
docker run \
--name unite.analysis.kmeier \
--restart unless-stopped \
--net unite \
--net-alias kmeier.analysis.unite.net \
-p 127.0.0.1:5304:80 \
-e ASPNETCORE_ENVIRONMENT=Release \
-v ./data:/mnt/data:rw \
-d \
unite.analysis.kmeier:latest
```


## Usage

### Prepare The Data
Place `input.tsv` file with input data to `{proc}` subdirectory of the `./data` directory on the host machine.
```txt
./data
└── {proc}
    └── input.tsv 
```

The file should have following structure:
```tsv
dataset_id    donor_id enrolment_date status status_change_date  status_change_day
project-1    sample-1  2020-01-01  true  2021-01-01
project-1    sample-2  2020-01-01  false  2021-01-01
project-1    sample-3  2020-01-01  true  2021-01-01
project-1    sample-4  2020-01-01  false  2021-01-01
```

Where:
- `dataset_id` - dataset identifier (if comparing multiple datasets).
- `donor_id`* - donor identifier.
- `enrolment_date` - donor enrolment date in format `yyyy-mm-dd`.
- `status`* - `true` is case of event (donor death or disease progression) or `false` otherwise.
- `status_change_date` - date in format `yyyy-mm-dd`, when the status was last time revised.
- `status_change_day` - relative number of days since enrolment, when the status was last time revised.

Requirements:
- Fields marked with `*` are required.
- Either (`endolment_date` and `status_change_date`) or (`status_change_day`) must be set.

### Run The Analysis
Send a POST request to the `localhost:5304/api/run?key={key}` endpoint, where `key` is the process key and the name of the corresponding process directory.

This will invoke the command `python` with the arguments `app.py {data}/{proc}` where:
- All entries of `{proc}` will be replaced with the process `key`, which is the name of the corresponding process directory.
- All entries of `{data}` will be replaced with the path to the data location in docker container (In the example `./data` on the host machine will be mounted to `/mnt/data` in container).

### Analysis
Analysis will perform the following steps:
- Read input data from the input.tsv file.
- Perform Kaplan-Meier survival estimation analysis.
- Write resulting data to `results.tsv` file.
