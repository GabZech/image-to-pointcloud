#%%
#######################
### GOBAL VARIABLES ###

raw_data_folder = "data/raw/pcs/"
processed_data_folder = "data/processed/pcs/"
rewrite_download=False # if True, metadata and tiles will be downloaded again, even if they already exist
rewrite_processing=False # if True, images of individual buildings will be created again, even if they already exist

###############
### IMPORTS ###

import json
import os
import urllib.request

import pdal
import numpy as np

from functions_download import download_metadata, prepare_building_data, create_dirs
from functions_filter import remove_buildings_outside_tile
from functions_process import extract_building_id, extract_coords_tilename, read_metadata

############################
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
################
### RUN CODE ###

if __name__ == "__main__":

    create_dirs([raw_data_folder, processed_data_folder])

    # 1. Download and read metadata
    metadata_filename = "3dm_nw.csv"

    download_metadata(raw_data_folder,
                    metadata_filename,
                    url_metadata="https://www.opengeodata.nrw.de/produkte/geobasis/hm/3dm_l_las/3dm_l_las/3dm_meta.zip",
                    skiprows = 6,
                    rewrite_download=rewrite_download)

    tile_names = ["3dm_32_375_5666_1_nw", "3dm_32_438_5765_1_nw"] # TEMPORARY
    metadata = read_metadata(tile_names, raw_data_folder, metadata_filename) # TEMPORARY
    # metadata = pd.read_csv("data/raw/images/dop_nw.csv")
    # tile_names = metadata["Kachelname"]

    # 2. Download and read pointclouds, footprints and building information
    base_url = "https://www.opengeodata.nrw.de/produkte/geobasis/hm/3dm_l_las/3dm_l_las/"

    # get geodataframe containing info on all buildings in the selected tiles
    skipped_processing = 0

    # get list of buildings for which there are images in processed/images
    buildings = [f[:-5] for f in os.listdir("data/processed/images/") if f.endswith(".png")]

    count_tiles = len(tile_names)

    for tile_name in tile_names:

        pc_url = f"{base_url}{tile_name}.laz"
        tile_file = f"{raw_data_folder}tile_temporary.laz"

        # download pointcloud
        urllib.request.urlretrieve(pc_url, tile_file)

        # download footprint and information of buildings
        coords = extract_coords_tilename(tile_name)
        coords = (coords[0] * 1000, coords[1] * 1000) # multiply by 1000 to get coordinates in meters
        gdf_temp = prepare_building_data(tile_name, coords)
        gdf_temp = remove_buildings_outside_tile(gdf_temp, coords)

        # keep only buildings for which there are images in processed/images
        gdf_temp["building_id"] = gdf_temp["id"].apply(extract_building_id)
        gdf_temp = gdf_temp[gdf_temp["building_id"].isin(buildings)]
        # gdf = read_concat_gdf(gdf, gdf_temp)

        # 3. Extract pointcloud of individual buildings
        geometries = []
        ids = []

        for index, row in gdf_temp.iterrows():

            building_id = extract_building_id(row.id)
            tile_file = f"{raw_data_folder}{row.kachelname}.laz"
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

print(f"\nDone. Files can be found in {processed_data_folder}.")
