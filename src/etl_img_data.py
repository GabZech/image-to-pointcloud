#######################
### GOBAL VARIABLES ###

number_of_imgs = 2 # number of 1kx1k image tiles to download. Use "all" to download all available images
raw_images_folder = "data/raw/images/"
processed_images_folder = "data/processed/images/"
rewrite_download=False # if True, metadata and tiles will be downloaded again, even if they already exist
rewrite_processing=True # if True, images of individual buildings will be created again, even if they already exist

###############
### IMPORTS ###

import os
import urllib.request
from io import BytesIO
from zipfile import ZipFile
import pandas as pd
import geopandas as gpd
import rasterio
import xml.etree.ElementTree as ET
import geopandas as gpd
import shapely
from rasterio.mask import mask
import re
from typing import Tuple

############################
### FUNCTION DEFINITIONS ###

def read_metadata(raw_images_folder, metadata_filename, number_of_imgs) -> Tuple[pd.DataFrame, list]:
    """Reads metadata from csv file

    Args:
        raw_images_folder (str): path to folder containing metadata
        metadata_filename (str): filename of metadata file
        number_of_imgs (int): number of images to download. Use "all" to download all available images

    Returns:
        tuple[pd.DataFrame, list]: metadata as pandas dataframe and list of image names
    """
    metadata = pd.read_csv(raw_images_folder + metadata_filename)

    # select metadata for subset of images
    if number_of_imgs == "all":
        img_names = list(metadata['Kachelname'].values)
    else:
        img_names = list(metadata['Kachelname'].values[:number_of_imgs])
        metadata = metadata[metadata['Kachelname'].isin(img_names)]

    return metadata, img_names

def read_convert_save_images(img_names, base_url, save_folder, rewrite=False) -> None:
    """Reads, converts and saves tile images as tiff

    Args:
        img_names (list): list of image names
        base_url (str): base url of images
        save_folder (str): path to folder where images will be saved
        rewrite (bool, optional): if True, images will be downloaded again, even if they already exist. Defaults to False.

    Returns:
        None
    """
    for img in img_names:
        img_url = f"{base_url}{img}.jp2"
        save_path = f"{save_folder}{img}.tiff"

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

def get_coords(img_name, metadata) -> tuple:
    """Get coordinates of tile image

    Args:
        img_name (str): name of tile image
        metadata (pd.DataFrame): metadata as pandas dataframe

    Returns:
        tuple: coordinates of tile image
    """
    lat = metadata.loc[metadata['Kachelname'] == img_name, 'Koordinatenursprung_East'].values[0]
    long = metadata.loc[metadata['Kachelname'] == img_name, 'Koordinatenursprung_North'].values[0]

    return (lat, long)

def get_geodataframe(coords:tuple, crs='EPSG:25832') -> gpd.GeoDataFrame:
    """Get geopandas dataframe containing building shapes and information from API

    Args:
        coords (tuple): coordinates of tile image
        crs (str, optional): coordinate reference system. Defaults to 'EPSG:25832'.

    Returns:
        gpd.GeoDataFrame: geopandas dataframe containing building shapes and information
    """
    base_url = "https://www.wfs.nrw.de/geobasis/wfs_nw_alkis_vereinfacht?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=ave:GebaeudeBauwerk&BBOX="

    x, y = coords

    # get second lat/lon value for bounding box (always 10000*10000)
    x2 = x + 1000
    y2 = y + 1000

    bbox4 = (x, y, x2, y2)

    # create bounding box string for API query
    bbox_str = ','.join(list(map(str, bbox4)))
    gml_url = ''.join([base_url, bbox_str])

    # query webservice
    req = urllib.request.Request(gml_url)
    req.get_method = lambda: 'GET'
    response = urllib.request.urlopen(req)

    gml_str = response.read()

    # response is formatted as GML, which can be queried like normal XML, by referencing the relevant namespaces
    root = ET.ElementTree(ET.fromstring(gml_str)).getroot()

    namespace = {'gml': "http://www.opengis.net/gml/3.2",
             'xmlns': "http://repository.gdi-de.org/schemas/adv/produkt/alkis-vereinfacht/2.0",
             'wfs': "http://www.opengis.net/wfs/2.0",
             'xsi': "http://www.w3.org/2001/XMLSchema-instance"
             }

    buildings = [i.text for i in root.findall('.//gml:posList', namespace)]

    funktions = [i.text for i in root.iter('{http://repository.gdi-de.org/schemas/adv/produkt/alkis-vereinfacht/2.0}funktion')]

    ids = [i.items()[0][1] for i in root.findall('.//gml:MultiSurface[@gml:id]', namespace)]

    building_shapefiles = []

    for id, funktion, build in zip(ids, funktions, buildings):
        # coordinates are not in the correct format, therefore need to be rearranged
        coord_iter = iter(build.split(' '))
        coords = list(map(tuple, zip(coord_iter, coord_iter)))

        # create shapefile from points
        poly = shapely.geometry.Polygon([[float(p[0]), float(p[1])] for p in coords])

        # create records of each building on the selected tile
        building_shapefiles.append({'id': id, 'funktion':funktion, 'geometry': poly})

    df = pd.DataFrame.from_records(building_shapefiles)

    # return geopandas dataframe for input that can be passed to the mask generation
    gdf = gpd.GeoDataFrame(df, crs=crs)

    return gdf

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

