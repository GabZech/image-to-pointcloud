# #%%
# import pandas as pd

# n_samples = 300

# # IMAGES

# meta_img = pd.read_csv("data/raw/images/dop_nw.csv")

# # randomly select n tiles from the meta_img
# meta_img_sample = meta_img.sample(n_samples, random_state=41)

# meta_img_sample.to_csv("data/tiles_sample_img.csv", index=False)

# # %%

# # POINTCLOUDS

# from functions_process import extract_coords_tilename

# tiles_img = meta_img_sample["Kachelname"].tolist()
# meta_pc = pd.read_csv("data/raw/pcs/3dm_nw.csv")
# tiles_pc_all = meta_pc["Kachelname"].tolist()

# meta_pc_sample = pd.DataFrame()
# coords = list(map(extract_coords_tilename, tiles_img))
# for i in range(len(coords)):
#     x, y = coords[i][0], coords[i][1]
#     tile = meta_pc[meta_pc["Kachelname"].str.contains(f"{x}_{y}")]
#     meta_pc_sample = pd.concat([meta_pc_sample, tile])
#     # for tile in tiles_pc_all:
#     #     if f"{x}_{y}" in tile:
#     #         tiles_pc.append(tile)

# meta_pc_sample.to_csv("data/processed/tiles_sample_pcs.csv", index=False)


# %%

import pandas as pd

from functions_download import download_metadata
from functions_process import extract_coords_tilename

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

meta_img = pd.read_csv("data/raw/images/dop_nw.csv")
meta_pc = pd.read_csv("data/raw/pcs/3dm_nw.csv")

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

merged["diff"] = abs(merged["Aktualitaet_img"] - merged["Aktualitaet_pc"])

# sort by difference
merged = merged.sort_values(by="diff", ascending=True).reset_index(drop=True)

merged.to_csv("data/tiles_merged.csv", index=False)

#%%
import matplotlib.pyplot as plt

plt.figure(figsize=(14,5))
avg = merged["diff"].mean()
print(f"Average difference: {avg} days")
max_value = max(list(merged["diff"].dt.days))
max_diff = (max_value // 30) + 1
#plot = merged["diff"].dt.days.plot.hist(bins=range(max_diff))
xtick = [i*30 for i in range(max_diff+1)]
plt.hist(merged["diff"].dt.days, bins=xtick)
plt.xticks(xtick, rotation=75)
plt.xlabel("Days")
plt.ylabel("Tile count")
plt.title(f"Difference in days between collection date of image and pointcloud tiles\n(n={len(merged)}, mean={avg.days} days)");
plt.axvline(x=merged["diff"].dt.days.mean(), color="red", label="mean")
plt.rcParams.update({'font.size': 12})

# %%
