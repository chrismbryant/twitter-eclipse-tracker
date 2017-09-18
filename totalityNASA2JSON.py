import json
import pandas as pd

def totality2JSON(totalityfile, outputGeoJSON):
    '''
    USAGE: 
    Converts raw text file of NASA eclipse path data into formatted GeoJSON file 
    containing both the totality path center-line and the polygon enclosing the 
    region of totality.
    
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
        
    return df

##### ------------------------------------- MAIN ------------------------------------- ##### 

def main():
    totalityfile = 'Resources/2017_08_21_NASAEclipsePath.txt'
    outputGeoJSON = 'Resources/eclipseGeoJSON.json'
    df = totality2JSON(totalityfile, outputGeoJSON)
    
if __name__ == '__main__':
    main() 