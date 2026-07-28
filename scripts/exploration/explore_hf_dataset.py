from huggingface_hub import list_repo_files

repo_id = "johnnybwell/neon_CLBJ"
files = list_repo_files(repo_id, repo_type="dataset")
raw_files = [f for f in files if f.startswith("raw/")]
print(f"Found {len(raw_files)} files in raw directory.")
for f in raw_files[:20]: # Print first 20 to get an idea
    print(f)
if len(raw_files) > 20:
    print("...")
