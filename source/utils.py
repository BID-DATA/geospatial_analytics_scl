"""
individual modules for geospatial analysis
includes multiple functions that eventualy should be in individual .py modules 

Author : Laura Goyeneche, Consultant SPH, lauragoy@iadb.org
Created: April 05, 2023 
"""

# Basics 
#-------------------------------------------------------------------------------#
# Libraries
import os 
import re
import time
import boto3
import dotenv
import requests
import numpy as np
import pandas as pd
import geopandas as gpd
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from geopandas.tools import sjoin
from shapely.geometry import Polygon
from h3 import geo_to_h3, h3_to_geo_boundary

# Working environments
dotenv.load_dotenv()
sclbucket   = os.environ.get("sclbucket")
scldatalake = os.environ.get("scldatalake")

# Resources and buckets
s3_       = boto3.resource("s3")
s3_bucket = s3_.Bucket(sclbucket)

# IADB countries 
#-------------------------------------------------------------------------------#
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
    file = "Manuals and Standards/IADB country and area codes for statistical use/IADB_country_codes_admin_0.xlsx"
    path = scldatalake + file
    data = pd.read_excel(path, engine = 'openpyxl')

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


# Administrative shapefiles
#-------------------------------------------------------------------------------#
def get_country_shp(code, level = 0):
    """
    gets the country's shapefile at the selected admin level 
    
    Parameters
    ----------
    code : str
        country's isoalpha3 code
    level: int, optional 
        administrative level (default is 0)
    
    Returns
    ----------
    geopandas.GeoDataFrame
        geo pandas dataframe with geo data at determined admin level (default 0)
    """
    
    # Import data
    code = code.lower()
    file = f"Geospatial Basemaps/Cartographic Boundary Files/LAC-26/level-{level}/{code}-level-{level}.shp"
    path = scldatalake + file
    shp  = gpd.read_file(path)
    
    return shp


# Extract HTML code / information from HDX website
#-------------------------------------------------------------------------------#
def get_meta_url(data, code):
    """
    gets the HTML content from the high density population datasets in HDX
    https://data.humdata.org/organization/facebook?q=high%20resolution%20population%20density
    
    Parameters
    ----------
    data : pandas.DataFrame
        dataframe with IADB country names (EN/SP) and isoalpha3 codes
    code : str
        country's isoalpha3 code
    
    Returns
    ----------
    dict
        dictionary with file name and URL to download data by groups
        groups includes:
            total_population
            women
            men
            children_under_five
            youth_15_24
            elderly_60_plus
            women_of_reproductive_age_15_49
    """
    
    # Get latest population density maps name files 
    # Request HTML content
    geo      = data[data.isoalpha3 == code].country_name_en.values[0].lower().replace(" ","-")
    url      = f"https://data.humdata.org/dataset/{geo}-high-resolution-population-density-maps-demographic-estimates"
    response = requests.get(url)
    
    # Omit countries without population daya
    if response.status_code == 200:
    
        # Format HTML code
        html = response.content
        soup = BeautifulSoup(html, "html5lib")

        # Find file names
        soup = soup.find_all('ul', attrs = {"class":"hdx-bs3 resource-list"})
        soup = soup[0].find_all('li', attrs = {"class":"resource-item"})
        url  = [item.find_all('div', attrs = {"class":"hdx-btn-group hdx-btn-group-fixed"})[0].find('a')['href'] for item in soup]

        # Processing URL
        url = [item for item in url if "csv" in item]
        url = [f"https://data.humdata.org{item}" for item in url]

        # Processing file names
        files = []
        for item in url: 
            item_ = item.split("/")[-1]
            item_ = item_.replace("_csv",".csv")
            item_ = item_.replace(".zip",".gz")
            item_ = re.sub("(_|-)\d+", "", item_)
            item_ = item_.replace("population","total_population")
            item_ = item_.replace("general","total_population")
            item_ = f"{code}_{item_}"
            item_ = item_.replace(f"{code.lower()}_","")
            item_ = item_.replace(f"_{code.lower()}","")
            item_ = item_.replace("elderly_plus","elderly_60_plus")
            item_ = item_.replace("youth","youth_15_24")
            item_ = item_.replace("women_of_reproductive_age","women_of_reproductive_age_15_49")

            files.append(item_)

        # Create dictionary 
        keys_ = [x.replace(f"{code.upper()}_","").replace(".csv.gz","") for x in files]
        vals_ = [[x,y] for x,y in zip(files,url)]
        dict_ = dict(zip(keys_,vals_))
        
    else: 
        dict_ = dict(zip([],[]))
    
    return dict_


