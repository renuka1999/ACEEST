# ACEest Fitness & Gym — Web Dashboard

> **MTech Computing Systems & Infrastructure | Introduction to DevOps**
> Full-stack Flask Web Dashboard with Docker, Podman, Docker Hub, SonarQube, GitHub Actions CI/CD, and Jenkins BUILD integration.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Features & Dashboard Pages](#features--dashboard-pages)
3. [Project Structure](#project-structure)
4. [Local Setup & Execution](#local-setup--execution)
5. [Running Tests Manually](#running-tests-manually)
6. [Docker Usage](#docker-usage)
7. [Docker Hub — Image Registry & Versioning](#docker-hub--image-registry--versioning)
8. [Podman Usage](#podman-usage)
9. [SonarQube — Static Code Analysis](#sonarqube--static-code-analysis)
10. [GitHub Actions CI/CD Pipeline](#github-actions-cicd-pipeline)
11. [Jenkins Integration — Step-by-Step](#jenkins-integration--step-by-step)
12. [API Reference](#api-reference)

---

## Project Overview

ACEest is a full-stack fitness and gym management system. It consists of:

* A **Flask REST API** serving all business logic (clients, workouts, progress, BMI)
* A **browser-based dashboard UI** served at `/` — no external frontend framework needed
* A **SQLite database** for persistence (swappable to Postgres in production)
* **Docker & Podman** packaging for environment-consistent, OCI-compliant deployment
* **Docker Hub** as the central container registry — all versioned image tags stored and pulled from here
* **SonarQube** for static code analysis and quality gate enforcement, triggered automatically by Jenkins
* **GitHub Actions** for cloud-based CI/CD on every push
* **Jenkins** for on-premises BUILD, test, image push, and SonarQube analysis automation

### Project has been integrated to Jenkins via the Virtual Machine instance spawned through osha portal. Screenshots of the same are attached below:
- Configuration
<img width="1007" height="887" alt="image" src="https://github.com/user-attachments/assets/293d5bec-d8b3-4fac-bd53-1bb638064105" />
- Build Status
<img width="1697" height="951" alt="image" src="https://github.com/user-attachments/assets/fc6031b2-1655-4130-85f7-5e4f086976cb" />
---

## Features & Dashboard Pages

| Page | What You Can Do |
| --- | --- |
| **Dashboard** | See live stats: total clients, active members, workouts logged, avg adherence, program distribution |
| **Clients** | Add clients (name, age, weight, program, membership), view details, delete clients |
| **Workouts** | Log workout sessions per client (type, duration, notes, date), delete entries |
| **Progress** | Log weekly adherence % per client, view progress table and live chart |
| **Programs** | Browse Fat Loss / Muscle Gain / Beginner programs, assign a program to any client |
| **BMI Calculator** | Select a client + enter height → instant BMI with category and visual bar |

Every action on the UI calls the corresponding REST API endpoint — there is no page reload.

---

## Project Structure

```
aceest-fitness/
├── app.py                        # Flask app — routes, API, DB logic
├── test_app.py                   # Pytest test suite (30+ tests)
├── requirements.txt              # Python dependencies
├── VERSION                       # Application version (e.g. 1.0.0) — drives Docker Hub tags
├── sonar-project.properties      # SonarQube project configuration
├── Dockerfile                    # Multi-stage Docker build
├── docker-compose.yml            # Local container orchestration
├── Jenkinsfile                   # Jenkins declarative pipeline (lint → test → sonar → docker → push)
├── README.md                     # This file
├── templates/
│   └── dashboard.html            # Full single-page dashboard UI
└── .github/
    └── workflows/
        └── main.yml              # GitHub Actions CI/CD pipeline
```

---

## Local Setup & Execution

### Prerequisites

* Python 3.11+
* pip

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/aceest-fitness.git
cd aceest-fitness

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the Flask application
python app.py
```

Open your browser at **http://localhost:5000** — the dashboard loads immediately.

---

## Running Tests Manually

```bash
# Activate your virtual environment first
source venv/bin/activate

# Run all tests
pytest test_app.py -v

# Run with coverage report
pytest test_app.py -v --cov=app --cov-report=term-missing

# Generate XML reports (required for SonarQube)
pytest test_app.py -v \
  --junitxml=test-results/junit.xml \
  --cov=app \
  --cov-report=xml:test-results/coverage.xml
```

The test suite covers home/health endpoints, all program routes, client CRUD, workout CRUD, progress boundary validation (0–100), BMI calculation, and all error responses (400, 404, 409).

---

## Docker Usage

### Option A — Docker Compose (recommended)

```bash
# Build and start the container
docker-compose up --build

# Run in background
docker-compose up -d --build

# Stop
docker-compose down

# Stop and remove data volume
docker-compose down -v
```

### Option B — Docker CLI

```bash
# Build the image
docker build -t aceest-fitness:latest .

# Run the container (data persists in named volume)
docker run -d \
  --name aceest \
  -p 5000:5000 \
  -v aceest_data:/data \
  aceest-fitness:latest

# Check logs
docker logs aceest

# Stop and remove
docker stop aceest && docker rm aceest
```

The dashboard will be available at **http://localhost:5000**.

### Docker Notes

* The app runs with **Gunicorn** (production WSGI server) inside the container
* The SQLite database is persisted in the `/data` volume — data survives container restarts
* The image uses a **non-root user** for security
* Multi-stage build keeps the final image lean (no build tools in production image)

---

## Docker Hub — Image Registry & Versioning

Docker Hub is used as the central container registry for all versioned builds of the ACEest image. Jenkins automatically builds, tags, and pushes images on every successful merge to `main`.

### Image Tagging Strategy

Every Jenkins build on `main` produces three tags simultaneously:

| Tag | Example | Purpose |
| --- | --- | --- |
| Semantic version | `v1.0.0` | Human-readable release identifier, driven by the `VERSION` file |
| Build number | `build-42` | Ties the image directly to a specific Jenkins run for traceability |
| Latest | `latest` | Always points to the most recent stable image |

The `VERSION` file in the repository root controls the semantic tag. Bumping it from `1.0.0` to `2.0.0` and merging to `main` automatically causes the next Jenkins build to push the `v2.0.0` tag.

### Pulling Images from Docker Hub

```bash
# Pull the latest stable image
docker pull <your-dockerhub-username>/aceest-fitness:latest

# Pull a specific versioned release
docker pull <your-dockerhub-username>/aceest-fitness:v1.0.0

# Pull by build number for exact traceability
docker pull <your-dockerhub-username>/aceest-fitness:build-42

# Run directly from Docker Hub (no local build needed)
docker run -d \
  --name aceest \
  -p 5000:5000 \
  -v aceest_data:/data \
  <your-dockerhub-username>/aceest-fitness:latest
```

### Docker Hub Repository

All published image versions are available at:
`https://hub.docker.com/r/<your-dockerhub-username>/aceest-fitness`

### Jenkins → Docker Hub Push Flow

The `Push to Registry` stage in the Jenkinsfile handles this automatically:

1. Reads the `VERSION` file to determine the semantic version tag
2. Logs in to Docker Hub using credentials stored securely in Jenkins (`dockerhub-creds`)
3. Tags the built image with `v<version>`, `build-<BUILD_NUMBER>`, and `latest`
4. Pushes all three tags to Docker Hub
5. Jenkins credential setup: **Manage Jenkins → Credentials → Add** → Kind: `Username with password`, ID: `dockerhub-creds`

---

## Podman Usage

Podman is a daemonless, rootless OCI-compatible container engine. Because the ACEest Docker image follows the OCI image specification, it runs on Podman without any modification — no Dockerfile changes are needed.

### Install Podman

```bash
# Ubuntu / Debian
sudo apt update && sudo apt install -y podman

# Verify installation
podman --version
```

### Run the ACEest Image with Podman

```bash
# Pull directly from Docker Hub (Podman supports Docker Hub natively)
podman pull docker.io/<your-dockerhub-username>/aceest-fitness:latest

# Run the container
podman run -d \
  --name aceest-podman \
  -p 5000:5000 \
  -v aceest_data:/data \
  docker.io/<your-dockerhub-username>/aceest-fitness:latest

# Check running containers
podman ps

# View logs
podman logs aceest-podman

# Stop and remove
podman stop aceest-podman && podman rm aceest-podman
```

### Build Locally with Podman

Podman reads the same `Dockerfile` — no changes needed:

```bash
# Build image using Podman
podman build -t aceest-fitness:latest .

# Tag and push to Docker Hub
podman tag aceest-fitness:latest docker.io/<your-dockerhub-username>/aceest-fitness:latest
podman push docker.io/<your-dockerhub-username>/aceest-fitness:latest
```

### Podman vs Docker — Key Differences in This Project

| Aspect | Docker | Podman |
| --- | --- | --- |
| Daemon required | Yes (`dockerd`) | No — fully daemonless |
| Root required | Yes (by default) | No — rootless by default |
| CLI compatibility | `docker` commands | Identical `podman` commands |
| Docker Hub access | Native | Native (`docker.io/` prefix) |
| OCI image compatibility | ✅ | ✅ — same image, no rebuild |
| Compose support | `docker-compose` | `podman-compose` (drop-in) |

### Podman Compose (alternative to docker-compose)

```bash
pip install podman-compose

# Identical to docker-compose usage
podman-compose up --build
podman-compose down
```

---

## SonarQube — Static Code Analysis

SonarQube performs automated static code analysis on every Jenkins build, enforcing quality gates before a build is considered successful. The analysis results — covering code smells, bugs, vulnerabilities, coverage, and duplication — are published to the SonarQube dashboard.

### SonarQube is integrated and triggered automatically by Jenkins on every build.

### Project Configuration

The `sonar-project.properties` file in the repository root configures the analysis:

```properties
sonar.projectKey=aceest-fitness
sonar.projectName=ACEest Fitness
sonar.projectVersion=1.0
sonar.sources=.
sonar.exclusions=venv/**,test_app.py,**/__pycache__/**
sonar.python.coverage.reportPaths=test-results/coverage.xml
sonar.python.xunit.reportPath=test-results/junit.xml
```

### What SonarQube Checks

| Category | What is measured |
| --- | --- |
| **Bugs** | Code that is likely to produce incorrect behaviour |
| **Vulnerabilities** | Security hotspots in the application code |
| **Code Smells** | Maintainability issues and anti-patterns |
| **Coverage** | Percentage of application code exercised by Pytest |
| **Duplications** | Copy-paste code blocks across the codebase |

### Running SonarQube Locally

```bash
# Start SonarQube via Docker
docker run -d \
  --name sonarqube \
  -p 9000:9000 \
  -e SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true \
  sonarqube:community

# Access the dashboard at http://localhost:9000
# Default credentials: admin / admin (you will be prompted to change on first login)
```

Once SonarQube is running, generate a project token from **My Account → Security → Generate Token** and store it in Jenkins (see below).

### Trigger Analysis Manually

```bash
# Run Pytest with coverage first (SonarQube reads the XML report)
pytest test_app.py -v \
  --junitxml=test-results/junit.xml \
  --cov=app \
  --cov-report=xml:test-results/coverage.xml

# Run the scanner
sonar-scanner \
  -Dsonar.projectKey=aceest-fitness \
  -Dsonar.sources=. \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.login=<your-sonar-token>
```

### Jenkins Integration for SonarQube

The `SonarQube Analysis` stage runs automatically in the Jenkins pipeline after Unit Tests and before the Docker build. No manual intervention is required.

Jenkins credential setup for SonarQube:
1. **Manage Jenkins → Credentials → Add Credentials**
2. Kind: `Secret text`
3. Secret: your SonarQube token
4. ID: `sonarqube-token`

The Jenkinsfile stage:

```groovy
stage('SonarQube Analysis') {
    steps {
        withCredentials([string(credentialsId: 'sonarqube-token', variable: 'SONAR_TOKEN')]) {
            sh """
                . venv/bin/activate
                sonar-scanner \
                  -Dsonar.projectKey=aceest-fitness \
                  -Dsonar.sources=. \
                  -Dsonar.host.url=http://localhost:9000 \
                  -Dsonar.login=\$SONAR_TOKEN \
                  -Dsonar.python.coverage.reportPaths=test-results/coverage.xml
            """
        }
    }
}
```

---

## GitHub Actions CI/CD Pipeline

Defined in `.github/workflows/main.yml`. Triggers on every `push` or `pull_request`.

### Pipeline Flow

```
Push to GitHub
      │
      ▼
┌─────────────────────┐
│  Stage 1: Lint      │  flake8 syntax check
└────────┬────────────┘
         │ pass
         ▼
┌─────────────────────┐
│  Stage 2: Tests     │  pytest (30+ tests) + coverage report
└────────┬────────────┘
         │ pass
         ▼
┌─────────────────────┐
│  Stage 3: Docker    │  docker build + smoke test /health
└────────┬────────────┘
         │ all pass
         ▼
     Pipeline ✅
```

Each stage only runs if the previous one passes (strict quality gate).

---

## Jenkins Integration — Step-by-Step

Jenkins is the central automation hub — it validates the build, runs tests, performs SonarQube analysis, pushes versioned images to Docker Hub, and deploys to Kubernetes, all triggered automatically on every push to `main`.

### Step 1 — Install Jenkins

**On Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install -y openjdk-17-jdk
wget -q -O - https://pkg.jenkins.io/debian/jenkins.io.key | sudo apt-key add -
sudo sh -c 'echo deb http://pkg.jenkins.io/debian-stable binary/ > /etc/apt/sources.list.d/jenkins.list'
sudo apt update
sudo apt install -y jenkins
sudo systemctl start jenkins
sudo systemctl enable jenkins
```

**On macOS (Homebrew):**

```bash
brew install jenkins-lts
brew services start jenkins-lts
```

Access Jenkins at **http://localhost:8080**.

### Step 2 — Initial Jenkins Setup

1. Get the initial admin password:

   ```bash
   sudo cat /var/lib/jenkins/secrets/initialAdminPassword
   ```
2. Paste it into the Jenkins setup wizard at http://localhost:8080
3. Click **"Install Suggested Plugins"**
4. Create your admin user

### Step 3 — Install Required Plugins

Go to **Manage Jenkins → Plugins → Available** and install:

| Plugin | Purpose |
| --- | --- |
| **Git** | Clone from GitHub |
| **Pipeline** | Read the Jenkinsfile |
| **Docker Pipeline** | Run Docker commands |
| **JUnit** | Display test results in Jenkins UI |
| **SonarQube Scanner** | Execute SonarQube analysis and enforce quality gates |
| **Cobertura** (optional) | Display coverage reports |

### Step 4 — Create the Pipeline Job

1. Click **"New Item"**
2. Name it `aceest-fitness`
3. Select **"Pipeline"** → click OK
4. Under **"Pipeline"** section:
   * Definition: `Pipeline script from SCM`
   * SCM: `Git`
   * Repository URL: `https://github.com/<your-username>/aceest-fitness.git`
   * Branch: `*/main`
   * Script Path: `Jenkinsfile`
5. Click **Save**

### Step 5 — Configure GitHub Webhook (Auto-trigger)

1. In your GitHub repo: **Settings → Webhooks → Add webhook**
2. Payload URL: `http://<your-jenkins-host>:8080/github-webhook/`
3. Content type: `application/json`
4. Events: `Just the push event`
5. Click **Add webhook**

Now every `git push` automatically triggers a Jenkins build.

### Step 6 — Run Your First Build

1. Click **"Build Now"** on the pipeline page
2. Watch the stages execute in the **Stage View**
3. Click any stage to view logs
4. After completion, check the **Test Results** link for Pytest output and the **SonarQube** dashboard for code quality results

### Jenkinsfile Pipeline Stages

| Stage | What it does |
| --- | --- |
| **Checkout** | Pulls latest code from your GitHub repo |
| **Setup Environment** | Creates Python venv, installs all dependencies |
| **Lint** | Runs flake8 — fails build on syntax errors |
| **Unit Tests** | Runs pytest, publishes JUnit XML to Jenkins UI |
| **SonarQube Analysis** | Runs sonar-scanner, publishes results to SonarQube dashboard — enforces quality gate ✅ |
| **Docker Build** | Builds and tags the Docker image |
| **Docker Test** | Starts container, hits `/health`, confirms it's alive |
| **Push to Registry** | Pushes `v<version>`, `build-<N>`, and `latest` tags to Docker Hub ✅ |

### Credentials Configuration Summary

| Credential ID | Kind | Used for |
| --- | --- | --- |
| `dockerhub-creds` | Username with password | Docker Hub image push |
| `sonarqube-token` | Secret text | SonarQube analysis authentication |

Both credentials are stored securely in Jenkins and never appear in plaintext in the Jenkinsfile or repository.

---

## API Reference

All API endpoints are prefixed with `/api/`.

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/` | Dashboard UI |
| GET | `/health` | Health check |
| GET | `/api/stats` | Dashboard statistics |
| GET | `/api/programs` | List all programs |
| GET | `/api/programs/<name>` | Get program details |
| GET | `/api/clients` | List all clients |
| POST | `/api/clients` | Add a new client |
| GET | `/api/clients/<name>` | Get client details |
| DELETE | `/api/clients/<name>` | Delete a client |
| POST | `/api/clients/<name>/workout` | Log a workout |
| GET | `/api/clients/<name>/workouts` | Get all workouts |
| DELETE | `/api/clients/<name>/workouts/<id>` | Delete a workout |
| POST | `/api/clients/<name>/progress` | Log weekly progress |
| GET | `/api/clients/<name>/progress` | Get all progress entries |
| GET | `/api/clients/<name>/bmi?height_cm=X` | Calculate BMI |

**POST /api/clients body:**

```json
{ "name": "Arjun", "age": 25, "weight": 75.0, "program": "Fat Loss", "membership_status": "Active" }
```

**POST /api/clients/\<name\>/workout body:**

```json
{ "workout_type": "Strength", "duration_min": 60, "notes": "PR on deadlift", "date": "2025-04-04" }
```

**POST /api/clients/\<name\>/progress body:**

```json
{ "adherence": 85, "week": "2025-W14" }
```

---

## Version Control Strategy

### Branch Naming Convention

```bash
git checkout -b feature/client-management
git checkout -b feature/workout-tracking
git checkout -b fix/adherence-validation
git checkout -b infra/docker-multi-stage
git checkout -b ci/github-actions-pipeline
git checkout -b ci/sonarqube-integration
git checkout -b infra/dockerhub-versioning
```

### Commit Message Convention

```bash
# Application changes
git commit -m "feat: add Flask REST API with dashboard UI for ACEest Fitness"

# Infrastructure
git commit -m "infra(docker): add multi-stage Dockerfile and compose config"
git commit -m "infra(dockerhub): enable versioned image push with semantic tags"

# CI/CD
git commit -m "ci(jenkins): add SonarQube analysis stage with quality gate"
git commit -m "ci(jenkins): enable Docker Hub push via dockerhub-creds"

# Tests
git commit -m "test: add comprehensive Pytest suite with 35 tests"

# Docs
git commit -m "docs: update README with Docker Hub, Podman, and SonarQube sections"
```
