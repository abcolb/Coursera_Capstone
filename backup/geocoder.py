import numpy as np

import matplotlib.cm as cm
import matplotlib.colors as colors

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

import folium

# Initialize locator
locator = Nominatim(user_agent="neighborhoods_geocoder")

# Validate locator with sample neighborhood name
# location = locator.geocode("Bergen-Enkheim, Frankfurt, Germany")
# print(location)

geocode = RateLimiter(locator.geocode, min_delay_seconds=1)

def geocode_with_fallback(neighborhood, city):
    try:
        return geocode(neighborhood + ', ' + city)
    except:
        return geocode(neighborhood)

def enrich_neighborhoods_with_geocoder(df, address):
    # use .loc for column addition to avoid SettingWithCopyWarning
    df.loc[:, 'Location'] = df['Neighborhood'].apply(lambda neigh: geocode(neigh + ', ' + address) if neigh else None)
    df.loc[:, 'Point'] = df['Location'].apply(lambda loc: tuple(loc.point) if loc else None)

    df.loc[:, 'Latitude'] = df['Point'].apply(lambda t: t[0] if t else None)
    df.loc[:, 'Longitude'] = df['Point'].apply(lambda t: t[1] if t else None)

    df.drop(["Location", "Point"], axis=1, inplace=True)
    return

def map_neighborhoods(df, address):
    location = geocode(address)
    latitude = location.latitude
    longitude = location.longitude

    m = folium.Map(location=[latitude, longitude], zoom_start=10, zoom_control=False)

    for lat, lng, label in zip(df['Latitude'], df['Longitude'], df['Neighborhood']):
        label = folium.Popup(label, parse_html=True)
        folium.CircleMarker(
            [lat, lng],
            radius=2,
            popup=label,
            color='blue',
            fill=True,
            fill_color='#3186cc',
            fill_opacity=0.5
        ).add_to(m)
    return m

def map_clusters(df, k, address):
    location = geocode(address)
    latitude = location.latitude
    longitude = location.longitude

    c = folium.Map(location=[latitude, longitude], zoom_start=10, zoom_control=False)

    # set color scheme for the clusters
    x = np.arange(k)
    ys = [i + x + (i*x)**2 for i in range(k)]
    colors_array = cm.rainbow(np.linspace(0, 1, len(ys)))
    rainbow = [colors.rgb2hex(i) for i in colors_array]

    # add markers to the map
    markers_colors = []
    for lat, lon, poi, cluster in zip(df['Latitude'], df['Longitude'], df['Neighborhood'], df['Cluster Labels']):
        label = folium.Popup(str(poi) + ' | Cluster ' + str(cluster), parse_html=True)
        folium.CircleMarker(
            [lat, lon],
            radius=3,
            popup=label,
            color=rainbow[cluster-1],
            fill=True,
            fill_color=rainbow[cluster-1],
            fill_opacity=0.5).add_to(c)
        
    return c