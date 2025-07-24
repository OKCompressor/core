import os
import subprocess

def step_archive(config, infile, final_dir, dict_final_dir, codebook_txt):
    archive_path = os.path.join(config['output_folder'], infile, "compressed.7z")
    files = []
    files.extend([os.path.join(final_dir, f) for f in os.listdir(final_dir) if f.endswith('_bwtmtfrle_bwt.txt')])
    files.extend([os.path.join(dict_final_dir, f) for f in os.listdir(dict_final_dir) if f.endswith('_bwtmtfrle_bwt.txt')])
    files.append(codebook_txt)
    cmd = ["7z", "a", "-mx=9", archive_path] + files
    print("[Luna] Archiving with 7z:", " ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print("[Luna] 7z failed! Check your archive settings.")
    return {"archive": archive_path}
