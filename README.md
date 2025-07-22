# Solutions Service

This service manages the solutions that are displayed on Charmhub.

## Local Development Setup

These instructions explain how to set up the project for local development and testing.

### Prerequisites

- Docker and Docker Compose

### 1. Build and run the service

Clone the repository, build the images and start the application and database containers in the background:

```bash
docker compose up --build -d
```

### 2. Database migrations

With the Docker container running, execute the database migrations inside the `solutions-service` container to set up the required tables:

```bash
docker compose exec solutions-service flask db upgrade
```

### 3. Seed the database

Run the seed script inside the `solutions-service` container:

```bash
docker-compose exec solutions-service python tests/seed.py
```

This will populate the database with mock data.

### 4. Accessing the application

The application is now running and accessible at `http://localhost:5000`.

### 5. Running tests

To run the tests, use the following command:

```bash
docker compose exec solutions-service python3 -m pytest tests/
```

### Stopping the service

To stop the Docker container, use:

```bash
docker compose down
```
