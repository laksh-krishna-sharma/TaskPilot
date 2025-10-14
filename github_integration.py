import subprocess
import tempfile
import os
import re
from typing import Dict
from dotenv import load_dotenv
import base64

load_dotenv()

GITHUB_USER = os.getenv("GITHUB_USER")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def parse_llm_output(output: str) -> Dict[str, str]:
    """Parse LLM output to extract code files."""
    files = {}
    # Regex to find code blocks
    pattern = r'```(\w+)?\n(.*?)\n```'
    matches = re.findall(pattern, output, re.DOTALL)
    for lang, code in matches:
        if lang.lower() in ['html', 'css', 'javascript', 'js']:
            ext = {'html': 'html', 'css': 'css', 'javascript': 'js', 'js': 'js'}.get(lang.lower(), 'txt')
            filename = f"index.{ext}" if ext == 'html' else f"styles.{ext}" if ext == 'css' else f"script.{ext}"
            files[filename] = code.strip()
    return files

def save_attachments(repo_dir: str, attachments: list):
    """Save data URI attachments to files."""
    for att in attachments:
        url = att['url']
        if url.startswith('data:'):
            # Parse data URI
            header, data = url.split(',', 1)
            if 'base64' in header:
                data = base64.b64decode(data)
            else:
                data = data.encode('utf-8')
            # Save file
            with open(os.path.join(repo_dir, att['name']), 'wb') as f:
                f.write(data)

def create_github_repo(task_id: str, files: Dict[str, str], brief: str, checks: list, attachments: list = None, round_num: int = 1) -> Dict[str, str]:
    """Create or update GitHub repo, push files, enable Pages."""
    if attachments is None:
        attachments = []
    
    repo_name = f"llm-deploy-{task_id}"
    repo_url = f"https://github.com/{GITHUB_USER}/{repo_name}"
    
    # Create temp dir for repo
    with tempfile.TemporaryDirectory() as repo_dir:
        if round_num == 1:
            # Create new repo
            # Write generated files
            for filename, content in files.items():
                with open(os.path.join(repo_dir, filename), 'w') as f:
                    f.write(content)
            
            # Save attachments
            save_attachments(repo_dir, attachments)
            
            # Add README and LICENSE
            add_readme_and_license(repo_dir, repo_name, brief, checks)
            
            # Git init
            subprocess.run(['git', 'init'], cwd=repo_dir, check=True)
            subprocess.run(['git', 'config', 'user.name', GITHUB_USER], cwd=repo_dir, check=True)
            subprocess.run(['git', 'config', 'user.email', f"{GITHUB_USER}@users.noreply.github.com"], cwd=repo_dir, check=True)
            subprocess.run(['git', 'add', '.'], cwd=repo_dir, check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=repo_dir, check=True)
            subprocess.run(['git', 'branch', '-m', 'main'], cwd=repo_dir, check=True)
            
            # Create GitHub repo
            subprocess.run(['gh', 'repo', 'create', repo_name, '--public', '--source', repo_dir, '--remote', 'origin'], check=True)
            
            # Change remote to HTTPS with token for pushing
            subprocess.run(['git', 'remote', 'set-url', 'origin', f'https://{GITHUB_TOKEN}@github.com/{GITHUB_USER}/{repo_name}.git'], cwd=repo_dir, check=True)
            
            # Push
            subprocess.run(['git', 'push', '-u', 'origin', 'main'], cwd=repo_dir, check=True)
            
            # Enable Pages
            pages_data = '{"source":{"branch":"main","path":"/"}}'
            subprocess.run(['sh', '-c', f'echo \'{pages_data}\' | gh api -X POST /repos/{GITHUB_USER}/{repo_name}/pages --input -'], check=True)
        else:
            # Update existing repo
            # Clone
            subprocess.run(['git', 'clone', repo_url, repo_dir], check=True)
            
            # Update files
            for filename, content in files.items():
                with open(os.path.join(repo_dir, filename), 'w') as f:
                    f.write(content)
            
            # Save attachments
            save_attachments(repo_dir, attachments)
            
            # Update README
            add_readme_and_license(repo_dir, repo_name, brief, checks)
            
            # Commit and push
            subprocess.run(['git', 'add', '.'], cwd=repo_dir, check=True)
            subprocess.run(['git', 'commit', '-m', f'Round {round_num} update'], cwd=repo_dir, check=True)
            subprocess.run(['git', 'push'], cwd=repo_dir, check=True)
        
        # Get commit SHA
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=repo_dir, capture_output=True, text=True, check=True)
        commit_sha = result.stdout.strip()
        
        pages_url = f"https://{GITHUB_USER}.github.io/{repo_name}/"
        
        return {
            'repo_url': repo_url,
            'commit_sha': commit_sha,
            'pages_url': pages_url
        }

def add_readme_and_license(repo_dir: str, repo_name: str, brief: str, checks: list):
    """Add README and LICENSE to repo."""
    readme = f"""# {repo_name}

Generated application.

## Brief
{brief}

## Checks
{chr(10).join(f"- {check}" for check in checks)}

## License
MIT License
"""
    with open(os.path.join(repo_dir, 'README.md'), 'w') as f:
        f.write(readme)
    
    license_text = """MIT License

Copyright (c) 2025 LLM Deployment

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
    with open(os.path.join(repo_dir, 'LICENSE'), 'w') as f:
        f.write(license_text)