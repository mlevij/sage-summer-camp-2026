from huggingface_hub import HfApi

TOKEN_PATH = "/home/mlevij/.huggingface_token"
REPO_ID = "mlevij/neon_CLBJ"
IMAGES_DIR = "/home/mlevij/clbj_phenocam_images"
MANIFEST_PATH = "/home/mlevij/clbj_phenocam_manifest.csv"

with open(TOKEN_PATH) as f:
    token = f.read().strip()

api = HfApi()

print("Uploading manifest...")
api.upload_file(
    path_or_fileobj=MANIFEST_PATH,
    path_in_repo="phenocam_manifest.csv",
    repo_id=REPO_ID,
    repo_type="dataset",
    token=token,
)
print("  done")

print("Uploading images folder (1,759 files, this will take a while)...")
api.upload_folder(
    folder_path=IMAGES_DIR,
    path_in_repo="phenocam_images",
    repo_id=REPO_ID,
    repo_type="dataset",
    token=token,
)
print("  done")

print("All uploaded.")
