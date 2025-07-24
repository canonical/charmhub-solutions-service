# Solutions Service

This service manages the solutions that are displayed on Charmhub.

## Local Development Setup

These instructions explain how to set up the project for local development and testing.

### Prerequisites

- Docker and Docker Compose

### 1. Build and run the service

Clone the repository, build the images and start the application and database containers:

```bash
docker compose up --build -d
```

This will also set up migrations and seed the database with mock data via the `entrypoint.sh` script.

### 2. Accessing the application

The application is now running and accessible at `http://localhost:5000`.

### 3. Running tests

To run the tests, use the following command:

```bash
docker compose exec solutions-service python3 -m pytest tests/
```

### 4. Stopping the service

To stop the Docker container, use:

```bash
docker compose down
```
