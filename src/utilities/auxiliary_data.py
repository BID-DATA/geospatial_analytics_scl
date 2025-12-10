import os
import io
import boto3
import dotenv

import pandas as pd
import geopandas as gpd

dotenv.load_dotenv()
s3          = boto3.client('s3')
sclbucket   = os.environ.get("sclbucket")
scldatalake = os.environ.get("scldatalake")

def get_iadb():
    """
    process data to obtain the spanish and english country names for IADB countries
    TODO: dataset must be updated directly in the Data Lake to eliminate this step
    
    Parameters
    ----------
    None
    
    Returns
    ----------
    pandas.DataFrame
        dataframe with IADB country names (EN/SP) and isoalpha3 codes 
    """
    
    # Import country names
        # Define path and S3 object 
    path = "Manuals and Standards/IADB country and area codes for statistical use"
    file = "IADB_country_codes_admin_0.xlsx"
    obj  = s3.get_object(Bucket = sclbucket, Key = f"{path}/{file}")
    
        # Load excel file from S3 into memory and create file-like object from the bytes read
    excel_data = obj['Body'].read()
    excel_file = io.BytesIO(excel_data)
    
        # Datafile
    data = pd.read_excel(excel_file, engine = 'openpyxl')

    # Select rows/columns of interest
    data = data[~data.iadb_region_code.isna()]
    data = data[['isoalpha3','country_name_es']]

    # Replace values
    data['country_name_en'] = data.country_name_es.str.normalize('NFKD')
    data.country_name_en    = data.country_name_en.str.encode('ascii', errors = 'ignore')
    data.country_name_en    = data.country_name_en.str.decode('utf-8')

    # Replace country names
    country_ = {"Belice"                              : "Belize",
                "Bolivia (Estado Plurinacional de)"   : "Bolivia",
                "Brasil"                              : "Brazil",
                "Venezuela (Republica Bolivariana de)": "Venezuela",
                "Republica Dominicana"                : "Dominican Republic",
                "Trinidad y Tabago"                   : "Trinidad and Tobago"}
    
    data.country_name_en = data.country_name_en.replace(country_)

    # Sort dataset
    data = data.sort_values(by = "isoalpha3")
    data = data.reset_index(drop = True)
    
    return data

def get_country_shp(code = "", level = 0):
    """
    get the country's shapefile at the selected admin level 
    
    Parameters
    ----------
    code : str, optional
        country's isoalpha3 code
    level: int, optional 
        administrative level (default is 0)
    
    Returns
    ----------
    geopandas.GeoDataFrame
        geo pandas dataframe with geo data at determined admin level (default 0)
    """
    
    # Import data
    if code == "":
        file = f"Geospatial Basemaps/Cartographic Boundary Files/LAC-26/region/level-{level}/lac-level-{level}.shp"
    else:
        code = code.lower()
        file = f"Geospatial Basemaps/Cartographic Boundary Files/LAC-26/level-{level}/{code}-level-{level}.shp"
    
    # Import data
    path = scldatalake + file
    shp  = gpd.read_file(path) 
    
    # Adjust country codes 
    shp.ADM0_PCODE = shp.ADM0_PCODE.replace({'BZ':'BLZ','BO':'BOL','BR':'BRA','BB':'BRB',
                                             'CL':'CHL','CO':'COL','CR':'CRI','DO':'DOM',
                                             'EC':'ECU','GT':'GTM','GY':'GUY','HN':'HND',
                                             'HT':'HTI','MX':'MEX','NI':'NIC','PA':'PAN',
                                             'PE':'PER','PY':'PRY','SV':'SLV','SR':'SUR',
                                             'TT':'TTO','UY':'URY','VE':'VEN'})
    
    return shp
            