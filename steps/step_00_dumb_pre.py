from utils import run_python_module, ensure_dirs
import os

def step_dumb_pre(config, infile):
    modules_dir = config['modules_dir']
    output_folder = config['output_folder']
    input_folder = config['input_folder']
    raw_dir = os.path.join(output_folder, infile, "00_dumb")
    ensure_dirs(raw_dir)
    script = os.path.join(modules_dir, "dumb_pre", "dumb_pre_v2.py")
    dict_out = os.path.join(raw_dir, "dict.txt")
    out_txt = os.path.join(raw_dir, "output.txt")
    args = {
        "input": os.path.join(input_folder, infile),
        "dict": dict_out,
        "out": out_txt
    }
    run_python_module(script, args)
    return {"dict": dict_out, "out": out_txt, "raw_dir": raw_dir}
