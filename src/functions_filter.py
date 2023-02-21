import geopandas as gpd
import shapely

def filter_buildings(gdf: gpd.GeoDataFrame, type: list, min_area: int) -> gpd.GeoDataFrame:
    """Filters buildings by building type and minimum polygon area

    Args:
        gdf (gpd.GeoDataFrame): GeoDataFrame containing building polygons
        type (list): list of building types to keep
        min_area (int): minimum area of polygon in square meters

    Returns:
        gpd.GeoDataFrame: filtered GeoDataFrame
    """
    # filter by building type
    gdf = gdf[gdf["funktion"].isin(type)]

    # filter by minimum polygon area
    gdf = gdf[gdf['geometry'].area >= min_area]

    return gdf


# remove buildings that are not fully contained in the tile
def remove_buildings_outside_tile(gdf: gpd.GeoDataFrame, coords: tuple) -> gpd.GeoDataFrame:
    """Removes buildings that are not fully contained in the tile

    Args:
        gdf (gpd.GeoDataFrame): GeoDataFrame containing building polygons
        tile_gdf (gpd.GeoDataFrame): GeoDataFrame containing tile polygon

    Returns:
        gpd.GeoDataFrame: filtered GeoDataFrame
    """
    bbox = shapely.geometry.box(coords[0], coords[1], coords[0] + 1000, coords[1] + 1000)

    return gdf[gdf.within(bbox)]