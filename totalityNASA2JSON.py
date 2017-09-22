import re
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def totalityNASA2JSON(totalityfile, outputGeoJSON):
    '''
    USAGE: 
    Converts raw text file of NASA eclipse path data into formatted GeoJSON file 
    containing both the totality path center-line and the polygon enclosing the 
    region of totality. Also creates a dataframe of the same information.
    
    ARGUMENTS:
    totalityfile - text file containing raw data from NASA
    outputGeoJSON - output location for generated GeoJSON
    
    RETURNS:
    df - dataframe of eclipse path data extracted from "totalityfile"
    '''
    
    with open(totalityfile, 'r') as tf:
        totalitydata = tf.read()
    
    tim = r'(\d+:\d+)'
    crd = r'(\d+) ([\d.]+)(\w) (\d+) ([\d.]+)(\w)' 
    values = re.findall(r'%s   %s  %s  %s' % (tim, crd, crd, crd), totalitydata)
    df = pd.DataFrame(values)
    df.replace(to_replace = 'N', value = 1, inplace = True)
    df.replace(to_replace = 'W', value = -1, inplace = True)

    for i in range(1, 18, 3):
        degrees = pd.to_numeric(df[i])
        minutes = pd.to_numeric(df[i + 1])
        sign = df[i + 2]
        df[i] = sign * (degrees + minutes/60)
        
    df = df[[0] + list(range(1,18,3))]
    df.columns = ['Time', 'NLat', 'NLon', 'SLat', 'SLon', 'CLat', 'CLon']
    df['NorthernLonLat'] = df[['NLon','NLat']].values.tolist()
    df['SouthernLonLat'] = df[['SLon','SLat']].values.tolist()
    df['CentralLonLat'] = df[['CLon','CLat']].values.tolist()
    df = df[['Time', 'NorthernLonLat', 'SouthernLonLat', 'CentralLonLat']]

    print('Creating GeoJSON from NASA Eclipse Path Data...')
    geoJSON = {}
    geoJSON['type'] = 'FeatureCollection'

    center = {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": list(df['CentralLonLat'])
        },
        "properties": {
            "Name" : 'Central line of totality'
        }
    }

    fore = list(df['NorthernLonLat'])
    back = list(reversed(list(df['SouthernLonLat'])))
    start = [fore[0]]

    limits = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [fore + back + start]
        },
        "properties": {
            "Name" : 'Region of totality'
        }
    }

    featurelist = [center, limits]

    geoJSON['features'] = featurelist

    with open(outputGeoJSON, 'w') as f:
        json.dump(geoJSON, f)
    
    print('Eclipse path GeoJSON created and saved to "%s"' % outputGeoJSON)
    
    return df

def centerEclipseJSON(df, outputCenterJSON):
    '''
    USAGE:
    Interpolate NASA coordinates to get centerline coordinates every 30s.
    Outputs a new GeoJSON with just points along the totality centerline.
    
    ARGUMENTS:
    df - dataframe created from totalityNASA2JSON
    outputCenterJSON - output location for generated GeoJSON
    '''    
    
    df['CentralLonLat']
    coordlist = list(df['CentralLonLat'])
    interp = []
    
    print('Interpolating coordinates...')
    for idx, val in enumerate(coordlist):
        A = np.array(val)
        interp.append(list(A))
        if idx < len(df) - 1:
            B = np.array(coordlist[idx + 1])
            diff = B - A
            for i in [1, 2, 3]:
                v = A + i/4*diff
                interp.append(list(v))

    t0 = datetime(2017, 8, 21, 16, 50, 0) # first time in data collection
    timelist = []
    for i in range(len(interp)):
        t = timedelta(seconds = i * 30) + t0
        timelist.append(str(t.time()))

    timeseries = pd.Series(timelist)
    interpseries = pd.Series(interp)
    inter_df = pd.DataFrame(timeseries, columns = ['Time'])
    inter_df['CentralLonLat'] = interpseries
    inter_df

    features = []
    for i in range(len(inter_df)):
        point = {"type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": inter_df.iloc[i]['CentralLonLat']
            },
            "properties": {
                "Time" : inter_df.iloc[i]['Time'] 
            }
        }
        features.append(point)

    centerJSON = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(outputCenterJSON, 'w') as f:
        json.dump(centerJSON, f)
        
    print('Coordinates interpolated and saved to "%s".' % outputCenterJSON)

##### ------------------------------------- MAIN ------------------------------------- #####
    
def main():
    totalityfile = 'Resources/2017_08_21_NASAEclipsePath.txt'
    outputGeoJSON = 'Resources/eclipseGeoJSON.json'
    outputCenterJSON = 'Resources/eclipseCenterJSON.json'
    df = totalityNASA2JSON(totalityfile, outputGeoJSON)
    centerEclipseJSON(df, outputCenterJSON)
    
if __name__ == '__main__':
    main() 