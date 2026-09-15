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

# TO USE AI (Deepseek)
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# TO USE EMAIL
SENDER_EMAIL=youemail@hot.com
SENDER_PASSWORD=your-email-password-for-smtp

# OPTIONAL
CORS_ALLOW_ORIGINS=*
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=20
RATE_LIMIT_WINDOW_SECONDS=60
```
Run MongoDB database using Docker
```bash
docker compose -f 'docker-compose.yml' up -d --build 'mongodb'
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

# TO USE AI (Deepseek)
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# TO USE EMAIL
SENDER_EMAIL=youemail@hot.com
SENDER_PASSWORD=your-email-password-for-smtp
```
Run docker compose
```bash
docker compose up --build
```

## API Client
Open the `bruno_collection` on bruno API Client and use the collection.
Download Bruno API Client: [Download Bruno API Client](https://www.usebruno.com/downloads)

## Seed Fake Data

Populate the database with fake users, houses and passes (idempotent). All
seeded users share the password `Password123!`.
```bash
uv run python scripts/seed_fake_data.py
```

## Tests

Run tests
```bash
uv run pytest
```

## API Documentation

Open the API documentation [here](openapi.json)
