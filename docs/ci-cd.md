# Self-Hosted CI/CD

This project includes a no-billing CI/CD path using Woodpecker CI. Woodpecker runs as a Docker Compose web service with a Docker-backed build agent, so quality gates can run on your own machine or server instead of paid hosted CI minutes.

## What It Runs

The pipeline in `.woodpecker.yml` runs:

- `ruff check config drift_engine tests`
- `mypy config drift_engine tests`
- `pytest --cov=config --cov=drift_engine --cov-report=term-missing --cov-report=xml`
- `alembic -c alembic/alembic.ini heads`
- `python scripts/ci_api_smoke.py` against a live local Uvicorn process
- Docker image build validation in dry-run mode

## Start The CI Server

Create a GitHub or GitLab OAuth application first. The callback URL should be:

```text
http://localhost:8000/authorize
```

PowerShell example for GitHub:

```powershell
$env:WOODPECKER_HOST = "http://localhost:8000"
$env:WOODPECKER_ADMIN = "CodeExplorerRay"
$env:WOODPECKER_AGENT_SECRET = "replace-with-a-long-random-secret"
$env:WOODPECKER_GITHUB = "true"
$env:WOODPECKER_GITHUB_CLIENT = "replace-with-oauth-client-id"
$env:WOODPECKER_GITHUB_SECRET = "replace-with-oauth-client-secret"
docker compose -f docker-compose.ci.yml up -d
```

PowerShell example for GitLab:

```powershell
$env:WOODPECKER_HOST = "http://localhost:8000"
$env:WOODPECKER_ADMIN = "CodeExplorerRay"
$env:WOODPECKER_AGENT_SECRET = "replace-with-a-long-random-secret"
$env:WOODPECKER_GITLAB = "true"
$env:WOODPECKER_GITLAB_CLIENT = "replace-with-oauth-application-id"
$env:WOODPECKER_GITLAB_SECRET = "replace-with-oauth-secret"
$env:WOODPECKER_GITLAB_URL = "https://gitlab.com"
docker compose -f docker-compose.ci.yml up -d
```

Open the Woodpecker web UI:

```text
http://localhost:8000
```

Enable the `CodeExplorerRay/drift_engine` repository in Woodpecker. The next push or manual run will execute the pipeline. Use the GitHub or GitLab OAuth app and webhook that Woodpecker creates for the repository; that is what makes pushes trigger automatically without paid hosted CI.

## Stop The CI Server

```powershell
docker compose -f docker-compose.ci.yml down
```

## Security Notes

- Do not commit OAuth client secrets or the Woodpecker agent secret.
- The agent mounts the Docker socket so it can build containers. Run it only on a trusted host.
- Keep this CI stack separate from production app credentials.
- Use dry-run image builds until you configure a private registry and explicit publish credentials.
