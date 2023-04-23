#%%
### GOBAL VARIABLES ###

roof_types = ["Flat Roof", "Saddle Roof", "Tent Roof"]

#directories
run = "all"
data_folder = "data/"
raw_data_folder = f"{data_folder}raw/images/"
processed_metadata_folder = f"{data_folder}{run}/processed/"
processed_data_folder = f"{processed_metadata_folder}pcs/"
processed_imgs_folder = f"{processed_metadata_folder}images/"

#rewrite
rewrite_download=False # if True, metadata and tiles will be downloaded again, even if they already exist
rewrite_processing=False # if True, images of individual buildings will be created again, even if they already exist


### IMPORTS ###

import json
import os
import urllib.request
import shutil

import pdal
import numpy as np
import pandas as pd
import geopandas as gpd

from functions_download import download_metadata, prepare_building_data, create_dirs
from functions_filter import remove_buildings_outside_tile
from functions_process import extract_building_id, extract_coords_tilename, move_to_subfolders, read_metadata


### FUNCTION DEFINITIONS ###

def create_pdal_pipeline(polygon, tile_file):
    """Create pipeline for pdal to crop pointclouds based on polygon"""
    pipeline = {
        "pipeline": [
            {
                "type": "readers.las",
                "filename": tile_file
            },
            {
                "type":"filters.range",
                "limits":"Classification[20:20]" # For classification information, https://www.bezreg-koeln.nrw.de/brk_internet/geobasis/hoehenmodelle/nutzerinformationen.pdf
            },
            {
                "type": "filters.crop",
                "polygon": polygon
            },
            # {
            #     "type":"writers.las",
            #     #"a_srs":"EPSG:25832+7837"
            #     "filename": save_path
            # }
        ]
    }

    return pipeline

#%%

if __name__ == "__main__":

    create_dirs([raw_data_folder, processed_data_folder])

    # 1. Read metadata

    metadata_img = gpd.GeoDataFrame()
    for f in os.listdir(processed_metadata_folder):
        if f.startswith("buildings_metadata"):
            print(f"Found {f}")
            metadata_img_ = gpd.read_file(f"{processed_metadata_folder}/{f}")
            metadata_img = pd.concat([metadata_img, metadata_img_])

    sub_dirs = next(os.walk(f"{processed_metadata_folder}/images"))[1]

    # get list of buildings based on images
    images = []
    for sub_dir in sub_dirs:
        if sub_dir != "check":
            # list all files in sub_dir
            [images.append(f[:-4]) for f in os.listdir(f"{processed_metadata_folder}/images/{sub_dir}")]

    # filter gdf to only include found images
    metadata_img = metadata_img[metadata_img["building_id"].isin(images)]

    tiles_img = metadata_img["kachelname"].unique().tolist()

    metadata_all = pd.read_csv(f"{data_folder}tiles_merged.csv")
    metadata_all = metadata_all[metadata_all["Kachelname_img"].isin(tiles_img)]
    tile_names = metadata_all["Kachelname_pc"].unique().tolist()


    # 2. Download and read pointclouds, footprints and building information
    base_url = "https://www.opengeodata.nrw.de/produkte/geobasis/hm/3dm_l_las/3dm_l_las/"

    # get geodataframe containing info on all buildings in the selected tiles
    skipped_processing = 0

    # get list of buildings for which there are images in processed/images
    saddle_bldgs = [f[:-4] for f in os.listdir(f"{processed_imgs_folder}saddle_roofs/") if f.endswith(".png")]
    tent_bldgs = [f[:-4] for f in os.listdir(f"{processed_imgs_folder}tent_roofs/") if f.endswith(".png")]
    flat_bldgs = [f[:-4] for f in os.listdir(f"{processed_imgs_folder}flat_roofs/") if f.endswith(".png")]
    buildings = saddle_bldgs + tent_bldgs + flat_bldgs

    count_tiles = len(tile_names)

    for tile_name in tile_names:

        pc_url = f"{base_url}{tile_name}.laz"
        tile_file = f"{raw_data_folder}tile_temporary.laz"

        # download pointcloud
        urllib.request.urlretrieve(pc_url, tile_file)

        # download footprint and information of buildings
        coords = extract_coords_tilename(tile_name)
        coords = (coords[0] * 1000, coords[1] * 1000) # multiply by 1000 to get coordinates in meters
        try:
            gdf_temp = prepare_building_data(tile_name, coords)
            gdf_temp = remove_buildings_outside_tile(gdf_temp, coords)
        except ValueError:
            print(f"Could not get building data for tile {tile_name}. Coordinates {coords} likely outside of Germany. Skipping.")

        # keep only buildings for which there are images in processed/images
        gdf_temp["building_id"] = gdf_temp["id"].apply(extract_building_id)
        gdf_temp = gdf_temp[gdf_temp["building_id"].isin(buildings)]

        # 3. Extract pointcloud of individual buildings
        geometries = []
        ids = []

        for index, row in gdf_temp.iterrows():

            building_id = extract_building_id(row.id)
            #tile_file = f"{raw_data_folder}{row.kachelname}.laz"
            geometries.append(str(row.geometry))
            ids.append(building_id)

        pipeline_str = create_pdal_pipeline(geometries, tile_file)
        json_str = json.dumps(pipeline_str)
        pipeline = pdal.Pipeline(json_str)
        pipeline.execute()

        # transform and save pointcloud as json file
        arrays = pipeline.arrays

        for i, array in enumerate(arrays):
            x_array = (array['X']*100).reshape(-1,1).astype(np.int32)
            y_array = (array['Y']*100).reshape(-1,1).astype(np.int32)
            z_array = (array['Z']*100).reshape(-1,1).astype(np.int32)

            new_array = np.concatenate((x_array, y_array, z_array), axis=1)

            json_string = {"building_id": ids[i],
                           "lidar": new_array.tolist(),
                           }

            save_path = f"{processed_data_folder}{ids[i]}.json"

            if not os.path.exists(save_path) or rewrite_processing:
                # write new_array to json file
                with open(save_path, 'w') as outfile:
                    json.dump(json_string, outfile)
            else:
                skipped_processing += 1

        count_tiles -= 1
        print(f"Finished {tile_name}. Remaining tiles: {count_tiles}")

    if skipped_processing > 0:
        print(f"\n{skipped_processing} individual building files already existed and were skipped. Set rewrite_processing=True to overwrite those files.")

    # count number of files in folder
    count_files = len([name for name in os.listdir(processed_data_folder) if os.path.isfile(os.path.join(processed_data_folder, name))])
    print(f"Found {count_files} buildings in {processed_data_folder}")

    # move files to subfolders
    print("Moving files to subfolders...")

    for dir in os.listdir(processed_imgs_folder):
        if dir != "check":
            for file in os.listdir(f"{processed_imgs_folder}/{dir}"):
                building_id = file.split(".")[0]
                try:
                    shutil.move(f"{processed_data_folder}{building_id}.json", f"{processed_data_folder}{dir}/{building_id}.json")
                except FileNotFoundError:
                    try:
                        os.remove(f"{processed_imgs_folder}/{dir}/{building_id}.png")
                    except FileNotFoundError:
                        continue
                    try:
                        os.remove(f"{processed_data_folder}{building_id}.json")
                    except FileNotFoundError:
                        continue

                    print(f"File {building_id}.json not found. Deleted both png and json files.")

    print("Finished.")