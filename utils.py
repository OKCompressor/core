import os
import subprocess
import yaml

def load_config(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def ensure_dirs(*dirs):
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def run_python_module(script, args_dict, check=True):
    if not os.path.isfile(script):
        print(f"[Luna] Script not found: {script}")
        return False
    args = ["python", script]
    for k, v in args_dict.items():
        if isinstance(v, bool):
            if v: args.append(f"--{k}")
        else:
            args.extend([f"--{k}", str(v)])
    print("[Luna] Running:", " ".join(args))
    subprocess.run(args, check=check)
    return True

def split_line_file(infile, outprefix, chunk_size=10000):
    with open(infile) as f:
        tokens = f.read().strip().split()
    for i in range(0, len(tokens), chunk_size):
        chunk = tokens[i:i+chunk_size]
        with open(f"{outprefix}{i+1}.txt", "w") as out:
            out.write(' '.join(chunk) + "\n")
