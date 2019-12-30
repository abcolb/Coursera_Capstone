## Do the World’s Financial Centers exhibit internal or external similarity?

### Introduction
Do the world’s top ten financial centers’ neighborhoods have more internal commonality? Or do cities share neighborhood venue distributions? The Global Financial Centers Index (GFCI), which ranks cities based on indicators such as economic prowess, financial strength, and its share trading index, has identified the following cities, in descending order, as the top financial cities in the world: _NYC, London, Hong Kong, Singapore, Shanghai, Tokyo, Toronto, Zurich, Beijing, Frankfurt_

Existing research in ‘city similarity’ includes clustering and pairing similar cities and identifying dissimilar ones. One useful application is helping people identify a city similar to their own to move or travel to. Local officials may look to a sister neighborhood for budgeting or planning. Law enforcement might find similarities with cities other than their own useful for preventing crime. Traditionally, indicators such as population, education, healthcare, culture, and climate are considered as clustering features. This analysis will consider venue distribution by neighborhood as a city's profile.

k-means is a simple, widely-used clustering technique appropriate for unlabeled data. Preliminary k-means clustering (k=5) of NYC and Toronto neighborhoods produced reasonable clusters, identifying hubs of transportation, food, outdoor activity, and coffee, illustrating how a financial center of a country has distributed its resources. To cluster cross-city, one can input unlabeled cities’ neighborhoods en masse into the same clustering model, then examine the output to determine if clusters span many cities or tend to group by city.

Will specialty shops like bubble tea cafes, empanada stands, and cheese shops that are wildly popular and localized to one region skew results in direction of internal sameness? Or is it the same grouping of venues in each city that makes these financial centers the best in the world?

_Keywords: city similarity, neighborhood clustering, k-means clustering_

### Data

Like previous analyses, data mining will be required to assemble lists of neighborhoods of each city. Wikipedia is a sufficient resource but varies greatly in formatting, so every page needs to be scraped and parsed independently.

- NYC: https://geo.nyu.edu/catalog/nyu_2451_34572
- London: https://en.wikipedia.org/wiki/List_of_London_boroughs
- Hong Kong: https://en.wikipedia.org/wiki/List_of_places_in_Hong_Kong
- Singapore: https://en.wikipedia.org/wiki/List_of_places_in_Singapore
- Shanghai: https://en.wikipedia.org/wiki/List_of_township-level_divisions_of_Shanghai
- Tokyo: https://en.wikipedia.org/wiki/Category:Neighborhoods_of_Tokyo
- Toronto: https://en.wikipedia.org/wiki/List_of_postal_codes_of_Canada:_M
- Zurich: https://en.wikipedia.org/wiki/Subdivisions_of_Z%C3%BCrich
- Beijing: https://en.wikipedia.org/wiki/List_of_township-level_divisions_of_Beijing
- Frankfurt: https://en.wikipedia.org/wiki/Category:Districts_of_Frankfurt

Since neighborhoods are not legal designations but instead represent cultural boundaries that change, it should be noted that there are many ways of geographically dividing populated regions, especially when they are densely populated. Other names for neighborhood that were considered include: boroughs, subdistricts, township-level divisions, and xiang. Macroscopic names, such as areas, regions, districts, and boroughs (in the case of NYC) were avoided.

Once lists of cities’ neighborhoods are mined, a list of venues can be generated for each neighborhood by accessing Foursquare Places API venue search, which accepts neighborhood name and radius as input and returns a list of venues. These venues will then be ranked by frequency and normalized, generating a profile of each neighborhood by its venues as inputs for the clustering model.

### References

ArcGis Desktop Tools Reference (2018) How Similarity Search works. https://desktop.arcgis.com/en/arcmap/10.3/tools/spatial-statistics-toolbox/how-similarity-search-works.htm. Accessed 29 Dec 2019.

Heredia, Karim (2016) Visualizing city similarity. https://teleport.org/blog/2016/02/visualizing-city-similarity. Accessed 29 Dec 2019.

Misachi, John (2019) Which Cities Are The World's Financial Centers?https://www.worldatlas.com/articles/the-world-s-top-financial-cities.html. Accessed 29 Dec 2019.