# Get population data from META
#-------------------------------------------------------------------------------#
def get_population(data, code, group = "total_population"):
    """
    gets the high density population datasets in HDX
    https://data.humdata.org/organization/facebook?q=high%20resolution%20population%20density
    
    Parameters
    ----------
    data : pandas.DataFrame
        dataframe with IADB country names (EN/SP) and isoalpha3 codes
    code : str
        country's isoalpha3 code
    group: str
        population group (default is `total_population`), including:
            total_population
            women
            men
            children_under_five
            youth_15_24
            elderly_60_plus
            women_of_reproductive_age_15_49
    
    Returns
    ----------
    pandas.DataFrame
        dataframe with adjusted population by admin-0 shapefile (country's admin border)
    """
    # Import data
    data = get_iadb()
    meta = get_meta_url(data, code)
    
    # Group of interest 
    groups = [name for name in meta.keys() if group in name]
    
    # Individuals shapefiles 
    files_ = []
    for group_ in groups:
        # Select group of interest
        item = meta[group_]
        name = item[0]
        path = item[1]
        pop  = pd.read_csv(path)

        # Keep variables of interest
        # Keep most recent population estimation 
        temp = [name for name in pop.columns if "latit" not in name and "long" not in name]
        if len(temp) > 1: 
            if temp[len(temp)-1] > temp[len(temp)-2]:
                var_ = temp[len(temp)-1]
            else: 
                var_ = temp[len(temp)-2]
        else: 
            var_ = temp[0]

        # Select variables of interest
        vars_ = ["latitude","longitude",var_]
        pop   = pop[vars_]
        pop   = pop.rename(columns = {var_:"population"})

        # Rename variables
        pop.columns = [re.sub("_\d+", "", name) for name in pop.columns]

        # Convert population .csv to .gpd
        geometry = gpd.points_from_xy(pop['longitude'], pop['latitude'])
        pop_geo  = gpd.GeoDataFrame(pop.copy(), geometry = geometry, crs = 4326)

        # Keep points inside country/region of interets
        # get_country_shp() default admin-level-0
        shp_        = get_country_shp(code)
        pop_geo_adj = gpd.clip(pop_geo, shp_)
        
        # Append to list of shapefiles
        files_.append(pop_geo_adj)
    
    # Create master data
    pop_geo_adj_ = gpd.pd.concat(files_).pipe(gpd.GeoDataFrame)
    
    # Export to Data Lake as .csv.gz 
    file = pop_geo_adj_.copy()
    file = file.drop(columns = "geometry")
    path = "Development Data Partnership/Facebook - High resolution population density map/public-fb-data/csv"
    path = scldatalake + f"{path}/{code.upper()}/{name}"
    file.to_csv(path, compression = 'gzip')
    
    return file


