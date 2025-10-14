from fastapi import FastAPI, Request
import subprocess

app = FastAPI()

@app.get("/task")
async def run_task(request: Request):
    query = request.url.query
    if 'q=' not in query:
        return {"error": "No q parameter"}
    q_encoded = query.split('q=')[1]
    if '&' in q_encoded:
        q_encoded = q_encoded.split('&')[0]
    from urllib.parse import unquote
    q = unquote(q_encoded)
    try:
        result = subprocess.run(
            ["python3", "-c", q],
            capture_output=True,
            text=True,
            timeout=10
        )
        return {"output": result.stdout or result.stderr}
    except subprocess.TimeoutExpired:
        return {"error": "Task timed out"}
    except Exception as e:
        return {"error": str(e)}
