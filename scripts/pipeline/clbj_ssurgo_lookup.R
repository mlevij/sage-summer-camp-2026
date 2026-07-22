library(sf)
library(soilDB)
library(jsonlite)

output_path <- "C:/Users/mlevij/AppData/Local/Temp/claude/C--Users-mlevij/506a9e3e-2cc2-424c-bea3-00a1bc6d9347/scratchpad/clbj_ssurgo_horizons.json"

# CLBJ soil pit location, from neonscience.org soil-descriptions/clbj (Windthorst series)
clbj_pt <- st_sfc(st_point(c(-97.5673, 33.4014)), crs = 4326)

# National point lookup via USDA Soil Data Access -- no local gpkg needed (CO_SSURGO.gpkg
# used for CPER doesn't cover Texas). Same soilDB package already used by build_all_profiles.R.
mukey <- SDA_spatialQuery(clbj_pt, what = "mukey", db = "SSURGO")
cat("mukey at CLBJ point:", mukey$mukey, "\n")

sql <- paste0(
  "SELECT c.mukey, c.cokey, c.compname, c.comppct_r,
          h.hzname, h.hzdept_r, h.hzdepb_r,
          h.sandtotal_r, h.silttotal_r, h.claytotal_r,
          h.om_r, h.dbthirdbar_r, h.ph1to1h2o_r
   FROM component c
   JOIN chorizon h ON c.cokey = h.cokey
   WHERE c.mukey IN (", paste(mukey$mukey, collapse = ","), ")
   ORDER BY c.mukey, c.comppct_r DESC, h.hzdept_r"
)
all_hz <- SDA_query(sql)

dominant_cokey <- all_hz$cokey[1]
dominant_compname <- all_hz$compname[1]
cat("Dominant component:", dominant_compname, "(cokey", dominant_cokey, ")\n")

dom_hz <- all_hz[all_hz$cokey == dominant_cokey, ]
cat("Horizons:", nrow(dom_hz), "\n")
print(dom_hz)

write_json(list(
  mukey = mukey$mukey[1],
  compname = dominant_compname,
  horizons = dom_hz
), output_path, pretty = TRUE, auto_unbox = TRUE, null = "null")

cat("\nWritten to", output_path, "\n")
