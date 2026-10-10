#!/usr/bin/env python3
"""
Eco RouteAI GitHub Push Utility
Pushes the local main branch to https://github.com/yeswanth240407-lang/ecorouteai1.git using a GitHub token.
Usage:
    python push_to_github.py <GITHUB_TOKEN>
    or set environment variable GITHUB_TOKEN and run:
    python push_to_github.py
"""

import sys
import os
import dulwich.repo
import dulwich.porcelain

def push_repo(token: str):
    remote_url = f"https://{token}@github.com/yeswanth240407-lang/ecorouteai1.git"
    repo = dulwich.repo.Repo(".")
    print(f"Connecting to remote: https://github.com/yeswanth240407-lang/ecorouteai1.git ...")
    try:
        dulwich.porcelain.push(repo, remote_url, "refs/heads/main")
        print(" Successfully pushed main branch to GitHub!")
    except Exception as e:
        print(f"Push failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    token = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Error: GitHub Personal Access Token is required.")
        print("Usage: python push_to_github.py <YOUR_GITHUB_TOKEN>")
        sys.exit(1)
    push_repo(token.strip())
