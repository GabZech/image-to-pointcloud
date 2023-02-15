# https://www.bezreg-koeln.nrw.de/brk_internet/geobasis/hoehenmodelle/3d-messdaten/index.html
# https://www.opengeodata.nrw.de/produkte/geobasis/hm/3dm_l_las/3dm_l_las/

#%%
#######################
### GOBAL VARIABLES ###

tile_names = ["3dm_32_375_5666_1_nw", "3dm_32_438_5765_1_nw"] # TEMPORARY
building_types = ["Wohnhaus"] # select building types to keep. All other building types will be removed.
raw_data_folder = "data/raw/pcs/"
processed_data_folder = "data/processed/pcs/"
rewrite_download=False # if True, metadata and tiles will be downloaded again, even if they already exist
rewrite_processing=False # if True, images of individual buildings will be created again, even if they already exist

###############
### IMPORTS ###

from functions_download import download_metadata, prepare_building_data, extract_building_id, read_concat_gdf

import pandas as pd
import geopandas as gpd
import os
import urllib.request
import pdal
import json
import urllib.request

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

    # 1. Download metadata
    metadata_filename = "3dm_nw.csv"

    download_metadata(raw_data_folder,
                    metadata_filename,
                    url_metadata="https://www.opengeodata.nrw.de/produkte/geobasis/hm/3dm_l_las/3dm_l_las/3dm_meta.zip",
                    skiprows = 6,
                    rewrite_download=rewrite_download)

    # read and filter metadata
    metadata = pd.read_csv(raw_data_folder + metadata_filename)
    metadata = metadata[metadata['Kachelname'].isin(tile_names)]
    print(f"Metadata for {len(tile_names)} tiles imported.")

    # 2. Download pointclouds, footprints and building information
    base_url = "https://www.opengeodata.nrw.de/produkte/geobasis/hm/3dm_l_las/3dm_l_las/"
    gdf = gpd.GeoDataFrame()
    files_skipped = 0
    files_processed = 0

    for tile_name in tile_names:

        pc_url = f"{base_url}{tile_name}.laz"
        tile_file = f"{raw_data_folder}{tile_name}.laz"

        # download pointcloud
        if not os.path.exists(tile_file) or rewrite_download:
            urllib.request.urlretrieve(pc_url, tile_file)
            print(f"Downloaded {tile_file}")
        else:
            print(f"File {tile_file} already exists. Skipping download.")

        # download footprint and information of buildings
        gdf_temp = prepare_building_data(tile_name, building_types)
        gdf = read_concat_gdf(gdf, gdf_temp)

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

            files_processed += 1

        else:
            files_skipped += 1

print(f"Processed and saved {files_processed} new files to {processed_data_folder}.\n\
      Skipped creating {files_skipped} already-existing files. Set rewrite=True to overwrite those files.\n")
