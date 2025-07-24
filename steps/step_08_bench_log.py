import os
import subprocess

def step_bench_log(config, infile, final_dir):
    modules_dir = config['modules_dir']
    script = os.path.join(modules_dir, "core", "bench_logger.py")
    bench_log = os.path.join(config['output_folder'], infile, "benchmarks.tsv")
    if os.path.isfile(script):
        print("[Luna] Running benchmark logger.")
        subprocess.run([
            "python", script,
            "--indir", final_dir,
            "--out", bench_log
        ])
    else:
        print("[Luna] bench_logger.py not found, skipping.")
    return {"bench_log": bench_log}
