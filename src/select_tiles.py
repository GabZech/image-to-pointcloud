#%%
import pandas as pd

n_samples = 300

# IMAGES

meta_img = pd.read_csv("data/raw/images/dop_nw.csv")

# randomly select n tiles from the meta_img
meta_img_sample = meta_img.sample(n_samples, random_state=42)

meta_img_sample.to_csv("data/processed/tiles_sample_img.csv", index=False)

# %%

# POINTCLOUDS

from functions_process import extract_coords_tilename

tiles_img = meta_img_sample["Kachelname"].tolist()
meta_pc = pd.read_csv("data/raw/pcs/3dm_nw.csv")
tiles_pc_all = meta_pc["Kachelname"].tolist()

meta_pc_sample = pd.DataFrame()
coords = list(map(extract_coords_tilename, tiles_img))
for i in range(len(coords)):
    x, y = coords[i][0], coords[i][1]
    tile = meta_pc[meta_pc["Kachelname"].str.contains(f"{x}_{y}")]
    meta_pc_sample = pd.concat([meta_pc_sample, tile])
    # for tile in tiles_pc_all:
    #     if f"{x}_{y}" in tile:
    #         tiles_pc.append(tile)

meta_pc_sample.to_csv("data/processed/tiles_sample_pcs.csv", index=False)


# %%
