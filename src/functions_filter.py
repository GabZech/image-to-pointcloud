import geopandas as gpd

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
