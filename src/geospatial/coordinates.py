def get_coordinates(address, code):
    """
    gets the coordinates for address
    
    Parameters
    ----------
    address : str
        address, including, if possible, admin1, admin2 and country name
    
    Returns
    ----------
    list
        list of possible coordinates [longitude,latitude]
    """    
    # Inputs
    token   = os.environ.get("access_token_dp")
    country = get_iadb()
    country = country[country.isoalpha3 == code].country_name_es.tolist()[0]
    address = address if country in address else f"{address} {country}"
    address = urllib.parse.quote(address.encode('utf-8')) 
    url     = f'https://api.mapbox.com/geocoding/v5/mapbox.places/{address}.json?access_token={token}'
    
    # Request
    try: 
        response = requests.get(url).json()
        response = response['features']
        response = [j for j in response if country in j["place_name"]]
    except: 
        response = []
        
    return response

def get_coordinates(address, country):
   
    # Inputs
    token   = os.environ.get("access_token_dp")
    address = urllib.parse.quote(address.encode('utf-8')) 
    url     = f'https://api.mapbox.com/geocoding/v5/mapbox.places/{address}.json?access_token={token}'
    
    # Request
    try: 
        response = requests.get(url).json()
        response = response['features']
        response = [j for j in response if country in j["place_name"]]
    except: 
        response = []
        
    return response



col = pd.read_csv('../../32-IDB Atlas/raw/infrastructure/COL/reps.csv')
col = col.drop_duplicates()
col = col[col.MunicipioPrestador == 11001]
col.CodigoHabilitacionSede = col.CodigoHabilitacionSede.apply(lambda x: str(x).replace(' ',''))
col.CodigoHabilitacionSede = col.CodigoHabilitacionSede.astype(int)
col['is_duplicate_sede']   = col.duplicated(subset=['CodigoPrestador','DireccionSede'], keep = 'first').astype(int)
col['is_duplicate_pres']   = col.duplicated(subset=['CodigoPrestador','DireccionPrestador'], keep = 'first').astype(int)

col = col[col.is_duplicate_sede == 0]
col = col[col.ClasePrestadorDesc == 'Instituciones Prestadoras de Servicios de Salud - IPS']

col = col[['MunicipioPrestador','CodigoPrestador','NombrePrestador','DireccionPrestador','ClasePrestadorDesc','CodigoHabilitacionSede','NombreSede','DireccionSede']]
col = col[~col.DireccionSede.isna()]

relevance,lon,lat = [],[],[]
for i in range(0,len(col)):
    print(i)
    address1 = f"{col.iloc[i].DireccionSede}, BOGOTA D.C."
    response = get_coordinates(address1,"Colombia")
    
    if len(response) > 0:
        response = response[0]
        relevance.append(response['relevance'])
        lon      .append(response['geometry']['coordinates'][0])
        lat      .append(response['geometry']['coordinates'][1])
    
    else:
        relevance.append('')
        lon      .append('')
        lat      .append('')

col['mapbox_relevance'] = relevance
col['lon']       = lon
col['lat']       = lat
col['lon'] = np.where(col['lon'] == '', np.nan, col['lon'])
col['lat'] = np.where(col['lat'] == '', np.nan, col['lat'])
col['is_duplicated'] = col.duplicated(subset = ['lon','lat'])

geom  = gpd.points_from_xy(col['lon'], col['lat'])
col = gpd.GeoDataFrame(col.copy(), geometry = geom)

col.to_csv('../../32-IDB Atlas/raw/infrastructure/COL/bogota-reps.csv', index = False)


