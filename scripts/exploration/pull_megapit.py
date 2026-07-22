import neonutilities as nu

token_path = r"C:\Users\mlevij\OneDrive - Colostate\Levi\NEON\NEON API.txt"
with open(token_path) as f:
    lines = [l.strip() for l in f if l.strip()]
token = lines[-1]

nu.zips_by_product(
    dpid="DP1.00096.001",
    site="CPER",
    package="basic",
    check_size=False,
    include_provisional=True,
    progress=True,
    token=token,
    savepath=r"C:\Users\mlevij\OneDrive - Colostate\Levi\NEON\CPER_Megapit",
)
print("MEGAPIT DOWNLOAD COMPLETE")
