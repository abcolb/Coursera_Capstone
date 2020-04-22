import pandas as pd
import numpy as np

import geopandas as gpd

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

# Define grid generator as inputs to foursquare venue search
def generate_square_grid(geometry, threshold=0.05):
    """
    Adapted from https://snorfalorpagus.net/blog/2016/03/13/splitting-large-polygons-for-faster-intersections/
    """
    bounds = geometry.bounds
    geom = geometry

    # Check if threshold is appropriate for bounding box
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]

    if width > 10 or height > 10:
        # prevents too many grid items per city
        threshold *= 10
        print('adjusted threshold', threshold)
    if width > 5 or height > 5:
        # prevents too many grid items per city
        threshold *= 4
        print('adjusted threshold', threshold)
    elif width > 2 or height > 2:
        # prevents too many grid items per city
        threshold *= 2
        print('adjusted threshold', threshold)

    x_min = int(bounds[0] // threshold)
    x_max = int(bounds[2] // threshold)
    y_min = int(bounds[1] // threshold)
    y_max = int(bounds[3] // threshold)
    
    grid = []
    for i in range(x_min, x_max+1):
        for j in range(y_min, y_max+1):
            b = box(i*threshold, j*threshold, (i+1)*threshold, (j+1)*threshold)
            g = geom.intersection(b)
            if g.is_empty:
                continue
            is_polygon = isinstance(g, (polygon.Polygon, multipolygon.MultiPolygon))
            if is_polygon:
                grid.append(g)
    return grid 

# Define Foursquare `/venues/VENUE_ID/likes` helper
def fetch_venue_likes(venue_id):
    url = "https://api.foursquare.com/v2/venues/{}/likes?client_id={}&client_secret={}&v={}".format(
        venue_id,
        CLIENT_ID, 
        CLIENT_SECRET, 
        VERSION
    )

    results = requests.get(url).json()
    time.sleep(0.3)

    if results["meta"]["code"] != 200:
        print('Status', results["meta"]["code"])
        return None
    
    response = results["response"]
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

# Define '/venues/categories' helper
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
