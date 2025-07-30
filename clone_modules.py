#!/usr/bin/env python3
import os
import subprocess

MOD_DIR = "modules"
os.makedirs(MOD_DIR, exist_ok=True)

# --- OKCompressor-only repo URLs ---
repos = {
    "dumb_pre":   "git@github.com:OKCompressor/dumb_pre.git",
    "redumb":     "git@github.com:OKCompressor/redumb.git",
    "ngram-pos":  "git@github.com:OKCompressor/ngram-pos.git",
    "cc_nlp":     "git@github.com:OKCompressor/cc_nlp.git",
    "ngram-dawg": "git@github.com:OKCompressor/ngram-dawg.git",
    "crux2":      "git@github.com:OKCompressor/crux2.git",
    "core":       "git@github.com:OKCompressor/core.git"
}

print(f"[Luna] Checking/Cloning {len(repos)} OKCompressor modules to ./{MOD_DIR}/\n")

for name, url in repos.items():
    mod_path = os.path.join(MOD_DIR, name)
    if os.path.isdir(mod_path):
        print(f"  [✔] {name}: already exists, skipping.")
    else:
        print(f"  [→] {name}: cloning from {url} ...")
        try:
            subprocess.run(["git", "clone", url, mod_path], check=True)
            print(f"  [✓] {name}: clone complete.")
        except subprocess.CalledProcessError as e:
            print(f"  [✗] ERROR cloning {name}: {e}")

print("\n[Luna] Module repo sync complete. All available modules are ready.")
