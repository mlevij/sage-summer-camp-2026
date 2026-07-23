from huggingface_hub import HfApi

# --- site config -- edit these for a new site/repo ---
TOKEN_PATH = r"C:\Users\mlevij\OneDrive - Colostate\Levi\Hugging Face\.huggingface_token"
REPO_ID = "mlevij/neon_CLBJ"
FILES = [
    r"C:\Users\mlevij\OneDrive - Colostate\Levi\NEON\CLBJ_SWC_5yr_30min\clbj_swc_daily.csv",
    r"C:\Users\mlevij\OneDrive - Colostate\Levi\NEON\CLBJ_SWC_5yr_30min\clbj_swc_weekly.csv",
    r"C:\Users\mlevij\OneDrive - Colostate\Levi\NEON\CLBJ_SWC_5yr_30min\clbj_swc_monthly.csv",
    r"C:\Users\mlevij\repos\sage-summer-camp-2026\drought-monitor\clbj_data.json",
    r"C:\Users\mlevij\repos\sage-summer-camp-2026\drought-monitor\clbj_wfp_fc_sat.json",
]
# --------------------------------------------------

with open(TOKEN_PATH) as f:
    token = f.read().strip()

api = HfApi()
for local_path in FILES:
    repo_path = local_path.split("\\")[-1]
    print(f"Uploading {repo_path} ...")
    api.upload_file(
        path_or_fileobj=local_path,
        path_in_repo=repo_path,
        repo_id=REPO_ID,
        repo_type="dataset",
        token=token,
    )
    print("  done")

print("All files uploaded.")
