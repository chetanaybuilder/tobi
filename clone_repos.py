import urllib.request
import json
import os
import subprocess

TOKEN = os.getenv("GITHUB_TOKEN", "your_github_token_here")
BASE_DIR = r"C:\Users\batra\Downloads\Portfolio"
os.makedirs(BASE_DIR, exist_ok=True)

req = urllib.request.Request("https://api.github.com/user/repos?per_page=100")
req.add_header("Authorization", f"Bearer {TOKEN}")
req.add_header("Accept", "application/vnd.github.v3+json")

try:
    with urllib.request.urlopen(req) as response:
        repos = json.loads(response.read().decode())
        
    print(f"Found {len(repos)} repositories.")
    
    inventory = []
    
    for repo in repos:
        name = repo['name']
        clone_url = repo['clone_url']
        # Insert token into clone url for authentication
        auth_clone_url = clone_url.replace("https://", f"https://oauth2:{TOKEN}@")
        
        repo_dir = os.path.join(BASE_DIR, name)
        
        inventory.append({
            "name": name,
            "description": repo.get('description'),
            "visibility": repo.get('visibility'),
            "language": repo.get('language'),
            "topics": repo.get('topics', []),
            "html_url": repo.get('html_url')
        })
        
        if not os.path.exists(repo_dir):
            print(f"Cloning {name}...")
            subprocess.run(["git", "clone", auth_clone_url, repo_dir], check=False)
        else:
            print(f"Repo {name} already exists. Pulling latest...")
            subprocess.run(["git", "-C", repo_dir, "pull"], check=False)
            
    with open(os.path.join(BASE_DIR, "inventory.json"), "w") as f:
        json.dump(inventory, f, indent=2)
        
    print("Done cloning and inventorying.")
except Exception as e:
    print(f"Error: {e}")
