# Passes for Private Residential Development

## Local Run
Install dependencies
```bash
pip install uv
```
```bash
uv sync
```
Add `.env` file with the following content:
```yaml
SECRET_KEY=change-me
MONGODB_URI=mongodb://admin:admin123@localhost:27017/?authSource=admin
```
Add this code to `commons/constants.py`:
```python
from dotenv import load_dotenv

load_dotenv()
```
Run MongoDB database using Docker
```bash
compose -f 'docker-compose.yml' up -d --build 'mongodb'
```
Run the API
```bash
cd src
uv run uvicorn app:app --reload --port 8080
```

## Docker Run
Add `.env` file with the following content:
```yaml
SECRET_KEY=change-me
MONGODB_URI=mongodb://admin:admin123@mongodb:27017/?authSource=admin
```
Run docker compose
```bash
docker compose up --build
```

## API Client
Open the `bruno_collection` on bruno API Client and use the collection.
Download Bruno API Client: [Download Bruno API Client](https://www.usebruno.com/downloads)

## Tests

Run tests
```bash
uv run pytest
```

## API Documentation

Open the API documentation [here](src/openapi.json)
