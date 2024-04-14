# Group group's DSA4213 Project: AcademIQ 

This app allows you to easily generate summaries and practice questions for topics based on your school notes.

## Getting Started

Create a python environment by running the following command (assuming Python is installed properly).

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
services will need to be started during development. Some examples include:

- `db.py` and `upload_files()` in `app.py` which relies on neo4j
- `preprocessing.py` and `upload_files()` in `app.py` which relies on nlm_ingestor

Make sure the respective services are up and running using docker compose:

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

If you prefer hands-on learning, you can run `wave fetch` command that will download all the existing small Python examples that show Wave in action. The best part is that all these examples are interactive, meaning you can edit their code directly within the browser and observe the changes.

## Learn More

To learn more about H2O Wave, check out the [docs](https://wave.h2o.ai/).
