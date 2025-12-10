import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString, Polygon


def get_data_types():
    # Generate random latitude and longitudes
    np.random.seed(42) 
    num_points = 20  
    latitudes  = np.random.uniform(low = -90 , high = 90 , size = num_points)
    longitudes = np.random.uniform(low = -180, high = 180, size = num_points)

    # DataFrame to GeoDataframe
    points_data = pd.DataFrame({'latitude': latitudes,'longitude': longitudes})
    geom_points = [Point(xy) for xy in zip(points_data['longitude'], points_data['latitude'])]
    gdf_points  = gpd.GeoDataFrame(points_data, geometry = geom_points)

    # Create line
    line       = LineString([geom_points[0], geom_points[1]])
    lines_data = gpd.GeoDataFrame({'geometry': [line]}, index=[0])

    # Create polygon
    polygon       = Polygon([[p.x, p.y] for p in geom_points[:5]])
    polygons_data = gpd.GeoDataFrame({'geometry': [polygon]}, index=[0])

    # Simulating raster data
    raster_data = np.random.rand(50, 100)

    # Plotting all geospatial data types in subplots
    fig, axs = plt.subplots(2, 2, figsize=(10, 6))

    # Point data subplot
    gdf_points.plot(ax = axs[0,0], markersize = 30)
    axs[0,0].set_title('Point Data')

    # Line data subplot with points
    gdf_points.plot(ax = axs[0,1], markersize = 30)
    lines_data.plot(ax = axs[0,1], color = 'orange', linewidth = 5)
    axs[0,1].set_title('Line Data') 

    # Polygon data subplot with points
    gdf_points   .plot(ax = axs[1,0], markersize = 30)
    polygons_data.plot(ax = axs[1,0], color = 'red', alpha = 0.7)
    axs[1,0].set_title('Polygon Data')

    # Raster data subplot
    axs[1,1].imshow(raster_data, cmap = 'viridis')
    axs[1,1].set_title('Raster Data')
    axs[1,1].axis('off')

    # Adjust layout
    plt.tight_layout()
    plt.show()