# Get infrastructure from official records
#-------------------------------------------------------------------------------#
def get_amenity_official(amenity, official):
    """
    process official records by country
    each country's raw data is different, preprocessing is done individually
    
    Parameters
    ----------
    amenity : str
        string with amenity name, including:
            financial
            healthcare
    official : list
        list of countries with official data
    
    Returns
    ----------
    pandas.DataFrame
        dataframe amenity information per country and site, including:
            isoalpha3: country name
            source   : source name
            name     : amenity name
            lat      : latitude
            lon      : longitude
    """
    
    # Inputs
    path = f"Geospatial infrastructure/{amenity} Facilities"
    
    # Master table 
    infrastructure = []
    
    # Financial Facilities
    # No official records yet
    
    # Healthcare Facilities
    if amenity == "Healthcare":
        # Jamaica 
        #--------------------------------------------------------
        # Import data
        file  = [file for file in official if "JAM" in file][0]
        path_ = f"{scldatalake}{path}/{file}"
        file  = pd.read_csv(path_)

        # Create variables
        file['isoalpha3'] = "JAM"
        file['source']    = "Ministry of Health"
        file['source_id'] = np.nan
        file['amenity']   = file.Type.str.lower()
        file['name']      = file[['H_Name','Parish']].apply(lambda x : '{} in {}'.format(x[0],x[1]), axis = 1)
        file['lat']       = file.GeoJSON.apply(lambda x: re.findall(r"\d+\.\d+", x)[1])
        file['lon']       = file.GeoJSON.apply(lambda x: re.findall(r"\d+\.\d+", x)[0])

        # Keep variables of interest
        file = file[file.columns[-7::]]

        # Add to master table
        infrastructure.append(file)
        
        # Peru 
        #--------------------------------------------------------
        # Import data
        file  = [file for file in official if "PER" in file][0]
        path_ = f"{scldatalake}{path}/{file}"
        file  = pd.read_csv(path_)

        # Dictionary with amenity names
        n_before  = ['I-1','I-2','I-3','I-4','II-1','II-2','II-E','III-1','III-2','III-E','SD'] 
        n_after   = ["Primary care"] * 4 + ["Secondary care"] * 3 + ["Tertiary care"] * 3 + [""]
        d_amenity = dict(zip(n_before,n_after))

        # Create variables
        file['isoalpha3'] = "PER"
        file['source']    = "Ministry of Health"
        file['source_id'] = file.codigo_renaes
        file['amenity']   = file.categoria.replace(d_amenity)
        file['name']      = file[['nombre','diresa']].apply(lambda x : '{} in {}'.format(x[0].title(),x[1].title()), axis = 1)
        file['lat']       = file.latitud
        file['lon']       = file.longitud

        # Keep variables of interest
        file = file[file.columns[-7::]]

        # Add to master table
        infrastructure.append(file)
        
        # El Salvador 
        #--------------------------------------------------------
        # Import data 
        file_ = [file for file in official if "SLV" in file]
        for file in file_:
            path_ = f"{scldatalake}{path}/{file}"
            file  = pd.read_csv(path_)

            # Create variables
            file['isoalpha3'] = "SLV"
            file['source']    = "Ministry of Health"
            file['source_id'] = np.nan
            file['amenity']   = file.ESPECIALIZACION.str.lower()
            file['name']      = file[['Name','MUNICIPIO','REGION']].apply(lambda x : '{}, {}, {}'.format(x[0], x[1], x[2]), axis = 1)
            file['lat']       = file.Y
            file['lon']       = file.X

            # Keep variables of interest
            file = file[file.columns[-7::]]

            # Add to master table
            infrastructure.append(file)
            
        # Master table 
        #--------------------------------------------------------
        # Generate master table 
        infrastructure = pd.concat(infrastructure)
        infrastructure = infrastructure.reset_index(drop = True)
    
    return infrastructure


# Get infrastructure from official and public records
#-------------------------------------------------------------------------------#
def get_amenity(amenity):
    """
    gets the infrastructure data based on official and public records
    
    Parameters
    ----------
    amenity : str
        string with amenity name, including:
            financial
            healthcare
    
    Returns
    ----------
    pandas.DataFrame
        dataframe amenity information per country and site, including:
            isoalpha3: country name
            source   : source name
            name     : amenity name
            lat      : latitude
            lon      : longitude
    """
    
    # Inputs
    data    = get_iadb()
    amenity = amenity.title()
    
    # Get files by bucket
    path  = f"Geospatial infrastructure/{amenity} Facilities"
    files = [file.key.split(path + "/")[1] for file in s3_bucket.objects.filter(Prefix = path).all()]
    
    # Identify records by categories
    official = [file for file in files if "official" in file]
    public   = [file for file in files if "healthsites" in file or "OSM" in file]
    
    # Create master table 
    infrastructure = []
    name           = []
    
    # Process official records 
    if len(official) > 0:
        infrastructure.append(get_amenity_official(amenity, official))
        
        # Identify country names with official records
        name = pd.concat(infrastructure).isoalpha3.unique().tolist()
    
    # Process public records
    # Records different from OSM
    file = [file for file in public if "OSM" not in file]
    if len(file) > 0:
        # Import data
        file  = file[0]
        path_ = f"{scldatalake}{path}/{file}"
        file  = pd.read_csv(path_)

        # Keep rows of interest
        file = file[~file.isoalpha3.isin(name)]
        file = file[~file.isoalpha3.isna()]

        # Keep variables of interest
        file = file.drop(columns = "geometry")
        
        # Add to master tables
        infrastructure.append(file)
        
        # Identify healthsites country names
        name =  pd.concat(infrastructure).isoalpha3.unique().tolist()
    
    # OSM records
    # Import data
    file_  = [file for file in public if "OSM" in file]
    for file in file_:
        path_ = f"{scldatalake}{path}/{file}"
        file  = pd.read_csv(path_, low_memory = False)

        # Keep IADB countries
        file = file[file.isoalpha3.isin(data.isoalpha3.unique())]

        # Keeps countries without official or healthsites.io records
        file = file[~file.isoalpha3.isin(name)]

        # Create variables
        file['source']    = "OSM"
        file['source_id'] = file.id

        # Keep variables of interest
        file = file[['isoalpha3','source','source_id','amenity','name','lat','lon']]

        # Add to master table
        infrastructure.append(file)
    
    # Generate master table 
    infrastructure = pd.concat(infrastructure)
    infrastructure = infrastructure.reset_index(drop = True)
    
    return infrastructure

