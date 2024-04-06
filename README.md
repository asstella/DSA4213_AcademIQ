# DSA4213 Project: Exam Assistant

This app allows you to easily generate summaries and practice questions for topics based on your school notes.

## Getting Started

If you haven't created a python env yet, simply run the following command (assuming Python is installed properly).

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

Once the virtual environment is setup and active, run the command to start the app:

```sh
wave run app.py
```

Which will start a Wave app at <http://localhost:10101>.

### Dependencies

This app depends on other services that are defined in `docker-compose.yml`. Some of these
services will need to be started during development. Some examples include:

- `db.py` and `upload_files()` in `app.py` relies on neo4j
- `preprocessing.py` and `upload_files()` in `app.py` relise on nlm_ingestor

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

If you prefer learning by doing, you can run `wave fetch` command that will download all the existing small Python examples that show Wave in action. The best part is that all these examples are interactive, meaning you can edit their code directly within the browser and observe the changes.

## Learn More

To learn more about H2O Wave, check out the [docs](https://wave.h2o.ai/).
