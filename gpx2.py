from selenium import webdriver
import time
import re
import requests
from selenium.webdriver.chrome.service import Service as ChromeService
import geopandas as gpd
import json


def get_js_urls(url):
    # Create a Chrome WebDriver instance
    chrome_driver_path = "./chromedriver_mac_arm64/chromedriver"  # Replace with the actual path to chromedriver

    # Create a Chrome WebDriver instance with the specified path
    #driver = webdriver.Chrome(chrome_driver_path)
    #driver = webdriver.Chrome()
    service = ChromeService(executable_path=chrome_driver_path)

    driver = webdriver.Chrome(service=service)

    try:
        # Enable performance logging
        driver.execute_script("performance.setResourceTimingBufferSize(300)")

        # Navigate to the given URL
        driver.get(url)

        # Wait for the page to load (you may need to adjust the waiting time)
        time.sleep(5)

        # Get the performance logs containing network requests
        logs = driver.execute_script("return window.performance.getEntriesByType('resource')")

        # Extract all URLs from the logs
        js_urls = set()
        for log in logs:
            url = log['name']
            js_urls.add(url)

        return js_urls

    finally:
        # Close the WebDriver after usage
        driver.quit()
def find_urls_with_pattern(text, pattern):
    # Compile the regular expression pattern
    regex = re.compile(pattern)

    # Find all matches in the text
    matches = regex.findall(text)

    return matches

def getJSON(url):
    # Replace 'your_url_here' with the URL of the website you want to analyze
    js_urls = get_js_urls(url)
    
    pattern = r'https://map.schweizmobil.ch/api/4/tracks/\d+'

    # Find all URLs matching the pattern

    # Print the matched URLs
    
    cnt=0

    url2=[]

    for js_url in js_urls:
        urls = find_urls_with_pattern(js_url, pattern)
        cnt+=1
        for ul in urls:
            if ul not in url2:
                url2.append(ul)
    print(url2)

    if len(url2) > 0:
        response = requests.get(url2[0])
        data = response.json()
        return data
        
#print(data)

import pyproj

def utm_to_latlon(utm_easting, utm_northing):
    utm_coordinate_system = pyproj.CRS.from_epsg(21781)  # EPSG code for UTM Zone 32T
    latlon_coordinate_system = pyproj.CRS.from_epsg(4326)  # EPSG code for WGS 84

    transformer = pyproj.Transformer.from_crs(utm_coordinate_system, latlon_coordinate_system, always_xy=True)

    lon, lat = transformer.transform(utm_easting, utm_northing)

    return lat, lon


if __name__ == "__main__":

    #url = 'https://map.schweizmobil.ch/?bgLayer=pk&land=wanderland&lang=fr&layers=Wanderwegnetz%2CCableway%2CTrain&photos=no&logo=yes&detours=yes&season=summer&resolution=1&E=2527375&N=1170628&trackId=166258'
    url = input("provide url:")
    data = getJSON(url)

    jsn = '''<?xml version="1.0" encoding="utf-8"?>
<gpx creator="MySchweizMobil - https://map.schweizmobil.ch/" version="1.1"
    xmlns="http://www.topografix.com/GPX/1/1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">
    '''

    #with open("test.json", 'r') as myfile:
    #   data= json.loads(myfile.read())
    
    name = data['properties']['name']

    profile = data['properties']['profile']
    
    trk='<trk>'
    trk += '<name>'+name+'</name><trkseg>'

    minLat=9999999
    minLon=9999999
    maxLat=0
    maxLon=0

    from ast import literal_eval
    profile = literal_eval(profile)
    for p in profile:

        utm_easting = p[0]
        utm_northing = p[1]
         
        lat, lon = utm_to_latlon(utm_easting, utm_northing)

        trk+='<trkpt lat="'+str(lat)+'" lon="'+str(lon)+'"><ele>'+str(p[2])+'</ele></trkpt>'
        minLat = lat if lat<minLat else minLat
        minLon = lon if lon<minLon else minLon
        maxLat = lat if lat>maxLat else maxLat
        maxLon = lon if lon>maxLon else maxLon

    trk += '</trkseg></trk>'

    jsn += '<metadata><name>'+name+'</name><bounds maxlat="'+str(maxLat)+'" maxlon="'+str(maxLon)+'" minlat="'+str(minLat)+'" minlon="'+str(minLon)+'" /></metadata>'
    jsn += trk + '</gpx>'
    with open("track.gpx", 'w') as myfile:
        myfile.write(jsn)
