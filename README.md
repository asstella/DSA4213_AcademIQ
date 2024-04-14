# Group group's DSA4213 Project: AcademIQ 

Introducing AcademIQ - your personal exam assistant designed to simplify your study experience and maximize your academic success. Simply upload any document and watch AcademIQ easily generate summaries and practice questions based on the different topics present in the documents.

## To Start

Ensure Docker is installed and running on your device.

Run the below command to start AcademIQ:

```sh
docker compose up -d
```

Head over to <http://localhost:10101> to start uploading.


## To Set Up A Development Server / To Edit On Wave App

Create a python environment by running the following command (this is assuming Python is installed properly).

For MacOS / Linux:

```sh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

For Windows:

```sh
python3 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Once the virtual environment is setup and active, run the below command to start the app:

```sh
wave run app.py
```

A Wave app will start at <http://localhost:10101>.


### Dependencies

This app depends on external services that are defined in `docker-compose.yml`. Some of these
services will need to run during development. They include:

- `db.py` and `upload_files()` in `app.py` which relies on neo4j
- `preprocessing.py` and `upload_files()` in `app.py` which relies on nlm_ingestor

Ensure the respective services are up and running using docker compose:

```sh
docker compose up -d <service_name>
```

## Testing

To run tests for specific files, run the command:

```sh
pytest <filename>
```

This will run the test functions prefixed with `test_` in the file.

## Interactive examples

If you prefer hands-on learning, you can run the command `wave fetch` that will download all the existing small Python examples that show Wave in action. The best part is that all these examples are interactive, meaning you can edit their code directly within the browser and observe the changes.

## Learn More

To learn more about H2O Wave, check out the [docs](https://wave.h2o.ai/).