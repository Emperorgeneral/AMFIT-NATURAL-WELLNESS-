#!/usr/bin/env python3
import shutil
import subprocess
import os

os.chdir(r"C:\Users\Michael Favour\Downloads\amfit e-commerce")

# Copy signup to mirror
shutil.copy("templates/users/signup.html", "amfit_ecommerce/templates/users/signup.html")
print("✓ Synced signup template")

# Git operations
subprocess.run(["git", "add", "templates/users/signup.html", "amfit_ecommerce/templates/users/signup.html"], check=True)
print("✓ Git add successful")

subprocess.run(["git", "commit", "-m", "Unify signup with login: identical button text and CSS classes"], check=True)
print("✓ Git commit successful")

subprocess.run(["git", "push", "origin", "main"], check=True)
print("✓ Git push successful")

print("\n✅ All operations completed!")
