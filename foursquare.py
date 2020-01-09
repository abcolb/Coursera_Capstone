import pandas as pd
import numpy as np

import requests

import category_encoders as ce

CLIENT_ID = '' # your Foursquare ID
CLIENT_SECRET = '' # your Foursquare Secret
VERSION = '20180605' # Foursquare API version

# Define Foursquare `/explore` helper

def fetch_venues(neighborhoods, cities, latitudes, longitudes, radius=250, LIMIT=100):
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
                    res.append({'name': subcategory, 'category': category})
    

            category = r['name']
            append_categories(r['categories'], category)

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

    print(neighborhood_top_venues.head())
    print(neighborhood_top_venues.shape)
    return neighborhood_top_venues