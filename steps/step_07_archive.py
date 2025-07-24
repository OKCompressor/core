import subprocess

def step_archive(files_to_archive, archive_path):
    if not files_to_archive:
        print("[Luna] No files found to archive!")
        return
    files_list = [str(f) for f in files_to_archive]
    print(f"[Luna] Archiving {len(files_list)} files → {archive_path}")
    cmd = ["7z", "a", "-mx=9", archive_path] + files_list
    result = subprocess.run(cmd)
    if result.returncode == 0:
        print(f"[Luna] Archive complete: {archive_path}")
    else:
        print(f"[Luna] Archive failed with code {result.returncode}")
