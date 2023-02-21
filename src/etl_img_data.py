#%%
#######################
### GOBAL VARIABLES ###

tile_names = ["dop10rgbi_32_375_5666_1_nw_2021", "dop10rgbi_32_438_5765_1_nw_2022"] # TEMPORARY
building_types = ["Wohnhaus"] # select building types to keep. All other building types will be removed.
min_area = 100 # area (in square meters) of buildings that will be kept. Buildings with smaller area will be removed.
raw_data_folder = "data/raw/images/"
processed_images_folder = "data/processed/images/"
rewrite_download=False # if True, metadata and tiles will be downloaded again, even if they already exist
rewrite_processing=True # if True, images of individual buildings will be created again, even if they already exist

name_id_only = True # if True, only the building id will be used when saving the image name. If False, the building id and the building type will be used as image name.

###############
### IMPORTS ###

from functions_download import download_metadata, prepare_building_data, extract_building_id, read_concat_gdf, extract_coords_tilename
from functions_filter import filter_buildings, remove_buildings_outside_tile

import os
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask
import shapely


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
            print(f"File {save_path} already exists. Skipping download.")


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
    existing_files = []

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
                    with rasterio.open(filename, "w", **out_meta) as dest:
                        dest.write(out_image)
                else:
                    existing_files.append(building_id)

    if len(existing_files) > 0:
        print(f"Skipped creating {len(existing_files)} already-existing files. Set rewrite=True to overwrite those files.\n")

#%%
################
### RUN CODE ###

if __name__ == "__main__":

    # Download metadata if not already in data/raw/images
    metadata_filename = "dop_nw.csv"

    download_metadata(raw_data_folder,
                    metadata_filename,
                    url_metadata="https://www.opengeodata.nrw.de/produkte/geobasis/lusat/dop/dop_jp2_f10/dop_meta.zip",
                    skiprows=5,
                    rewrite_download=rewrite_download)

    # read and filter metadata
    metadata = pd.read_csv(raw_data_folder + metadata_filename)
    metadata = metadata[metadata['Kachelname'].isin(tile_names)]
    print(f"Metadata for {len(tile_names)} tiles imported.")

    # read image tiles from API, convert and save them as .tiff
    base_url = "https://www.opengeodata.nrw.de/produkte/geobasis/lusat/dop/dop_jp2_f10/"
    read_convert_save_tiles(tile_names, base_url, raw_data_folder, rewrite=rewrite_download)

    # get geodataframe containing the shapes of all buildings in the selected tiles
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

    print(f"Found {len(gdf)} buildings to be processed.\n")

    # create single image for each building
    extract_individual_buildings(tile_names, gdf, raw_data_folder, processed_images_folder, rewrite=rewrite_processing, name_id_only=name_id_only)

# %%
