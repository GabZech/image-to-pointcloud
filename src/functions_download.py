import os
from io import BytesIO
from zipfile import ZipFile
import pandas as pd
import urllib.request
import re
import geopandas as gpd
import xml.etree.ElementTree as ET
import shapely

def download_metadata(raw_data_folder, metadata_filename, url_metadata, skiprows, rewrite_download=False) -> None:
    """Downloads metadata from url and saves it as csv file

        Args:
            raw_data_folder (str): path to folder where metadata will be saved
            metadata_filename (str): name of metadata file
            url_metadata (str): url of metadata file
            skiprows (int): number of rows to skip when reading metadata file
            rewrite_download (bool, optional): if True, metadata will be downloaded again, even if it already exists. Defaults to False.

        Returns:
            None
    """
    if metadata_filename not in os.listdir(raw_data_folder) or rewrite_download:
        response = urllib.request.urlopen(url_metadata)
        zipfile = ZipFile(BytesIO(response.read()))

        metadata = pd.read_csv(zipfile.open(metadata_filename),
                            sep=';',
                            skiprows=skiprows) # skip first X rows with irrelevant metadata

        metadata.to_csv(raw_data_folder + metadata_filename, index=False)
        print(f"Metadata saved as {raw_data_folder + metadata_filename}")

    else:
        print(f"Metadata already exists in {raw_data_folder + metadata_filename}")


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

def prepare_building_data(tile_name, building_types):
    """Prepares building data from given tile name"""
    try:
        coords = extract_coords_tilename(tile_name)
        # multiply by 1000 to get coordinates in meters
        coords = (coords[0] * 1000, coords[1] * 1000)
        gdf_temp = download_building_data(coords, crs='EPSG:25832')
        gdf_temp = gdf_temp[gdf_temp['funktion'].isin(building_types)]
        gdf_temp["kachelname"] = tile_name

        return gdf_temp

    except ValueError:
        print(f"Could not get building data for tile {tile_name}. Coordinates {coords} likely outside of Germany. Skipping.")


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
        return None


def download_building_data(coords:tuple, crs='EPSG:25832') -> gpd.GeoDataFrame:
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