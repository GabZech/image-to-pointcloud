# https://www.bezreg-koeln.nrw.de/brk_internet/geobasis/hoehenmodelle/3d-messdaten/index.html
# https://www.opengeodata.nrw.de/produkte/geobasis/hm/3dm_l_las/3dm_l_las/

#%%
#######################
### GOBAL VARIABLES ###

number_of_tiles = 2 # number of 1kx1k image tiles to download. Use "all" to download all available images
raw_data_folder = "data/raw/pcs/"
processed_data_folder = "data/processed/pcs/"
rewrite_download=False # if True, metadata and tiles will be downloaded again, even if they already exist
rewrite_processing=False # if True, images of individual buildings will be created again, even if they already exist

###############
### IMPORTS ###

from etl_img_data import download_metadata, read_metadata, get_building_data, read_concat_gdf, extract_building_id
import re
import geopandas as gpd
import os
import urllib.request
import pdal
import json

import urllib.request

############################
### FUNCTION DEFINITIONS ###

def extract_coords(string):
    """Extract coordinates from string"""
    match = re.search(r'\d+_(\d+)_(\d+)', string)
    return (int(match.group(1)), int(match.group(2)))

def download_pointclouds(tile_names, base_url, save_folder, rewrite=False):
    """Download pointclouds from tile names"""
    for tile_name in tile_names:
        pc_url = f"{base_url}{tile_name}.laz"
        save_path = f"{save_folder}{tile_name}.laz"

        if not os.path.exists(save_path) or rewrite:
                urllib.request.urlretrieve(pc_url, save_path)
                print(f"Downloaded {save_path}.")
        else:
            print(f"File {save_path} already exists. Skipping download.")

def create_pc_pipeline(polygon, tile_file, save_path):

    pipeline = {
        "pipeline": [
            {
                "type": "readers.las",
                "filename": tile_file
            },
            {
                "type": "filters.crop",
                "polygon": polygon
            },
            {
                "type":"writers.las",
                #"a_srs":"EPSG:25832+7837"
                "filename": save_path
            }
        ]
    }

    return pipeline

#%%

################
### RUN CODE ###


if __name__ == "__main__":

    # 1. Download metadata
    metadata_filename = "3dm_nw.csv"

    download_metadata(raw_data_folder,
                    metadata_filename,
                    url_metadata="https://www.opengeodata.nrw.de/produkte/geobasis/hm/3dm_l_las/3dm_l_las/3dm_meta.zip",
                    skiprows = 6,
                    rewrite_download=rewrite_download)

    tile_names = ["3dm_32_375_5666_1_nw"] # TEMPORARY
    #metadata, tile_names = read_metadata(raw_data_folder, metadata_filename, number_of_tiles)
    print(f"Metadata for {len(tile_names)} tiles imported.")

    # 2. Download pointclouds, footprints and building information
    base_url = "https://www.opengeodata.nrw.de/produkte/geobasis/hm/3dm_l_las/3dm_l_las/"
    gdf = gpd.GeoDataFrame()
    files_skipped = 0
    files_processed = 0

    for tile_name in tile_names:

        pc_url = f"{base_url}{tile_name}.laz"
        tile_file = f"{raw_data_folder}{tile_name}.laz"

        # 2. Download pointclouds
        if not os.path.exists(tile_file) or rewrite_download:
            urllib.request.urlretrieve(pc_url, tile_file)
            print(f"Downloaded {tile_file}")
        else:
            print(f"File {tile_file} already exists. Skipping download.")

        # 3. Download footprint and information of buildings
        gdf_temp = get_building_data((375000,5666000), crs='EPSG:25832') # TEMPORARY
        gdf_temp["kachelname"] = tile_name # TEMPORARY
        gdf = read_concat_gdf(gdf, gdf_temp) # TEMPORARY

        # try:
        #     coords = extract_coords(tile_name)
        #     # multiply by 1000 to get coordinates in meters
        #     coords = (coords[0] * 1000, coords[1] * 1000)
        #     gdf_temp = get_building_data(coords, crs='EPSG:25832')
        #     gdf_temp["kachelname"] = tile_name
        #     gdf = read_concat_gdf(gdf, gdf_temp)
        # except ValueError:
        #     print(f"Could not get building data for tile {tile_name}. Coordinates {coords} likely outside of Germany. Skipping.")
    print(f"Found {len(gdf)} buildings to be processed.\n")

    # 3. Extract pointcloud of individual buildings
    for index, row in gdf.iterrows():

        # get building id and file save path
        building_id = extract_building_id(row.id)
        save_path = f"{processed_data_folder}{building_id}.las"

        if not os.path.exists(save_path) or rewrite_processing:

            # extract pointcloud for single building
            tile_file = f"{raw_data_folder}{row.kachelname}.laz"
            pipeline_str = create_pc_pipeline(row.geometry.wkt, tile_file, save_path)
            json_str = json.dumps(pipeline_str)
            pipeline = pdal.Pipeline(json_str)
            pipeline.execute()

            files_processed += 1

        else:
            files_skipped += 1

print(f"Processed and saved {files_processed} new files to {processed_data_folder}.\n\
      Skipped creating {files_skipped} already-existing files. Set rewrite=True to overwrite those files.\n")
