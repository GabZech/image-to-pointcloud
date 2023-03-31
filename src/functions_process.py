import re
import shutil
import os

import geopandas as gpd
import pandas as pd

from functions_download import create_dirs


def read_metadata(tile_names, raw_data_folder, metadata_filename):
    """Reads metadata from csv file

    Args:
        tile_names (list): list of tile names
        raw_data_folder (str): path to folder where metadata is saved
        metadata_filename (str): name of metadata file

    Returns:
        pd.DataFrame: metadata
    """
    metadata = pd.read_csv(raw_data_folder + metadata_filename)
    metadata = metadata[metadata['Kachelname'].isin(tile_names)]
    print(f"Metadata for {len(tile_names)} tiles imported.")

    return metadata


def extract_coords_tilename(string):
    """Extract coordinates from tile name in format x_x_lat_long..."""
    match = re.search(r'\d+_(\d+)_(\d+)', string)
    return (int(match.group(1)), int(match.group(2)))


def read_concat_gdf(gdf1, gdf2) -> gpd.GeoDataFrame:
    """Read and concatenate two geodataframes

    Args:
        gdf1 (gpd.GeoDataFrame): first geodataframe
        gdf2 (gpd.GeoDataFrame): second geodataframe

    Returns:
        gpd.GeoDataFrame: concatenated geodataframe
    """
    gdf_temp = pd.concat([gdf1, gdf2])
    gdf_temp.drop_duplicates(keep="first", inplace=True)
    gdf_temp.reset_index(drop=True, inplace=True)

    return gdf_temp


def extract_building_id(input_string) -> str:
    """Extract building id from string

    Args:
        input_string (str): input string containing building id in the format "gebbau.id.334050178.geometrie.Geom_0"

    Returns:
        str: the building id
    """
    pattern = re.compile(r'\w+\.id\.(\d+)\.\w+\.(\w+)_(\d+)')
    match = pattern.search(input_string)
    if match:
        #return match.group(1) + '_' + match.group(2)
        return match.group(1)
    else:
        return


def move_to_subfolders(gdf, processed_data_folder):

    saddle_roofs = gdf[gdf["roofType"] == "Saddle Roof"].building_id.to_list()
    tent_roofs = gdf[gdf["roofType"] == "Tent Roof"].building_id.to_list()
    flat_roofs = gdf[gdf["roofType"] == "Flat Roof"].building_id.to_list()

    saddle_dir = f"{processed_data_folder}saddle_roofs/"
    tent_dir = f"{processed_data_folder}tent_roofs/"
    flat_dir = f"{processed_data_folder}flat_roofs/"

    create_dirs([saddle_dir, tent_dir, flat_dir])

    for file in os.listdir(processed_data_folder):
        if file.endswith(".png"):
            if file[:-4] in saddle_roofs:
                shutil.move(f"{processed_data_folder}{file}", f"{saddle_dir}{file}")
            elif file[:-4] in tent_roofs:
                shutil.move(f"{processed_data_folder}{file}", f"{tent_dir}{file}")
            elif file[:-4] in flat_roofs:
                shutil.move(f"{processed_data_folder}{file}", f"{flat_roofs}{file}")
            else:
                print(f"Could not move file {file} to subfolder.")