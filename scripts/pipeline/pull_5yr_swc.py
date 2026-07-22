import neonutilities as nu

token_path = r"C:\Users\mlevij\OneDrive - Colostate\Levi\NEON\NEON API.txt"
with open(token_path) as f:
    lines = [l.strip() for l in f if l.strip()]
token = lines[-1]

nu.zips_by_product(
    dpid="DP1.00094.001",
    site="CLBJ",
    startdate="2021-07",
    enddate="2026-06",
    package="basic",
    timeindex="30",
    check_size=False,
    include_provisional=True,
    progress=True,
    token=token,
    savepath=r"C:\Users\mlevij\OneDrive - Colostate\Levi\NEON\CLBJ_SWC_5yr_30min",
)
print("DOWNLOAD COMPLETE")
