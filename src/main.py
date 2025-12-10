"""
Import libraries
    Standard
    Thrid-party 
    Local modules
        Initialize the `src` package
"""

# Standard 
import io
import os
import re
import time
from datetime import datetime
import urllib

# AWS and environment
import boto3
import dotenv

# Data management and processing
import numpy as np
import pandas as pd
import geopandas as gpd
from sodapy import Socrata

# Web scraping and requests
import requests
from bs4 import BeautifulSoup

# Geospatial 
import fiona
import rasterio
from geopandas.tools import sjoin
from shapely.geometry import Polygon
from h3 import geo_to_h3, h3_to_geo_boundary

# Visualization
import matplotlib.pyplot as plt

# Local Application/Library Imports
from src.processing import *
from src.geospatial import *
from src.utilities  import *
from src.statistics import *

# Working environments
dotenv.load_dotenv()
dotenv.load_dotenv("/Users/lauragoyeneche/Google Drive/My Drive/02-Work/10-IDB Consultant/1-Social Protection & Health/32-IDB Atlas/src/.env")
sclbucket   = os.environ.get("sclbucket")
scldatalake = os.environ.get("scldatalake")

# Resources and buckets
s3  = boto3.client('s3')
s3_ = boto3.resource("s3")
s3_bucket = s3_.Bucket(sclbucket)

# Define funcionts accessible via 'from src import *'
__all__ = [
    'get_iadb',
    'get_country_shp',
    'get_meta_url',
    'get_population',
    'get_coordinates',
    'get_isochrone',
    'get_isochrones_country',
    'get_tile_url',
    'get_amenity_official',
    'get_amenity',
    'get_access',
    'quarter_start',
    'find_best_match',
    'calculate_stats',
    'palettes',
    'expand_colors',
    'create_bivariate',
    'get_desinventar',
    'get_emdat',
    'get_desastres',
    'normalize_text',
    'get_metadata',
    'get_data_types'
]
