#%%
### GLOBAL VARIABLES

output_file = "data/tiles_merged.csv"


### IMPORTS ###
import pandas as pd

from functions_download import download_metadata
from functions_process import extract_coords_tilename

# %%
### RUN CODE ###

# Download metadata for tiles and find matching tiles
download_metadata(raw_data_folder="data/",
    metadata_filename="dop_nw.csv",
    url_metadata="https://www.opengeodata.nrw.de/produkte/geobasis/lusat/dop/dop_jp2_f10/dop_meta.zip",
    skiprows=5,
    rewrite_download=True)

download_metadata(raw_data_folder="data/",
    metadata_filename="3dm_nw.csv",
    url_metadata="https://www.opengeodata.nrw.de/produkte/geobasis/hm/3dm_l_las/3dm_l_las/3dm_meta.zip",
    skiprows=6,
    rewrite_download=True)

meta_img = pd.read_csv("data/dop_nw.csv")
meta_pc = pd.read_csv("data/3dm_nw.csv")

meta_img["coords"] = meta_img["Kachelname"].apply(extract_coords_tilename)
meta_pc["coords"] = meta_pc["Kachelname"].apply(extract_coords_tilename)

meta_img_s = meta_img[['Kachelname', "Aktualitaet", 'coords']]
meta_pc_s = meta_pc[['Kachelname', "Aktualitaet", 'coords']]

meta_img_s.rename(columns={"Aktualitaet": "Aktualitaet_img", "Kachelname": "Kachelname_img"}, inplace=True)
meta_pc_s.rename(columns={"Aktualitaet": "Aktualitaet_pc", "Kachelname": "Kachelname_pc"}, inplace=True)

meta_img_s["Aktualitaet_img"] = meta_img_s["Aktualitaet_img"].str[:-3]

merged = pd.merge(meta_img_s, meta_pc_s, on="coords", how="inner")

# transform to datetime
merged["Aktualitaet_img"] = pd.to_datetime(merged["Aktualitaet_img"], format="%Y-%m-%d")
merged["Aktualitaet_pc"] = pd.to_datetime(merged["Aktualitaet_pc"], format="%Y-%m-%d")

merged["diff"] = abs((merged["Aktualitaet_img"] - merged["Aktualitaet_pc"]).dt.days)

# sort by difference
merged = merged.sort_values(by="diff", ascending=True).reset_index(drop=True)

merged.to_csv(output_file, index=False)

#%% plot histogram of time differences
import matplotlib.pyplot as plt

plt.figure(figsize=(14,5))
avg = merged["diff"].mean()
print(f"Average difference: {avg} days")
max_value = max(list(merged["diff"]))
max_diff = (max_value // 30) + 1
#plot = merged["diff"].dt.days.plot.hist(bins=range(max_diff))
xtick = [i*30 for i in range(max_diff+1)]
plt.hist(merged["diff"], bins=xtick)
plt.xticks(xtick, rotation=75)
plt.xlabel("Days")
plt.ylabel("Tile count")
plt.title(f"Difference in days between collection date of image and pointcloud tiles\n(n={len(merged)}, mean={int(avg)} days)");
plt.axvline(x=avg, color="red", label="mean")
plt.rcParams.update({'font.size': 12})

# %% check difference in dates across tiles
import os
import pandas as pd
import geopandas as gpd

data_dir = "data/all/processed"

gdf = gpd.GeoDataFrame()
for f in os.listdir(data_dir):
    if f.startswith("buildings_metadata"):
        print(f"Found {f}")
        gdf_ = gpd.read_file(f"{data_dir}/{f}")
        gdf = pd.concat([gdf, gdf_])

sub_dirs = next(os.walk(f"{data_dir}/images"))[1]

images = []
for sub_dir in sub_dirs:
    if sub_dir != "check":
        # list all files in sub_dir
        [images.append(f[:-4]) for f in os.listdir(f"{data_dir}/images/{sub_dir}")]

# filter gdf to only include found images
gdf = gdf[gdf["building_id"].isin(images)]

# add time information
all_tiles = pd.read_csv("data/tiles_merged.csv")
gdf = pd.merge(gdf, all_tiles, left_on="kachelname", right_on="Kachelname_img", how="left")

above_2years = gdf[gdf["diff"] > 365*2]

plot = gdf["diff"].plot.hist(bins=100)
