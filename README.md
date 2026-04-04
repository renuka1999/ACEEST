# ACEest Fitness & Gym — Web Dashboard

> **MTech Computing Systems & Infrastructure | Introduction to DevOps**
> Full-stack Flask Web Dashboard with Docker, GitHub Actions CI/CD, and Jenkins BUILD integration.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Features & Dashboard Pages](#features--dashboard-pages)
3. [Project Structure](#project-structure)
4. [Local Setup & Execution](#local-setup--execution)
5. [Running Tests Manually](#running-tests-manually)
6. [Docker Usage](#docker-usage)
7. [GitHub Actions CI/CD Pipeline](#github-actions-cicd-pipeline)
8. [Jenkins Integration — Step-by-Step](#jenkins-integration--step-by-step)
9. [API Reference](#api-reference)

---

## Project Overview

ACEest is a full-stack fitness and gym management system. It consists of:

- A **Flask REST API** serving all business logic (clients, workouts, progress, BMI)
- A **browser-based dashboard UI** served at `/` — no external frontend framework needed
- A **SQLite database** for persistence (swappable to Postgres in production)
- **Docker** packaging for environment-consistent deployment
- **GitHub Actions** for cloud-based CI/CD on every push
- **Jenkins** for on-premises BUILD validation

---

## Features & Dashboard Pages

| Page | What You Can Do |
|------|----------------|
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
├── Dockerfile                    # Multi-stage Docker build
├── docker-compose.yml            # Local container orchestration
├── Jenkinsfile                   # Jenkins declarative pipeline
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
- Python 3.11+
- pip

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
- The app runs with **Gunicorn** (production WSGI server) inside the container
- The SQLite database is persisted in the `/data` volume — data survives container restarts
- The image uses a **non-root user** for security
- Multi-stage build keeps the final image lean (no build tools in production image)

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

Jenkins acts as a second, independent BUILD environment — validating the build on your own infrastructure, not just in the cloud.

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
|--------|---------|
| **Git** | Clone from GitHub |
| **Pipeline** | Read the Jenkinsfile |
| **Docker Pipeline** | Run Docker commands |
| **JUnit** | Display test results in Jenkins UI |
| **Cobertura** (optional) | Display coverage reports |

### Step 4 — Create the Pipeline Job

1. Click **"New Item"**
2. Name it `aceest-fitness`
3. Select **"Pipeline"** → click OK
4. Under **"Pipeline"** section:
   - Definition: `Pipeline script from SCM`
   - SCM: `Git`
   - Repository URL: `https://github.com/<your-username>/aceest-fitness.git`
   - Branch: `*/main`
   - Script Path: `Jenkinsfile`
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
4. After completion, check the **Test Results** link for Pytest output

### Jenkinsfile Pipeline Stages

| Stage | What it does |
|-------|-------------|
| **Checkout** | Pulls latest code from your GitHub repo |
| **Setup Environment** | Creates Python venv, installs all dependencies |
| **Lint** | Runs flake8 — fails build on syntax errors |
| **Unit Tests** | Runs pytest, publishes JUnit XML to Jenkins UI |
| **Docker Build** | Builds and tags the Docker image |
| **Docker Test** | Starts container, hits `/health`, confirms it's alive |
| **Push to Registry** | (Optional) Pushes to Docker Hub on `main` branch |

### Enabling Docker Hub Push (Optional)

1. In Jenkins: **Manage Jenkins → Credentials → Add Credentials**
2. Kind: `Username with password`
3. ID: `dockerhub-creds`
4. Username/Password: your Docker Hub credentials
5. In `Jenkinsfile`, uncomment the `withCredentials` block in the **Push to Registry** stage
6. Update `DOCKER_REPO` at the top of the Jenkinsfile to your Docker Hub username

---

## API Reference

All API endpoints are prefixed with `/api/`.

| Method | Endpoint | Description |
|--------|----------|-------------|
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

**POST /api/clients/<name>/workout body:**
```json
{ "workout_type": "Strength", "duration_min": 60, "notes": "PR on deadlift", "date": "2025-04-04" }
```

**POST /api/clients/<name>/progress body:**
```json
{ "adherence": 85, "week": "2025-W14" }
```

---

## Version Control Strategy (Phase 2 — Your Action Required)

This section tells you exactly what Git commands to run and commit messages to write when pushing this project to GitHub for submission.

### Initial Push

```bash
# 1. Initialize
git init
git remote add origin https://github.com/<your-username>/ACEEST.git

# 2. Core application
git add app.py requirements.txt templates/
git commit -m "feat: add Flask REST API with dashboard UI for ACEest Fitness

- Implement 15 REST endpoints (clients, workouts, progress, BMI, stats)
- Add single-page dashboard with Chart.js visualizations
- Initialize SQLite schema with clients, workouts, progress tables"

# 3. Test suite
git add test_app.py
git commit -m "test: add comprehensive Pytest suite with 35 tests

- Cover all API endpoints: programs, clients, workouts, progress, BMI
- Boundary tests for adherence validation (0-100)
- Error path coverage for 400, 404, 409 responses"

# 4. Docker
git add Dockerfile docker-compose.yml
git commit -m "infra(docker): add multi-stage Dockerfile and compose config

- Multi-stage build for lean final image
- Non-root appuser for security
- Gunicorn WSGI server, named volume for DB persistence"

# 5. GitHub Actions
git add .github/
git commit -m "ci: add GitHub Actions pipeline with in-Docker test execution

- Stage 1: flake8 lint
- Stage 2: Docker build + image export
- Stage 3: Pytest runs inside the built container"

# 6. Jenkins
git add Jenkinsfile
git commit -m "ci(jenkins): add declarative Jenkinsfile with 7-stage pipeline

- Stages: Checkout, Setup, Lint, Tests, Docker Build, Smoke Test, Push
- JUnit results published to Jenkins UI"

## Project has been integrated to jenkins via the vm instance spawned through osha portal. Screenshots of the same are attached below:
- Configuration
<img width="1007" height="887" alt="image" src="https://github.com/user-attachments/assets/293d5bec-d8b3-4fac-bd53-1bb638064105" />
- Build Status
<img width="1697" height="951" alt="image" src="https://github.com/user-attachments/assets/fc6031b2-1655-4130-85f7-5e4f086976cb" />


# 7. Docs
git add README.md
git commit -m "docs: add professional README with Jenkins integration guide"

# 8. Push
git push -u origin main
```

### Branch Naming Convention

```bash
git checkout -b feature/client-management
git checkout -b feature/workout-tracking
git checkout -b fix/adherence-validation
git checkout -b infra/docker-multi-stage
git checkout -b ci/github-actions-pipeline
```


