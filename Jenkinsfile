// ============================================================
// ACEest Fitness & Gym — Jenkinsfile
// Declarative Pipeline: Lint → Test → Docker Build → Deploy
// ============================================================

pipeline {
    agent any

    environment {
        IMAGE_NAME   = "aceest-fitness"
        IMAGE_TAG    = "${env.BUILD_NUMBER}"
        DOCKER_REPO  = "your-dockerhub-username"   // ← Change this
        CONTAINER_PORT = "5000"
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 20, unit: 'MINUTES')
        timestamps()
    }

    stages {

        // ----------------------------------------------------------
        stage('Checkout') {
            steps {
                echo "=== Pulling latest code from GitHub ==="
                checkout scm
                sh "echo 'Branch: ${env.GIT_BRANCH}' && echo 'Commit: ${env.GIT_COMMIT}'"
            }
        }

        // ----------------------------------------------------------
        stage('Setup Environment') {
            steps {
                echo "=== Creating Python virtual environment ==="
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip --quiet
                    pip install -r requirements.txt --quiet
                    echo "Python: $(python3 --version)"
                    echo "Pip packages installed successfully"
                '''
            }
        }

        // ----------------------------------------------------------
        stage('Lint') {
            steps {
                echo "=== Running flake8 syntax & style check ==="
                sh '''
                    . venv/bin/activate
                    flake8 app.py \
                        --count \
                        --select=E9,F63,F7,F82 \
                        --show-source \
                        --statistics
                    echo "Lint check PASSED"
                '''
            }
        }

        // ----------------------------------------------------------
        stage('Unit Tests') {
            steps {
                echo "=== Running Pytest test suite ==="
                sh '''
                    . venv/bin/activate
                    pytest test_app.py -v \
                        --tb=short \
                        --junitxml=test-results/junit.xml \
                        --cov=app \
                        --cov-report=xml:test-results/coverage.xml \
                        --cov-report=term-missing
                '''
            }
            post {
                always {
                    // Publish JUnit test results in Jenkins UI
                    junit 'test-results/junit.xml'
                }
            }
        }

        // ----------------------------------------------------------
        stage('Docker Build') {
            steps {
                echo "=== Building Docker Image ==="
                sh """
                    docker build \
                        -t ${IMAGE_NAME}:${IMAGE_TAG} \
                        -t ${IMAGE_NAME}:latest \
                        --label "build=${IMAGE_TAG}" \
                        --label "commit=${env.GIT_COMMIT}" \
                        .
                    echo "Image built: ${IMAGE_NAME}:${IMAGE_TAG}"
                    docker images ${IMAGE_NAME}
                """
            }
        }

        // ----------------------------------------------------------
        stage('Docker Test') {
            steps {
                echo "=== Running integration test against Docker container ==="
                sh """
                    # Start container in background
                    docker run -d \
                        --name aceest-test-${IMAGE_TAG} \
                        -p 5999:5000 \
                        -e DB_NAME=/tmp/test.db \
                        ${IMAGE_NAME}:${IMAGE_TAG}

                    # Wait for container to be ready
                    sleep 8

                    # Test health endpoint
                    response=\$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5999/health)
                    echo "Health check response: \$response"
                    if [ "\$response" != "200" ]; then
                        echo "HEALTH CHECK FAILED"
                        docker logs aceest-test-${IMAGE_TAG}
                        exit 1
                    fi
                    echo "Container health check PASSED"
                """
            }
            post {
                always {
                    sh "docker stop aceest-test-${IMAGE_TAG} || true && docker rm aceest-test-${IMAGE_TAG} || true"
                }
            }
        }

        // ----------------------------------------------------------
        // Optional: Push to Docker Hub (only on main branch)
        stage('Push to Registry') {
            steps {
                script {
                    def appVersion = readFile('VERSION').trim()
                    def imageTag = "v${appVersion}"
                    def buildTag = "build-${env.BUILD_NUMBER}"
                    withCredentials([usernamePassword(
                        credentialsId: 'dockerhub-creds',
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                    )]) {
                        sh """
                            echo \$DOCKER_PASS | docker login -u \$DOCKER_USER --password-stdin
                            docker tag ${IMAGE_NAME}:${IMAGE_TAG} \$DOCKER_USER/aceest-fitness:${imageTag}
                            docker tag ${IMAGE_NAME}:${IMAGE_TAG} \$DOCKER_USER/aceest-fitness:${buildTag}
                            docker tag ${IMAGE_NAME}:${IMAGE_TAG} \$DOCKER_USER/aceest-fitness:latest
                            docker push \$DOCKER_USER/aceest-fitness:${imageTag}
                            docker push \$DOCKER_USER/aceest-fitness:${buildTag}
                            docker push \$DOCKER_USER/aceest-fitness:latest
                        """
                    }
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withCredentials([string(credentialsId: 'sonarqube-token', variable: 'SONAR_TOKEN')]) {
                    sh """
                        . venv/bin/activate
                        pip install coverage --quiet
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

    }

    post {
        success {
            echo """
            ╔══════════════════════════════════════════╗
            ║     ACEest Jenkins BUILD PASSED ✓        ║
            ║     Build #${env.BUILD_NUMBER}            ║
            ╚══════════════════════════════════════════╝
            """
        }
        failure {
            echo """
            ╔══════════════════════════════════════════╗
            ║     ACEest Jenkins BUILD FAILED ✗        ║
            ║     Check logs above for details         ║
            ╚══════════════════════════════════════════╝
            """
        }
        always {
            // Clean workspace and remove dangling Docker layers
            sh "docker rmi ${IMAGE_NAME}:${IMAGE_TAG} || true"
            cleanWs()
        }
    }
}
