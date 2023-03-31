#%%
### GOBAL VARIABLES ###

# filters
building_types = ["Wohnhaus", "Wohngebäude mit Handel und Dienstleistungen", "Wohn- und Geschäftsgebäude"] # select building types to keep. All other building types will be removed.
#roof_types = ["Saddle Roof", "Tent Roof", "Flat Roof"]
dormer_count = 0 # number of dormers that a building must have to be kept.
#roof_surface_counts = [1, 2, 4]
has_solar = False
min_area = 100 # area (in square meters) of buildings that will be kept. Buildings with smaller area will be removed.

# directories
run = "run2"
data_folder = "D:/thesis/data/"
raw_data_folder = f"{data_folder}raw/images/"
processed_metadata_folder = f"{data_folder}{run}/processed/"
processed_data_folder = f"{processed_metadata_folder}images/"

# rewrite
rewrite_download=False # if True, metadata and tiles will be downloaded again, even if they already exist
rewrite_processing=True # if True, images of individual buildings will be created again, even if they already exist

name_id_only = True # if True, only the building id will be used when saving the image name. If False, the building id and the building type will be used as image name.


### IMPORTS ###

import os
import shutil

import geopandas as gpd
import pandas as pd
import rasterio
from rasterio.mask import mask
import numpy as np
#import cv2

from functions_download import download_metadata, prepare_building_data, create_dirs, get_credium_metadata
from functions_filter import filter_buildings, remove_buildings_outside_tile
from functions_process import extract_building_id, extract_coords_tilename, read_concat_gdf, move_to_subfolders, read_metadata
from creds import sub_key


### FUNCTION DEFINITIONS ###

def read_convert_save_tile(tile_name, base_url, save_folder) -> None:
    """Reads, converts and saves tile images as png

    Args:
        tile_names (list): list of tile names
        base_url (str): base url of images
        save_folder (str): path to folder where images will be saved
        rewrite (bool, optional): if True, images will be downloaded again, even if they already exist. Defaults to False.

    Returns:
        None
    """

    img_url = f"{base_url}{tile_name}.jp2"
    save_path = f"{save_folder}tile_temporary.tiff"

    # read image

    with rasterio.open(img_url, "r") as src:

        # keep only RGB channels
        img_rgb = src.read([1,2,3])

        profile = src.profile
        profile.update(count=3, driver='GTiff')

        # save image as png
        with rasterio.open(save_path, 'w', **profile) as dst:
            dst.write(img_rgb)

def create_mask_from_shape(img, shape, crop=True, pad=False):
    """Create mask of a building from shapefile

    Args:
        img (numpy.ndarray): image to be masked
        shape (gpd.GeoDataFrame): geodataframe containing building shapes
        crop (bool, optional): crop mask according to its bbox. Defaults to True.
        pad (bool, optional): pad mask by half a pixel. Defaults to False.

    Returns:
        tuple[numpy.ndarray, dict]: masked image and metadata
    """
    out_image, out_transform = mask(img, shape, crop=crop, pad=pad)
    out_meta = img.meta

    out_meta.update({
        "height": out_image.shape[1],
        "width": out_image.shape[2],
        "transform": out_transform})

    return out_image, out_meta


def extract_individual_buildings(gdf, src_images_folder, dst_images_folder, rewrite=False, name_id_only=True):
    """Extract and save images of individual buildings from image tiles

        Args:
            tile_names (list[str]): list of image names
            gdf (gpd.GeoDataFrame): geodataframe containing building shapes
            src_images_folder (str): path to source image folder
            dst_images_folder (str): path to destination image folder
            rewrite (bool, optional): rewrite existing files. Defaults to False.

        Returns:
            None
    """
    # create empty list to store existing files that were not rewritten
    skipped_processing = 0
    above_224 = 0

    tile_path = f"{src_images_folder}tile_temporary.tiff"

    # open image
    with rasterio.open(tile_path, "r") as src:
        assert src.crs == gdf.crs # check if crs of image and gdf are the same
        # subset gdf to buildings on the current tile
        gdf_temp = gdf[gdf["kachelname"] == tile_name]

        for index, row in gdf_temp.iterrows():

            building_id = extract_building_id(row["id"])

            if name_id_only:
                filename = f"{dst_images_folder}{building_id}.png"
            else:
                # lowercase, remove spaces and special characters from building function
                building_function = row["funktion"].lower().replace(" ", "_").replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
                filename = f"{dst_images_folder}{building_function}_{building_id}.png"

            if not os.path.exists(filename) or rewrite:
                # create mask for building
                out_image, out_meta = create_mask_from_shape(src, [row["geometry"]], crop=True, pad=True)

                if out_image.shape[1] <= 224 and out_image.shape[2] <= 224: # filters out images that have a dimension smaller than 224 pixels
                    # pad image to 224x224
                    extra_left, extra_right, extra_top, extra_bottom = get_padding_dim(out_image)
                    out_image = np.pad(out_image, ((0, 0), (extra_top, extra_bottom), (extra_left, extra_right)), mode='constant', constant_values=0)
                    out_meta.update({"height": 224, "width": 224})
                    with rasterio.open(filename, "w", **out_meta) as dest:
                        dest.write(out_image)
                else:
                    above_224 += 1
            else:
                skipped_processing += 1

    if skipped_processing > 0:
        print(f"{skipped_processing} individual building images already existed in {dst_images_folder} and were skipped. Set rewrite_processing=True to overwrite those files.")

    return above_224

