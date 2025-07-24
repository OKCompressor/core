import os
import subprocess
import yaml

def load_config(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def ensure_dirs(*dirs):
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def run_python_module(script, args_dict=None, positional_args=None, check=True):
    import subprocess
    if not os.path.isfile(script):
        print(f"[Luna] Script not found: {script}")
        return False
    args = ["python", script]
    if positional_args:
        args.extend(positional_args)
    if args_dict:
        for k, v in args_dict.items():
            if isinstance(v, bool):
                if v:  # Only include flag if True
                    args.append(f"--{k}")
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


def flatten_file_with_sentinel(infile, outfile, sentinel="\x00"):
    """
    Flatten a multi-line file (space-separated ints per line)
    into a single line, inserting a sentinel between each line.
    """
    with open(infile) as f, open(outfile, "w") as out:
        first = True
        for line in f:
            line = line.strip()
            if not line:
                continue
            if not first:
                out.write(f" {sentinel} ")
            out.write(line)
            first = False
        out.write("\n")

def unflatten_file_with_sentinel(infile, outfile, sentinel="\x00"):
    """
    Reverse flatten: splits the flat file back into multiple lines at the sentinel.
    """
    with open(infile) as f, open(outfile, "w") as out:
        data = f.read()
        lines = data.split(sentinel)
        for line in lines:
            # Clean up leading/trailing whitespace if needed
            line = line.strip()
            if line:
                out.write(line + "\n")
