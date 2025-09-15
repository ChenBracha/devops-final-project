# Flask Grocery List API

[![CI Pipeline with Security Scans](https://github.com/YOUR_USERNAME/YOUR_REPOSITORY/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPOSITORY/actions/workflows/ci.yml)

This project is a simple yet robust RESTful API for managing grocery lists, built with Python (Flask) and PostgreSQL. The entire application is containerized using Docker and is designed with a full DevOps lifecycle in mind, including Continuous Integration and Security Scanning with GitHub Actions.

---
## Tech Stack & Architecture

This project uses a modern, container-based architecture.



* **Backend**: **Python 3.11** with the **Flask** micro-framework.
* **WSGI Server**: **Gunicorn** to serve the Flask application.
* **Reverse Proxy**: **Nginx** to handle incoming HTTP requests and forward API calls.
* **Database**: **PostgreSQL** for data persistence.
* **Containerization**: **Docker** and **Docker Compose** to build and run the entire application stack locally.
* **CI/CD**: **GitHub Actions** for automated testing, linting, and security scanning.
* **Security**: **Trivy** for vulnerability scanning of dependencies and the final Docker image.

---
## Getting Started

Follow these instructions to get the project running on your local machine.

## Prerequisites

You must have the following software installed:
* [Docker](https://www.docker.com/get-started)
* [Docker Compose](https://docs.docker.com/compose/install/)

## Installation & Running

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git](https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git)
    cd YOUR_REPOSITORY
    ```

2.  **Create the environment file:**
    Create a file named `.env` in the project root. This file holds the database credentials. **It should not be committed to Git.**
    ```.env
    POSTGRES_DB=mydb
    POSTGRES_USER=myuser
    POSTGRES_PASSWORD=mypassword
    ```

3.  **Build and run the application:**
    Use Docker Compose to build the images and start the containers.
    ```bash
    docker-compose up --build
    ```
    The API will be accessible at `http://localhost:8080`.

---
## API Endpoints

The following endpoints are available to interact with the API.

| Method | Endpoint                             | Description                       | Example `curl` Command                                                                                   |
| :----- | :----------------------------------- | :-------------------------------- | :------------------------------------------------------------------------------------------------------- |
| `GET`    | `/api/lists/<list_id>`               | Get a specific list and its items | `curl http://localhost:8080/api/lists/1`                                                                   |
| `POST`   | `/api/lists`                         | Create a new grocery list         | `curl -X POST -H "Content-Type: application/json" -d '{"list_name": "Weekend Party"}' http://localhost:8080/api/lists` |
| `DELETE` | `/api/lists/<list_id>`               | Delete a list                     | `curl -X DELETE http://localhost:8080/api/lists/1`                                                         |
| `POST`   | `/api/lists/<list_id>/items`         | Add an item to a specific list    | `curl -X POST -H "Content-Type: application/json" -d '{"item_name": "Chips"}' http://localhost:8080/api/lists/1/items` |

---
## DevOps & CI/CD

This project includes a CI pipeline configured in `.github/workflows/ci.yml`. The pipeline is triggered on every push or pull request to the `main` branch and performs the following jobs:

1.  **Lint and Scan Repository**:
    * Lints the Python code using **Flake8**.
    * Scans the filesystem and Python dependencies for known vulnerabilities using **Trivy**.

2.  **Build and Scan Docker Image**:
    * Builds the application's Docker image.
    * Scans the final Docker image for OS and library vulnerabilities using **Trivy**.

The build will fail if the linter finds serious issues or if Trivy detects any `HIGH` or `CRITICAL` severity vulnerabilities.