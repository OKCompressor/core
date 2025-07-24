import os
import glob
import subprocess

def step_archive(config, infile, bwt_dir, dict_dir, codebook_bwt, subidx_bwt_files):
    archive_path = os.path.join(config['output_folder'], infile, "compressed.7z")
    files = []

    # Dict BWTs
    files.extend(glob.glob(os.path.join(dict_dir, "cat*_bwtmtfrle_bwt.txt")))
    
    # Codebook BWT
    if codebook_bwt:
        files.append(codebook_bwt)
    # Subidx BWT files
    if subidx_bwt_files:
        files.extend(subidx_bwt_files)
    # Inside step_archive after subidx_bwt_files
    base4_dir = os.path.join(config['output_folder'], infile, "ccnlp")
    files.extend(glob.glob(os.path.join(base4_dir, "cats_*.base4")))


    # Dedup just in case
    files = list(dict.fromkeys(files))

    cmd = ["7z", "a", "-mx=9", archive_path] + files
    print("[Luna] Archiving with 7z:", " ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print("[Luna] 7z failed! Check your archive settings.")
    return {"archive": archive_path}
