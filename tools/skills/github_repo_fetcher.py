import os
import sys
import subprocess
import argparse

def clone_repo(repo_url, target_dir):
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Hiba: GITHUB_TOKEN nincs beállítva a környezeti változók között!")
        sys.exit(1)

    # Átírjuk az URL-t úgy, hogy tartalmazza a tokent az autentikációhoz
    if repo_url.startswith("https://github.com/"):
        auth_url = repo_url.replace("https://github.com/", f"https://oauth2:{token}@github.com/")
    else:
        auth_url = repo_url

    print(f"Repozitórium klónozása: {repo_url} -> {target_dir}")
    try:
        subprocess.run(["git", "clone", auth_url, target_dir], check=True)
        print("✅ Klónozás sikeres!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Klónozás sikertelen: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitHub Repo Fetcher az Agentek számára")
    parser.add_argument("repo_url", help="A klónozandó GitHub repozitórium URL-je")
    parser.add_argument("target_dir", help="A célkönyvtár")
    args = parser.parse_args()

    clone_repo(args.repo_url, args.target_dir)
