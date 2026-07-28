from huggingface_hub import list_repo_files

repo_id = "johnnybwell/neon_CLBJ"
files = list_repo_files(repo_id, repo_type="dataset")
# Look for anything that isn't in 'raw/' or looks like satellite data
satellite_keywords = ['smap', 'sentinel', 'remote', 'satellite', 'raster', 'nc']
relevant_files = [f for f in files if any(k in f.lower() for k in satellite_keywords)]

print(f"Found {len(relevant_files)} potentially relevant satellite files.")
for f in relevant_files:
    print(f)
