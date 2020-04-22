import pandas as pd
import numpy as np

import geopandas as gpd
import matplotlib.pyplot as plt

import re
import json
import sys
import time
import requests
import category_encoders as ce
from urllib.parse import quote_plus

import folium
from shapely.geometry import box, mapping, polygon, multipolygon, Point

CLIENT_ID = '' # your Foursquare ID
CLIENT_SECRET = '' # your Foursquare Secret
VERSION = '20180605' # Foursquare API version

def generate_square_grid(geometry, threshold=0.05):
    """
    Adapted from https://snorfalorpagus.net/blog/2016/03/13/splitting-large-polygons-for-faster-intersections/
    """
    bounds = geometry.bounds
    geom = geometry

    # Check if threshold is appropriate for bounding box
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]

    print(width)
    print(height)

    if width > 10 or height > 10:
        # prevents too many grid items per city
        threshold *= 10
        print('next threshold', threshold)
    if width > 5 or height > 5:
        # prevents too many grid items per city
        threshold *= 4
        print('next threshold', threshold)
    elif width > 2 or height > 2:
        # prevents too many grid items per city
        threshold *= 2
        print('next threshold', threshold)

    x_min = int(bounds[0] // threshold)
    x_max = int(bounds[2] // threshold)
    y_min = int(bounds[1] // threshold)
    y_max = int(bounds[3] // threshold)
    
    grid = []
    for i in range(x_min, x_max+1):
        for j in range(y_min, y_max+1):
            b = box(i*threshold, j*threshold, (i+1)*threshold, (j+1)*threshold)
            g = geom.intersection(b)
            print('int', g)
            if g.is_empty:
                continue
            is_polygon = isinstance(g, (polygon.Polygon, multipolygon.MultiPolygon))
            if is_polygon:
                grid.append(g)
    print('grid length', len(grid))
    return grid 

def plot_foursquare_search_grid(lat, lng, grid=[]):
    m = folium.Map(location=[lat, lng])

    for g in grid:
        folium.GeoJson(g).add_to(m)

    folium.LayerControl().add_to(m)
    return m

def fetch_venues(neighborhoods, cities, latitudes, longitudes, radius=250, LIMIT=100):
    """
    Foursquare neighborhood `/explore` helper
    """
    venues_list=[]
    for n, c, lat, lng in zip(neighborhoods, cities, latitudes, longitudes):            
        # create the API request URL
        url = 'https://api.foursquare.com/v2/venues/explore?&client_id={}&client_secret={}&v={}&ll={},{}&radius={}&limit={}'.format(
            CLIENT_ID, 
            CLIENT_SECRET, 
            VERSION, 
            lat, 
            lng, 
            radius, 
            LIMIT)
        results = requests.get(url).json()["response"]
        if results:
            items = results['groups'][0]['items']
            if results and items:
                venues_list.append([(
                    n,
                    c,
                    lat, 
                    lng, 
                    v['venue']['name'],
                    v['venue']['categories'][0]['name']) for v in items])

    nearby_venues = pd.DataFrame([item for venue_list in venues_list for item in venue_list])
    nearby_venues.columns = ['Neighborhood', 
                    'City',
                  'Latitude', 
                  'Longitude', 
                  'Venue',  
                  'Venue Category']
    
    return(nearby_venues)

# Define Foursquare `/explore` helper

def fetch_city_venues(cities, radius=100000):
    venues_list=[]
    for c in cities:            
        # create the API request URL
        url = 'https://api.foursquare.com/v2/venues/explore?&client_id={}&client_secret={}&v={}&near={}&intent=browse'.format(
            CLIENT_ID, 
            CLIENT_SECRET, 
            VERSION, 
            c
        )
        print(url)
        results = requests.get(url).json()["response"]

        try:
            if results:
                items = results['groups'][0]['items']
                if results and items:
                    venues_list.append([(
                        c,
                        v['venue']['name'],
                        v['venue']['categories'][0]['name'],
                        v['venue']['location']['lat'],
                        v['venue']['location']['lng']) for v in items])
                else:
                    break
        except:
            e = sys.exc_info()[0]
            print('error' + e)
            break

    nearby_venues = pd.DataFrame([item for venue_list in venues_list for item in venue_list])
    nearby_venues.columns = ['City',
                  'Venue',  
                  'Venue Category',
                  'Venue Latitude',
                  'Venue Longitude']
    
    return(nearby_venues)

def fetch_venue_likes(venue_id):
    url = "https://api.foursquare.com/v2/venues/{}/likes?client_id={}&client_secret={}&v={}".format(
        venue_id,
        CLIENT_ID, 
        CLIENT_SECRET, 
        VERSION
    )

    results = requests.get(url).json()
    # time.sleep(0.3)

    if results["meta"]["code"] != 200:
        print('Status', results["meta"]["code"])
        return None
    
    response = results["response"]
    print(response)
    return response["likes"]["count"] or 0

# Define Foursquare `/search` helper

def search_city_venues(city_name='', grid_gdf=gpd.GeoDataFrame(), grid_interval=0.05):
    """
    Searches city with grid. This approach of using /search should reduce the 
    duplication problem we were seeing with pagination.
    
    grid -- list of Polygons
    
    Returns
    list of venues labeled with cityname
    """
    grid_piece_venues = []
    
    # for i,g in enumerate(grid):
    #     print('g', g, g.geometry)

    for i,g in grid_gdf.iterrows():
        geom = g.geometry
        is_polygon = isinstance(geom, (polygon.Polygon, multipolygon.MultiPolygon))

        if is_polygon:
            # create the API request URL
            url = 'https://api.foursquare.com/v2/venues/search?&categoryId=4d4b7105d754a06374d81259&client_id={}&client_secret={}&v={}&sw={},{}&ne={},{}&intent=browse&limit=50'.format(
                CLIENT_ID, 
                CLIENT_SECRET, 
                VERSION, 
                geom.bounds[1],
                geom.bounds[0],
                geom.bounds[3],
                geom.bounds[2],
            )

            print('REQUESTED', city_name, i, geom.bounds)
            results = requests.get(url).json()
            time.sleep(0.3)

            # if results.status_code != 200:
            #     print('Status', results.status_code)
            
            response = results["response"]
            try:
                if response:
                    items = response['venues']

                    if items and len(items)>0:
                        grid_items = []
                        
                        for v in items:
                            lat = v['location']['lat'] if v['location'] else None
                            lng = v['location']['lng'] if v['location'] else None
                            
                            p = Point(lng, lat)
                            if p and geom.contains(p):
                                grid_items.append({
                                    'city': city_name,
                                    'id': v['id'],
                                    'name': v['name'],
                                    'category': v['categories'][0]['name'] if v['categories'] and v['categories'][0] else None,
                                    'location': p
                                })

                        print('FOUND', len(grid_items))
                        if len(grid_items) == 50:
                            next_grid = generate_square_grid(geom, grid_interval/2)
                            next_grid_gdf = gpd.GeoDataFrame(geometry=next_grid)
                            next_venues = search_city_venues(city_name, next_grid_gdf, grid_interval/2)
                            [grid_piece_venues.append(v) for v in next_venues]
                        else:
                            [grid_piece_venues.append(gr) for gr in grid_items]

            except:
                print('Unable to parse venues/search response.')
                break
    
    return(grid_piece_venues)

def fetch_venue_categories():
    url = 'https://api.foursquare.com/v2/venues/categories?client_id={}&client_secret={}&v={}'.format(
            CLIENT_ID, 
            CLIENT_SECRET, 
            VERSION, 
    )
    results = requests.get(url).json()["response"]
    res = []
    if results and results['categories']:
        for r in results['categories']:
            
            def append_categories(categories, category):
                for c in categories:
                    subcategory = c['name']
                    nested = len(c['categories'])
                    if nested:
                        append_categories(c['categories'], category)
                    res.append({'name': subcategory, 'id': c['id'], 'category': category['name'], 'cat_id': category['id'] })
    
            append_categories(r['categories'], r)

    return res



def return_most_common_venues(row, num_top_venues):
    row_categories = row.iloc[1:]
    row_categories_sorted = row_categories.sort_values(ascending=False)
    
    return row_categories_sorted.index.values[0:num_top_venues]

num_top_venues = 10

indicators = ['st', 'nd', 'rd']

def hash_venue_categories(venues):
    # use high n=10 to account for 1024 categories, expect ~525
    ce_hash = ce.HashingEncoder(cols = ['1st Most Common Venue' , '2nd Most Common Venue', '3rd Most Common Venue'], n_components=10)
    return ce_hash.fit_transform(venues)

def venue_frequency(venues):
    venues_onehot = pd.get_dummies(venues[['Venue Category']], prefix="", prefix_sep="")
    venues_onehot.loc[:, 'Neighborhood'] = venues['Neighborhood'] 
    venues_onehot.insert(1, 'City', venues['City'])

    neighborhood_venues = venues_onehot.groupby(["Neighborhood"], as_index=False).mean()
    print(neighborhood_venues.head())
    return neighborhood_venues

def rank_venues_by_frequency(neighborhood_venues):
    # create columns according to number of top venues
    columns = ['Neighborhood']
    for ind in np.arange(num_top_venues):
        try:
            columns.append('{}{} Most Common Venue'.format(ind+1, indicators[ind]))
        except:
            columns.append('{}th Most Common Venue'.format(ind+1))

    # create a new dataframe
    neighborhood_top_venues = pd.DataFrame(columns=columns)
    neighborhood_top_venues['Neighborhood'] = neighborhood_venues['Neighborhood']

    for ind in np.arange(neighborhood_venues.shape[0]):
        neighborhood_top_venues.iloc[ind, 1:] = return_most_common_venues(neighborhood_venues.iloc[ind, :], num_top_venues)

    return neighborhood_top_venues

def request_plot_save_venues(city_name=''):
    # Helper to request, plot, and save city venues, given city name
    if not city_name:
        return
    
    trimmed_city_name = "".join(re.findall("[a-zA-Z]+", city_name))

    try:
        geo_df = gpd.read_file(f'data/{trimmed_city_name}_grid.geojson')
    
    except:
        print('Exception occurred. Unable to find file')
        return

    venues_list = search_city_venues(city_name, grid_gdf=geo_df.geometry)
    venues = pd.DataFrame(venues_list)

    plt.scatter(x='Venue Latitude', y='Venue Longitude', data=venues)
    plt.show()

    venues.to_csv(f'data/{trimmed_city_name}_grid_venues.csv')