# Get isochrone
#-------------------------------------------------------------------------------#
def get_isochrone(lon, lat, minute, profile, generalize = 500):
    """
    calculates the individual isochrones based on lat-lon
    for more detail on the API options, refer to the following link:
        https://docs.mapbox.com/playground/isochrone/
    
    Parameters
    ----------
    lat,lon : float
        latitude, longitude
    minute : int 
        distance in minutes from facility 
    profile : str
        routing profile, including:
            walking
            cycling
            driving
    generalize : int, optional
        tolerance for Douglas-Peucker generalization in meters (default is 500)
        
    Returns
    ----------
    geopandas.GeoDataFrame
        geo pandas dataframe with isochrone for each latitude and longitude points
    """
    
    # Define url 
    token = os.environ.get("access_token_dp")
    url   = "https://api.mapbox.com/isochrone/v1/mapbox/"
    url   = f'{url}{profile}/{lon},{lat}?contours_minutes={minute}&generalize={generalize}&polygons=true&access_token={token}'
    
    # Request isochrones
    response = requests.get(url).json()
    
    # Create GeoDataframe and append results 
    try: 
        features  = response['features']
        isochrone = gpd.GeoDataFrame.from_features(features)
    except:
        isochrone = gpd.GeoDataFrame()
    
    return isochrone


# Get multipolygon with isochrones by country
#-------------------------------------------------------------------------------#
def get_isochrones_country(code, amenity, minute, profile):
    """
    calculates the isochrones per country based on mapbox API
    for more detail on the API options, refer to the following link:
        https://docs.mapbox.com/playground/isochrone/
    
    Parameters
    ----------
    code : str
        country isoalpha3 code
    amenity : str
        string with amenity name, including:
            financial
            healthcare
    minute : int 
        distance in minutes from facility 
    profile : str
        routing profile, including:
            walking
            cycling
            driving
    
    Returns
    ----------
    geopandas.GeoDataFrame
        geo pandas dataframe with multipolygon with covered area 
    """
    
    # Infrastructure data
    # TODO: path must be updated with Data Lake path
    path = f"../data/0-raw/infrastructure/{amenity}_facilities.csv"
    data = pd.read_csv(path)
    data = data[data.isoalpha3 == code]
    data = data[~data.lat.isna()]
    
    # Get list of isochrones 
    isochrones = []
    for x,y,name in zip(data.lon, data.lat, data.amenity):
        # Calculate isochrone 
        shp_            = get_isochrone(x, y, minute, profile)
        shp_['amenity'] = name
        isochrones.append(shp_)

        # Set time 
        time.sleep(1)
            
    # Master table 
    isochrones = pd.concat(isochrones)
    
    return isochrones


