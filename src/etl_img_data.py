#%%
#######################
### GOBAL VARIABLES ###

tile_names = ["dop10rgbi_32_375_5666_1_nw_2021", "dop10rgbi_32_438_5765_1_nw_2022"] # TEMPORARY
building_types = ["Wohnhaus"] # select building types to keep. All other building types will be removed.
min_area = 100 # area (in square meters) of buildings that will be kept. Buildings with smaller area will be removed.
raw_data_folder = "data/raw/images/"
processed_data_folder = "data/processed/images/"
rewrite_download=False # if True, metadata and tiles will be downloaded again, even if they already exist
rewrite_processing=True # if True, images of individual buildings will be created again, even if they already exist

name_id_only = True # if True, only the building id will be used when saving the image name. If False, the building id and the building type will be used as image name.

###############
### IMPORTS ###

import os

import geopandas as gpd
import rasterio
from rasterio.mask import mask
import numpy as np

from functions_download import download_metadata, prepare_building_data
from functions_filter import filter_buildings, remove_buildings_outside_tile
from functions_process import extract_building_id, extract_coords_tilename, read_concat_gdf, read_metadata

############################
### FUNCTION DEFINITIONS ###

def read_convert_save_tiles(tile_names, base_url, save_folder, rewrite=False) -> None:
    """Reads, converts and saves tile images as tiff

    Args:
        tile_names (list): list of tile names
        base_url (str): base url of images
        save_folder (str): path to folder where images will be saved
        rewrite (bool, optional): if True, images will be downloaded again, even if they already exist. Defaults to False.

    Returns:
        None
    """
    skipped_download = 0

    for tile_name in tile_names:
        img_url = f"{base_url}{tile_name}.jp2"
        save_path = f"{save_folder}{tile_name}.tiff"

        # read image
        if not os.path.exists(save_path) or rewrite:
            with rasterio.open(img_url, "r") as src:

                profile = src.profile
                profile.update(count=3, driver='GTiff')

                # keep only RGB channels
                img_rgb = src.read([1,2,3])

                # save image as tiff
                with rasterio.open(save_path, 'w', **profile) as dst:
                    dst.write(img_rgb)
                    print(f"Downloaded {save_path}")
        else:
            skipped_download += 1

    if skipped_download > 0:
        print(f"{skipped_download} tiles already existed and were skipped. Set rewrite_download=True to overwrite those files.")


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


def extract_individual_buildings(tile_names, gdf, src_images_folder, dst_images_folder, rewrite=False, name_id_only=True):
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

    for tile_name in tile_names:
        image_path = src_images_folder + tile_name + ".tiff"

        # open image
        with rasterio.open(image_path, "r") as src:
            assert src.crs == gdf.crs # check if crs of image and gdf are the same
            # subset gdf to buildings on the current tile
            gdf_temp = gdf[gdf["kachelname"] == tile_name]

            for index, row in gdf_temp.iterrows():

                building_id = extract_building_id(row["id"])

                if name_id_only:
                    filename = f"{dst_images_folder}{building_id}.tiff"
                else:
                    # lowercase, remove spaces and special characters from building function
                    building_function = row["funktion"].lower().replace(" ", "_").replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
                    filename = f"{dst_images_folder}{building_function}_{building_id}.tiff"

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
        print(f"{skipped_processing} individual building files already existed and were skipped. Set rewrite_processing=True to overwrite those files.")

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
################
### RUN CODE ###

if __name__ == "__main__":

    # 1. Download and read metadata
    metadata_filename = "dop_nw.csv"

    download_metadata(raw_data_folder,
                    metadata_filename,
                    url_metadata="https://www.opengeodata.nrw.de/produkte/geobasis/lusat/dop/dop_jp2_f10/dop_meta.zip",
                    skiprows=5,
                    rewrite_download=rewrite_download)

    # read and filter metadata
    metadata = read_metadata(tile_names, raw_data_folder, metadata_filename)

    # 2. Download and read images, footprints and building information
    base_url = "https://www.opengeodata.nrw.de/produkte/geobasis/lusat/dop/dop_jp2_f10/"
    # read image tiles from API, convert and save them as .tiff
    read_convert_save_tiles(tile_names, base_url, raw_data_folder, rewrite=rewrite_download)

    # get geodataframe containing info on all buildings in the selected tiles
    gdf = gpd.GeoDataFrame()

    for tile_name in tile_names:

        # download footprint and information of buildings
        coords = extract_coords_tilename(tile_name)
        coords = (coords[0] * 1000, coords[1] * 1000) # multiply by 1000 to get coordinates in meters
        gdf_temp = prepare_building_data(tile_name, coords)
        gdf_temp = remove_buildings_outside_tile(gdf_temp, coords)
        gdf = read_concat_gdf(gdf, gdf_temp)

    # filter out buildings that are not of interest
    gdf = filter_buildings(gdf, type=building_types, min_area=min_area)

    print(f"Found {len(gdf)} buildings to be processed.")

    # 3. Extract images of individual buildings
    above_224 = extract_individual_buildings(tile_names, gdf, raw_data_folder, processed_data_folder, rewrite=rewrite_processing, name_id_only=name_id_only)

    print(f"\nDone. Files can be found in {processed_data_folder}.")
    print(f"\n{above_224} buildings were removed because they had one or more dimensions larger than 224 pixels.")
