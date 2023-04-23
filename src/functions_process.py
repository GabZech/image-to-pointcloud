import os
import re
import shutil

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


def move_to_subfolders(gdf, roof_types, processed_data_folder, format):
    """Moves files to subfolders based on roof type

    Args:
        gdf (gpd.GeoDataFrame): geodataframe containing building data
        roof_types (list): list of roof types
        processed_data_folder (str): path to processed data folder
        format (str): file format

    Returns:
        None
    """
    for type in roof_types:
        roof_dir = f"{processed_data_folder}{type}/"
        create_dirs([roof_dir])

        length = len(format)

        for file in os.listdir(processed_data_folder):
            if file.endswith(format):
                try:
                    if file[:-length] in gdf[gdf["roofType"] == type].building_id.to_list():
                        shutil.move(f"{processed_data_folder}{file}", roof_dir)
                except Exception as e:
                    print(f"Could not move file {file} to subfolder ({e})")