def extract_string(input_string) -> str:
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
        return match.group(1) + '_' + match.group(3)
    else:
        return None

def extract_individual_buildings(img_names, gdf, src_images_folder, dst_images_folder, rewrite=False):
    """Extract and save images of individual buildings from image tiles

        Args:
            img_names (list[str]): list of image names
            gdf (gpd.GeoDataFrame): geodataframe containing building shapes
            src_images_folder (str): path to source image folder
            dst_images_folder (str): path to destination image folder
            rewrite (bool, optional): rewrite existing files. Defaults to False.

        Returns:
            None
    """
    # create empty dataframe to store buildings that could not be processed
    unprocessed_buildings = gpd.GeoDataFrame(columns=gdf.columns)
    # create empty list to store existing files that were not rewritten
    existing_files = []

    for img in img_names:
        image_path = src_images_folder + img + ".tiff"

        # open image
        with rasterio.open(image_path, "r") as src:
            assert src.crs == gdf.crs # check if crs of image and gdf are the same
            bbox = shapely.geometry.box(*src.bounds)
            # subset gdf to buildings on the current tile
            gdf_temp = gdf[gdf["kachelname"] == img]

            for index, row in gdf_temp.iterrows():

                building_id = extract_string(row["id"])
                filename = dst_images_folder + building_id + ".tiff"

                # check if file does not exists or if it should be rewritten
                if not os.path.exists(filename) or rewrite:

                    # check if bounds of building are fully within bounds of image
                    if not bbox.contains(row["geometry"]):
                        # add building to unprocessed_buildings
                        row_df = gpd.GeoDataFrame(row).transpose().set_crs(gdf.crs)
                        unprocessed_buildings = pd.concat([unprocessed_buildings, row_df], ignore_index=True)
                        continue
                    else:
                        # create mask for building
                        out_image, out_meta = create_mask_from_shape(src, [row["geometry"]], crop=True, pad=True)
                        with rasterio.open(filename, "w", **out_meta) as dest:
                            dest.write(out_image)
                else:
                    existing_files.append(building_id)

    if len(existing_files) > 0:
        print(f"Skipped creating {len(existing_files)} already-existing files. Set rewrite=True to overwrite those files.\n")

    if unprocessed_buildings.shape[0] > 0:
        gdf_file = dst_images_folder + "buildings_out_of_bounds.gpkg"
        # check if file for saving buildings out of bounds already exists
        if not os.path.exists(gdf_file):
            gdf_temp = gpd.GeoDataFrame(columns=gdf.columns).set_crs(gdf.crs)
        else:
            gdf_temp = gpd.read_file(gdf_file)

        # add unprocessed buildings and save to file
        buildings_out_of_bounds = read_concat_gdf(gdf_temp, unprocessed_buildings)
        buildings_out_of_bounds.to_file(gdf_file, driver="GPKG")
        print(f"Skipped processing {unprocessed_buildings.shape[0]} out of {gdf.shape[0]} buildings whose shapes did not fully lie within the bounds of the image. Added those to {gdf_file}.\n")
    else:
        print("All buildings were processed successfully.\n")

################
### RUN CODE ###

# Download metadata if not already in data/raw/images
metadata_filename = "dop_nw.csv"

if metadata_filename not in os.listdir(raw_images_folder) or rewrite_download:
    print("File not found. Downloading...")
    url_metadata = "https://www.opengeodata.nrw.de/produkte/geobasis/lusat/dop/dop_jp2_f10/dop_meta.zip"

    response = urllib.request.urlopen(url_metadata)
    zipfile = ZipFile(BytesIO(response.read()))

    metadata = pd.read_csv(zipfile.open(metadata_filename),
                        sep=';',
                        skiprows=5) # skip first 5 rows with irrelevant metadata

    metadata.to_csv(raw_images_folder + metadata_filename, index=False)

# read metadata
metadata, img_names = read_metadata(raw_images_folder, metadata_filename, number_of_imgs)

print(f"Metadata for {len(img_names)} tiles imported.")

# read image tiles from API, convert and save them as .tiff
base_url = "https://www.opengeodata.nrw.de/produkte/geobasis/lusat/dop/dop_jp2_f10/"
read_convert_save_images(img_names, base_url, raw_images_folder, rewrite=False)

# get geodataframe containing the shapes of all buildings in the selected tiles
gdf = gpd.GeoDataFrame()

for img_name in img_names:
    coords = get_coords(img_name, metadata)
    gdf_temp = get_geodataframe(coords)
    gdf_temp["kachelname"] = img_name

    # add gdf_temp to gdf
    gdf = read_concat_gdf(gdf, gdf_temp)

print(f"Found {len(gdf)} buildings to be processed.\n")

# create single image for each building
extract_individual_buildings(img_names, gdf, raw_images_folder, processed_images_folder, rewrite=rewrite_processing)