# Get coverage by ADMIN-2 level and H3 cell
#-------------------------------------------------------------------------------#
def get_coverage(code, amenity, profile, minute, group = "total_population"):
    """
    calculates the coverage percentage per country by admin-2 level and H3 cell (resolution 3)
    
    Parameters
    ----------
    code : str
        country isoalpha3 code
    amenity : str
        string with amenity name, including:
            financial
            healthcare
    profile : str
        routing profile, including:
            walking
            cycling
            driving
     minute : int 
        distance in minutes from facility 
    group: str
        population group (default is `total_population`), including:
            total_population
            women
            men
            children_under_five
            youth_15_24
            elderly_60_plus
            women_of_reproductive_age_15_49
    
    Returns
    ----------
    geopandas.GeoDataFrame
        geo pandas dataframe with coverage at admin-2 and H3
    """
    
    # Inputs 
    #--------------------------------------------------------
        # Shapefile
    if code in ["BHS","BRB","BLZ","JAM","TTO"]:
        adm2_shp = get_country_shp(code, level = 1)
        adm2_shp["ADM2_PCODE"] = adm2_shp.ADM1_PCODE
    else: 
        adm2_shp = get_country_shp(code, level = 2)
    
        # Population and isochrones
    isochrone  = gpd.read_file(f"../data/1-isochrones/{amenity}/{code}-{profile}-{minute}.geojson")
    population = pd.read_csv(f"../data/0-raw/population/{group}/{code}_{group}.csv.gz")
    geometry   = gpd.points_from_xy(population['longitude'], population['latitude'])
    population = gpd.GeoDataFrame(population.copy(), geometry = geometry, crs = 4326)
    
    # Population in isochrone 
    pop_iso = gpd.clip(population, isochrone)
    
    # Coverage at admin-2 level 
    #--------------------------------------------------------
        # Population in admin-2 level 
    pop_adm2 = gpd.sjoin(population, adm2_shp)
    pop_adm2 = pop_adm2[["ADM2_PCODE","population"]].groupby("ADM2_PCODE").sum().reset_index()
    pop_adm2 = pop_adm2.rename(columns = {"population":"pop_tot"})
    
        # Covered population in admin-2 level
    pop_adm2_cov = gpd.sjoin(pop_iso, adm2_shp)
    pop_adm2_cov = pop_adm2_cov[["ADM2_PCODE","population"]].groupby("ADM2_PCODE").sum().reset_index()
    pop_adm2_cov = pop_adm2_cov.rename(columns = {"population":"pop_cov"})
    
        # Coverage map 
    adm2_coverage = adm2_shp.copy()
    adm2_coverage = adm2_coverage.merge(pop_adm2    , on = "ADM2_PCODE", how = "left")
    adm2_coverage = adm2_coverage.merge(pop_adm2_cov, on = "ADM2_PCODE", how = "left")
    
        # Create coverage features
    adm2_coverage["pop_cov"]   = adm2_coverage.pop_cov.fillna(0)
    adm2_coverage["pop_uncov"] = adm2_coverage.pop_tot   - adm2_coverage.pop_cov
    adm2_coverage["per_cov"]   = adm2_coverage.pop_cov   * 100 / adm2_coverage.pop_tot
    adm2_coverage["per_uncov"] = adm2_coverage.pop_uncov * 100 / adm2_coverage.pop_tot
    
    # Coverage at H3 cell
    # Source: resolution table 
    # https://h3geo.org/docs/core-library/restable/
    #--------------------------------------------------------
        # Calculate H3 cells per population points
    population["hex_id"] = population.apply(lambda x: geo_to_h3(x["latitude"], x["longitude"], resolution = 6), axis = 1)
    
        # Collapse by H3
    h3_population             = population.groupby("hex_id").population.agg(sum).reset_index()
    h3_population["geometry"] = h3_population['hex_id'].apply(lambda x: h3_to_geo_boundary(x, geo_json = True))
    h3_population['hex_poly'] = h3_population['geometry'].apply(lambda x: Polygon(x))
    h3_population             = gpd.GeoDataFrame(h3_population, geometry = h3_population.hex_poly, crs = "EPSG:4326")
    
        # Covered population in H3 cells
    h3_pop_cov = gpd.sjoin(pop_iso, h3_population.drop(columns = "population"))
    h3_pop_cov = h3_pop_cov[["hex_id","population"]]
    h3_pop_cov = h3_pop_cov.rename(columns = {"population":"pop_cov"})
    h3_pop_cov = h3_pop_cov.groupby("hex_id").sum().reset_index()
    
        # H3 coverage map 
    h3_coverage = h3_population.merge(h3_pop_cov, on = "hex_id", how = "left")
    h3_coverage = h3_coverage.rename(columns = {"population":"pop_tot"})
    h3_coverage = h3_coverage.drop(columns = "geometry")
    h3_coverage = h3_coverage.rename(columns = {"hex_poly":"geometry"})
    
        # Create coverage features
    h3_coverage["pop_cov"]   = h3_coverage.pop_cov.fillna(0)
    h3_coverage["pop_uncov"] = h3_coverage.pop_tot   - h3_coverage.pop_cov
    h3_coverage["per_cov"]   = h3_coverage.pop_cov   * 100 / h3_coverage.pop_tot
    h3_coverage["per_uncov"] = h3_coverage.pop_uncov * 100 / h3_coverage.pop_tot
    
        # Set `geometry` as geometry in h3 level
    h3_coverage = h3_coverage.set_geometry(col = 'geometry')
    
    return adm2_coverage, h3_coverage  