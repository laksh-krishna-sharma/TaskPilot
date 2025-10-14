import subprocess
import tempfile
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional

load_dotenv()

AGENT_COMMAND = os.getenv("AGENT_COMMAND", "aider --message")

def build_web_app_prompt(brief: str, checks: List[str], attachments: Optional[List[Dict[str, str]]] = None) -> str:
    prompt = f"""
Create a complete single-page web application based on the following brief:

{brief}

Requirements and checks to pass:
{chr(10).join(f"- {check}" for check in checks)}

Please generate the following files:
1. index.html - Main HTML file
2. styles.css - CSS styles
3. script.js - JavaScript functionality

"""
    if attachments:
        prompt += "\nAttachments provided:\n"
        for att in attachments:
            prompt += f"- {att['name']}: {att['url'][:100]}...\n"
        prompt += "Use these attachments in your application as needed.\n"
    
    prompt += """
Ensure the application:
- Is self-contained (no external dependencies unless specified)
- Passes all the checks listed
- Has professional, clean code
- Includes proper HTML structure, styling, and interactivity

Output the code for each file clearly labeled.
"""
    return prompt

def run_agent_task(brief: str, checks: List[str] = None, attachments: Optional[List[Dict[str, str]]] = None):
    if checks is None:
        checks = []
    prompt = build_web_app_prompt(brief, checks, attachments)
    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = AGENT_COMMAND.split() + [prompt]
        try:
            result = subprocess.run(
                cmd,
                cwd=tmpdir,
                text=True,
                capture_output=True,
                timeout=300  # 5 minutes timeout
            )
            return result
        except subprocess.TimeoutExpired:
            return subprocess.CompletedProcess(cmd, -1, stdout="", stderr="Task timed out")