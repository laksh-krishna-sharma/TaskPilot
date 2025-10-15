# TaskPilot (LLM Code Deployment API)

A FastAPI-based service that receives natural language app briefs, uses LLMs to generate web applications, deploys them to GitHub Pages, and reports back to evaluation endpoints.

## Features
- **LLM-Powered Code Generation**: Uses configurable CLI LLMs (e.g., `llm` with Gemma models)
- **GitHub Integration**: Automatic repo creation, code pushing, and Pages deployment
- **Attachment Support**: Handles data URI attachments
- **Round-Based Updates**: Supports iterative improvements (round 1 creates, round 2+ updates)
- **Evaluation Pinging**: Automatic reporting to evaluation URLs with retry logic
- **Security**: Secret verification and no secrets in git history

## Setup

1. **Install Dependencies**:
   ```bash
   uv sync
   ```

2. **Install Required Tools**:
   - `llm` CLI: `pip install llm`
   - GitHub CLI: `gh` (install from GitHub releases)
   - Git

3. **Configure Environment**:
   Update `.env` with your credentials:
   ```
   AGENT_COMMAND=llm -m gemma3:12b
   STUDENT_SECRETS={"student@example.com": "secret123"}
   GITHUB_USER=your-github-username
   GITHUB_TOKEN=your-personal-access-token
   ```

4. **Authenticate GitHub CLI**:
   ```bash
   gh auth login
   ```

## Run

```bash
uv run uvicorn main:app --reload
```

## API Usage

### POST /task
Accepts JSON payload for app deployment requests.

**Request Body**:
```json
{
  "email": "student@example.com",
  "secret": "secret123",
  "task": "captcha-solver-abc123",
  "round": 1,
  "nonce": "unique-nonce",
  "brief": "Create a web app that...",
  "checks": ["Has MIT license", "Displays title correctly"],
  "evaluation_url": "https://evaluation.example.com/notify",
  "attachments": [
    {"name": "sample.png", "url": "data:image/png;base64,..."}
  ]
}
```

**Response**:
```json
{
  "status": "success",
  "repo_url": "https://github.com/user/llm-deploy-captcha-solver-abc123",
  "pages_url": "https://user.github.io/llm-deploy-captcha-solver-abc123/"
}
```

## Workflow

1. **Request Received**: API validates secret and parses request
2. **LLM Generation**: Sends detailed prompt to LLM for code generation
3. **File Parsing**: Extracts HTML, CSS, JS from LLM response
4. **Repo Management**: Creates/updates GitHub repo with generated files
5. **Deployment**: Enables GitHub Pages
6. **Evaluation**: POSTs repo details to evaluation URL with retries

## Testing

Test with curl:
```bash
curl -X POST http://127.0.0.1:8000/task \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "secret": "secret123",
    "task": "test-task",
    "round": 1,
    "nonce": "test-nonce",
    "brief": "Create a simple HTML page with Hello World",
    "checks": ["Page displays Hello World"],
    "evaluation_url": "https://httpbin.org/post"
  }'
```


```bash
curl -X POST http://127.0.0.1:8000/task \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "secret": "secret123",
    "task": "test-task",
    "round": 2,
    "nonce": "test-nonce",
    "brief": "Change the color of the Hello World text to red",
    "checks": ["Hello World text is displayed in red color"],
    "evaluation_url": "https://httpbin.org/post"
  }' | jq
```

## Security Notes
- Secrets are validated against configured values
- No sensitive data is committed to git
- Temporary directories are used for all operations
- GitHub tokens should have minimal required permissions

## Logs
All operations are logged to `logs/agent.log` for debugging and monitoring.
