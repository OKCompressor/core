from tqdm import tqdm
import glob
import os
from utils import run_python_module

def process_subidxs_through_bwt(config, infile):
    replaced_dir = os.path.join(config['output_folder'], infile, "04_replaced")
    dict_final_dir = os.path.join(config['output_folder'], infile, "99_dicts_final")
    modules_dir = config['modules_dir']
    subidx_files = glob.glob(os.path.join(replaced_dir, "repl_sub_idxs_*.txt"))
    outputs = []

    for subfile in tqdm(subidx_files, desc="[Luna] Subidx BWT/MTF/RLE"):
        bn = os.path.basename(subfile).replace(".txt", "")
        bwt = os.path.join(dict_final_dir, f"{bn}_bwtmtfrle.txt")
        # BWT
        run_python_module(os.path.join(modules_dir, "crux2", "crux2_bwt.py"),
            {"input": subfile, "output": bwt, "chunk-mode": "lines"})
        # MTF
        mtf = bwt.replace("_bwtmtfrle.txt", ".bwtmtf.txt")
        run_python_module(os.path.join(modules_dir, "crux2", "crux2_mtf.py"),
            {"input": bwt, "output": mtf, "alphabet_mode": "global"})
        # RLE
        rle = mtf.replace(".bwtmtf.txt", ".bwtmtfrle.txt")
        run_python_module(os.path.join(modules_dir, "crux2", "crux2_rle.py"),
            {"input": mtf, "output": rle})
        # Final BWT
        final_bwt = rle.replace(".txt", "_bwt.txt")
        run_python_module(os.path.join(modules_dir, "crux2", "crux2_bwt.py"),
            {"input": rle, "output": final_bwt, "chunk-mode": "lines"})
        outputs.append(final_bwt)
    return outputs  # Could use for archiving if you wish
