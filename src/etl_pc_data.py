#%%
#######################
### GOBAL VARIABLES ###

tile_names = ["3dm_32_375_5666_1_nw", "3dm_32_438_5765_1_nw"] # TEMPORARY
building_types = ["Wohnhaus"] # select building types to keep. All other building types will be removed.
min_area = 100 # area (in square meters) of buildings that will be kept. Buildings with smaller area will be removed.
raw_data_folder = "data/raw/pcs/"
processed_data_folder = "data/processed/pcs/"
rewrite_download=False # if True, metadata and tiles will be downloaded again, even if they already exist
rewrite_processing=False # if True, images of individual buildings will be created again, even if they already exist

###############
### IMPORTS ###

import json
import os
import urllib.request

import geopandas as gpd
import pdal

from functions_download import download_metadata, prepare_building_data
from functions_filter import filter_buildings, remove_buildings_outside_tile
from functions_process import extract_building_id, extract_coords_tilename, read_concat_gdf, read_metadata

############################
### FUNCTION DEFINITIONS ###

def create_pdal_pipeline(polygon, tile_file, save_path):
    """Create pipeline for pdal to crop pointclouds based on polygon"""
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

    # 1. Download and read metadata
    metadata_filename = "3dm_nw.csv"

    download_metadata(raw_data_folder,
                    metadata_filename,
                    url_metadata="https://www.opengeodata.nrw.de/produkte/geobasis/hm/3dm_l_las/3dm_l_las/3dm_meta.zip",
                    skiprows = 6,
                    rewrite_download=rewrite_download)

    metadata = read_metadata(tile_names, raw_data_folder, metadata_filename)

    # 2. Download and read pointclouds, footprints and building information
    base_url = "https://www.opengeodata.nrw.de/produkte/geobasis/hm/3dm_l_las/3dm_l_las/"

    # get geodataframe containing info on all buildings in the selected tiles
    gdf = gpd.GeoDataFrame()
    skipped_download = 0
    skipped_processing = 0

    for tile_name in tile_names:

        pc_url = f"{base_url}{tile_name}.laz"
        tile_file = f"{raw_data_folder}{tile_name}.laz"

        # download pointcloud
        if not os.path.exists(tile_file) or rewrite_download:
            urllib.request.urlretrieve(pc_url, tile_file)
            print(f"Downloaded {tile_file}")
        else:
            skipped_download += 1

        # download footprint and information of buildings
        coords = extract_coords_tilename(tile_name)
        coords = (coords[0] * 1000, coords[1] * 1000) # multiply by 1000 to get coordinates in meters
        gdf_temp = prepare_building_data(tile_name, coords)
        gdf_temp = remove_buildings_outside_tile(gdf_temp, coords)
        gdf = read_concat_gdf(gdf, gdf_temp)

    if skipped_download > 0:
        print(f"{skipped_download} tiles already existed and were skipped. Set rewrite_download=True to overwrite those files.")

    # filter out buildings that are not of interest
    gdf = filter_buildings(gdf, type=building_types, min_area=min_area)

    print(f"Found {len(gdf)} buildings to be processed.\n")

    # 3. Extract pointcloud of individual buildings
    for index, row in gdf.iterrows():

        # get building id and file save path
        building_id = extract_building_id(row.id)
        save_path = f"{processed_data_folder}{building_id}.las"

        if not os.path.exists(save_path) or rewrite_processing:

            # extract pointcloud for single building
            tile_file = f"{raw_data_folder}{row.kachelname}.laz"
            pipeline_str = create_pdal_pipeline(row.geometry.wkt, tile_file, save_path)
            json_str = json.dumps(pipeline_str)
            pipeline = pdal.Pipeline(json_str)
            pipeline.execute()

        else:
            skipped_processing += 1

if skipped_processing > 0:
    print(f"{skipped_processing} individual building files already existed and were skipped. Set rewrite_processing=True to overwrite those files.")

print(f"\nDone. Files can be found in {processed_data_folder}.")