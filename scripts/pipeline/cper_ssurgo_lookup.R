library(sf)
library(RSQLite)
library(DBI)
library(jsonlite)

gpkg <- "C:/Users/mlevij/Documents/ArcGIS/Projects/Master List/Resources/SSURGO Portal/CO_SSURGO_gpkg/CO_SSURGO.gpkg"
output_path <- "C:/Users/mlevij/AppData/Local/Temp/claude/C--Users-mlevij/506a9e3e-2cc2-424c-bea3-00a1bc6d9347/scratchpad/cper_ssurgo_horizons.json"

# CPER soil pit location, from NEON.DOC.003883vB.pdf Table 6
cper_pt <- st_sfc(st_point(c(-104.74455, 40.81297)), crs = 4326)

con <- dbConnect(SQLite(), gpkg)

mu_crs <- st_read(gpkg, layer = "mupolygon", query = "SELECT * FROM mupolygon LIMIT 1") |>
  st_zm() |>
  st_crs()

cper_pt <- st_transform(cper_pt, mu_crs)

# Small bbox around the point to avoid a statewide read (same pattern as build_all_profiles.R)
buffered <- st_buffer(cper_pt, 500)  # 500m, units of mu_crs (should be meters for CO SSURGO's projected CRS)
bbox_wkt <- st_as_text(st_as_sfc(st_bbox(buffered)))
mupolygon <- st_read(gpkg, layer = "mupolygon", wkt_filter = bbox_wkt) |> st_zm() |> st_make_valid()

hit <- st_filter(mupolygon, cper_pt, .predicate = st_intersects)
cat("Map units at CPER point:", nrow(hit), "\n")
mukeys <- unique(hit$mukey)
cat("mukeys:", paste(mukeys, collapse = ", "), "\n")

sql <- paste0(
  "SELECT c.mukey, c.cokey, c.compname, c.comppct_r,
          h.hzname, h.hzdept_r, h.hzdepb_r,
          h.sandtotal_r, h.silttotal_r, h.claytotal_r,
          h.om_r, h.dbthirdbar_r, h.ph1to1h2o_r
   FROM component c
   JOIN chorizon h ON c.cokey = h.cokey
   WHERE c.mukey IN (", paste(mukeys, collapse = ","), ")
   ORDER BY c.mukey, c.comppct_r DESC, h.hzdept_r"
)
all_hz <- dbGetQuery(con, sql)
dbDisconnect(con)

# Dominant component only (same convention as build_all_profiles.R)
dominant_cokey <- all_hz$cokey[1]
dominant_compname <- all_hz$compname[1]
cat("Dominant component:", dominant_compname, "(cokey", dominant_cokey, ")\n")

dom_hz <- all_hz[all_hz$cokey == dominant_cokey, ]
cat("Horizons:", nrow(dom_hz), "\n")
print(dom_hz)

write_json(list(
  mukey = mukeys[1],
  compname = dominant_compname,
  horizons = dom_hz
), output_path, pretty = TRUE, auto_unbox = TRUE, null = "null")

cat("\nWritten to", output_path, "\n")