def get_padding_dim(img):

    remaining_rows, remaining_cols = 224 - img.shape[1], 224 - img.shape[2]

    if remaining_cols % 2 == 0 and remaining_cols != 1:
        extra_left, extra_right = remaining_cols // 2, remaining_cols // 2
    elif remaining_cols == 1:
        extra_left, extra_right = 0 , 1
    else:
        extra_left, extra_right = remaining_cols // 2, remaining_cols // 2 + 1

    if remaining_rows % 2 == 0 and remaining_rows != 1:
        extra_top, extra_bottom = remaining_rows // 2, remaining_rows // 2
    elif remaining_rows == 1:
        extra_top, extra_bottom = 0, 1
    else:
        extra_top, extra_bottom = remaining_rows // 2, remaining_rows // 2 + 1

    return extra_left, extra_right, extra_top, extra_bottom

#%%
### RUN CODE ###

if __name__ == "__main__":

    create_dirs([raw_data_folder, processed_data_folder])

    # 1. Download and read metadata
    #metadata_filename = "dop_nw.csv"

    # download_metadata(raw_data_folder,
    #                 metadata_filename,
    #                 url_metadata="https://www.opengeodata.nrw.de/produkte/geobasis/lusat/dop/dop_jp2_f10/dop_meta.zip",
    #                 skiprows=5,
    #                 rewrite_download=rewrite_download)
    # tile_names = ["dop10rgbi_32_375_5666_1_nw_2021", "dop10rgbi_32_438_5765_1_nw_2022"] # TEMPORARY
    # metadata = read_metadata(tile_names, raw_data_folder, metadata_filename) # TEMPORARY

    metadata = pd.read_csv(f"{data_folder}tiles_sample_img.csv")
    tile_names = metadata["Kachelname"][1:5]

    # 2. Download and read images, footprints and building information
    gdf = gpd.GeoDataFrame()

    for tile_name in tile_names:

        # read_convert_save_tile(tile_name, base_url, raw_data_folder, rewrite=rewrite_download)

        # download footprint and information of buildings
        coords = extract_coords_tilename(tile_name)
        coords = (coords[0] * 1000, coords[1] * 1000) # multiply by 1000 to get coordinates in meters
        try:
            gdf_temp = prepare_building_data(tile_name, coords)
            gdf_temp = remove_buildings_outside_tile(gdf_temp, coords)
            gdf = read_concat_gdf(gdf, gdf_temp)
        except ValueError:
            print(f"Could not get building data for tile {tile_name}. Coordinates {coords} likely outside of Germany. Skipping.")

    # filter out buildings that are not of interest
    gdf = filter_buildings(gdf, type=building_types, min_area=min_area)

    # create a list of gml_ids with last 2 characters removed
    gml_ids = [gml_id[:-2] for gml_id in gdf["gml_id"]]
    gdf["gml_id"] = gml_ids

    count = len(gml_ids)
    range = list(range(0, count, 50))

    # iterate over gml_ids and append dataframes to dfs list
    dfs = []
    for gml_id in gml_ids:
        df_single = get_credium_metadata(gml_id, sub_key)
        dfs.append(df_single)
        count -= 1
        if count in range:
            print(f"Remaining buildings: {count}")
    # concatenate all dataframes in dfs list into a single dataframe
    gdf_credium = pd.concat(dfs, ignore_index=True)

    gdf = gdf.merge(gdf_credium, left_on="gml_id", right_on="buildingId", how='left')

    gdf["building_id"] = gdf["id"].apply(extract_building_id)

    # apply further filters based on credium data
    gdf = gdf[gdf["hasSolar"] == has_solar]
    gdf = gdf[gdf["dormerCount"] == dormer_count]
    gdf_saddle = gdf[(gdf["roofType"] == "Saddle Roof") & (gdf["roofSurfaceCount"] == 2)]
    gdf_tent = gdf[(gdf["roofType"] == "Tent Roof") & (gdf["roofSurfaceCount"] == 4)]
    gdf_flat = gdf[(gdf["roofType"] == "Flat Roof") & (gdf["roofSurfaceCount"] == 1)]
    gdf = pd.concat([gdf_saddle, gdf_tent, gdf_flat], ignore_index=True)

    # save metadata to file
    gdf_filename = f"{processed_metadata_folder}buildings_metadata.json"
    gdf["roofSurfaces"] = gdf["roofSurfaces"].astype(str)
    gdf.to_file(gdf_filename, driver="GeoJSON")

    print(f"\nFound {len(gdf)} buildings to be processed. Saved metadata to {gdf_filename}")

#%%
if __name__ == "__main__":
    # 3. Extract images of individual buildings
    base_url = "https://www.opengeodata.nrw.de/produkte/geobasis/lusat/dop/dop_jp2_f10/"

    #gdf = gpd.read_file(gdf_filename)

    count_tiles = len(tile_names)
    count_excluded = 0

    for tile_name in tile_names:
        try:
            read_convert_save_tile(tile_name, base_url, raw_data_folder)
            above_224 = extract_individual_buildings(gdf, raw_data_folder, processed_data_folder, rewrite=rewrite_processing, name_id_only=name_id_only)
            count_excluded += above_224
        except Exception as e: # if the tile could not be downloaded, skip it
            print(f"Could not download tile {tile_name}. Error: {e}.")
            count_tiles -= 1
            continue
        count_tiles -= 1
        print(f"Finished {tile_name}. Remaining tiles: {count_tiles}")

    print(f"\n{count_excluded} buildings were removed because they had one or more dimensions larger than 224 pixels.")

    # count number of files in folder
    count_files = len([name for name in os.listdir(processed_data_folder) if os.path.isfile(os.path.join(processed_data_folder, name))])
    print(f"Found {count_files} buildings in {processed_data_folder}")

    # move files to subfolders
    print("Moving files to subfolders...")
    move_to_subfolders(gdf, processed_data_folder)

    print("Finished.")


# %%
