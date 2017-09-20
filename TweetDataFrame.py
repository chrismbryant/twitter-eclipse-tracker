print('Importing libraries...')

import re                                  # for parsing through data files
import os                                  # for checking to see if files already exist on disk
import numpy as np                         # for numerical analysis
import json                                # for JSON processing
import pandas as pd                        # for dataframe processing
import requests                            # for API interactions
import matplotlib.pyplot as plt            # for plotting data
from datetime import datetime, timedelta   # for analysis of temporal data features
from tqdm import tqdm                      # for monitoring progress of time-consuming for-loops

print('Libraries imported.')

class TweetDF():
    '''
    Tweet Dataframe class for creating and manipulating a pandas-dataframe of geo-tagged Twitter data.
    '''
    
    df = pd.DataFrame([])                                   # Initialize empty dataframe for Twitter data
    tallyframe = pd.DataFrame([])                           # Initialize empty dataframe for county tallies 
    no_code = []                                            # Initialize List of tweet indices for which no county code could be found
    mincolor = 0                                            # Initialize minimum color value
    county_tally = {}                                       # Initialize dictionary of tallies/county/time
    time_params = ''                                        # Initialize time parameter string for file-labeling
    
    state_file = 'Resources/state_table.csv'                # Location from where to retrieve state name/code info
    
    revgeofile = 'Resources/revgeodata.json'                # Location for storing reverse geocoding data
    timetallyroot = 'Resources/Tally/timetallydata.json'    # Location for storing list of arrays of tweet tallies
    countytallyfile = 'Resources/countytallydata.json'      # Location for storing list of tweet county codes
    censusdatafile = 'Resources/censusdata.json'            # Location for storing census data for each county
    countycolorroot = 'Resources/Color/countycolordata.csv' # Location for storing numerical tweet data per county
    topoJSONfile = 'Resources/USTopoJSON.json'              # Location for storing US TopoJSON data from d3js.org
    tweetGeoJSONfile = 'Resources/tweetGeoJSON.json'        # Location for storing GeoJSON encoding of tweet events
    
    def __init__(self, datafilepath):
        '''
        Initialize TweetDF object.
        '''
        
        self.datafilepath = datafilepath                    # Location from where to retrieve JSON tweet data
        
    def tweetfile2df(self):
        '''
        USAGE: 
        Creates a pandas dataframe of tweet data from a tweet data file
        '''
        
        if self.df.empty:
            
            tweet_list = []
            
            print('Adding Twitter data to dataframe...')
            with open(self.datafilepath, 'r') as f:
                text = f.read()
                
            tweets = re.findall(r'({"USER".*?]]]})', text) # Creates a list of tweet data strings
            
            for tweet in tweets:
                tweet_list.append(json.loads(tweet))       # Loads JSON from each tweet data string
            
            self.df = pd.DataFrame(tweet_list)
            self.df.rename(columns={'PLACE': 'Place', 'USER': 'User', 'TEXT': 'Text'}, inplace=True)
            
            print('Twitter data added to dataframe.')
            
        else:
            print('No action: dataframe already populated.')
    
    def mkDatetime(self):
        '''
        USAGE: Adds a column of datetime values to replace the "CREATED AT" strings.
        '''
        
        if 'Datetime' not in self.df.keys():
            print('Creating datetime labels...')
            datetimelist = []
            createdatlist = list(self.df['CREATED AT'])
            for idx, t in enumerate(createdatlist):
                match = re.search(r'\d\d:\d\d:\d\d', createdatlist[idx])
                time = datetime.strptime('2017 Aug 21 ' + match.group(0), '%Y %b %d %H:%M:%S')
                datetimelist.append(time)
                
            del self.df['CREATED AT']
            self.df['Datetime'] = datetimelist
            print('Datetime labels added to tweet dataframe.')
        
        else:
            print('No action: Datetime labels already added to tweet dataframe.')
    
    def stateNoState(self):
        '''
        USAGE: 
        Parses through tweets to determine whether or not each tweet should be regarded as having been 
        sent from a point location rather than from the broad region of "state". A column of values is 
        added to the tweet dataframe under the name "State" specifying this, where the state code string
        is listed if the state condition is met, and "False" is listed if it is not. This method also 
        throws out all tweets which have no location more specific than "United States" identified. 
        '''
        if 'Place' not in self.df.keys():
            self.tweetfile2df()
        
        if 'State' not in self.df.keys():
            print('Determining location precision of tweets...')
            
            # Create a dictionary of "state name : state code" pairs
            with open(self.state_file, 'r') as s:
                state_df = pd.read_csv(s)
            state_df = state_df.loc[:,['name', str('fips_state')]]
            fips_state = ['0' + str(x) if len(str(x)) == 1 else str(x) for x in list(state_df['fips_state'])]
            state_dict = dict(zip(list(state_df['name']), fips_state))
            
            state = []
            trash = []
            for idx, place in enumerate(list(self.df['Place'])):
                if place[0] == 'admin':
                    if place[1][-5:] == ', USA':                # only states (and DC) end with this string
                        state.append(state_dict[place[1][:-5]]) # label tweet with state code

                    else:
                        state.append(False)     # label tweet as not requiring broad state treatment
                
                elif place[0] == 'country':
                    trash.append(idx)           # collect a list of tweets to throw away
                
                else:
                    state.append(False)
            
            self.df.drop(self.df.index[trash], inplace=True)  # throw out tweets labeled only as "country"
            self.df['State'] = state            # add state-level precision precision column to tweets.df
            self.df = self.df.reset_index(drop=True)
            print('Tweet location state-precision status entered as tweet dataframe column "State".')
            
    def avgLONLAT(self):
        '''
        USAGE: 
        Calculates average GPS coordinates from each tweet bounding box, adding the average 'LON' 
        and 'LAT' to the tweet dataframe.
        '''
        
        if 'State' not in self.df.keys():
            self.stateNoState()
        
        # Careful: Twitter gives coordinates in [LON, LAT] (opposite the ISO 6709 convention!)
        if not (('LON' and 'LAT') or ('listLATLON')) in self.df.keys():
            
            coords = [(x[-1]) for x in self.df['Place'].tolist()]
            avgcoords = np.array([np.ndarray.flatten(np.mean(np.array(coords[idx]),1)) for idx in range(len(coords))])
            
            lon = list(avgcoords[:,0])
            lat = list(avgcoords[:,1])
            self.df['LON'] = lon
            self.df['LAT'] = lat
            print('Average \"LON\" and \"LAT\" coordinates added to dataframe.')
            
        else:
            print('No action: Average \"LON\" and \"LAT\" coordinates already in dataframe.')
    
    def listLATLON(self):
        '''
        USAGE:
        Combines "LAT" and "LON" to create a [LAT, LON] list for each tweet in the tweet dataframe, 
        for use with the Coordinates to Politics Data Science Toolkit POST API. Also removes original 
        ['LAT'] and ['LON'] columns from tweet dataframe.
        '''
        
        if 'listLATLON' not in self.df.keys():
            
            if not ('LON' and 'LAT') in self.df.keys():
                self.avgLONLAT()
            
            self.df['listLATLON'] = self.df[['LAT','LON']].values.tolist()
            del self.df['LAT'], self.df['LON']
            print('"[LAT, LON]" lists added to dataframe. "LAT" and "LON" removed from dataframe.')
            
        else:
            print('No action: "[LAT, LON]" lists already in dataframe.')
       
    def revGeocodePOST(self):
        '''
        USAGE: 
        Retrieves political region info on coordinates using the "Coordinates to Politics" API from 
        datasciencetoolkit.org/coordinates2politics. Uses a series of POST requests (rather than GET 
        requests) to expedite the retrieval process, then saves the results in a JSON file. If the 
        file already exists, this method performs no action.
        '''
        # For some reason, if the length of my JSON list exceeds exactly 576, I receive the following error message:
        #  >>> JSONDecodeError: Expecting value: line 1 column 1 (char 0)
        # I can't figure out how to fix it, so for now, I'll just gather data at a max of 500 coordinate pairs at a time.
        
        if not os.path.exists(self.revgeofile):
            
            if 'listLATLON' not in self.df.keys():
                self.listLATLON()
            
            limit = 500
            size = len(self.df['listLATLON'])
            start = 0
            response = []

            tic = datetime.now()

            while start < size:
                stop = start + limit
                if stop >= size:
                    stop = size    

                coords = list(self.df['listLATLON'][start:stop])
                coords_json = json.dumps(coords)
                url = 'http://www.datasciencetoolkit.org/coordinates2politics'
                print("Processing tweets %d - %d..." % (start, stop))
                response += requests.post(url, data=coords_json).json()
                start += limit

            print("Done! Data on %s coordinates were retrieved." % len(response))
            toc = datetime.now()
            print("Total processing time: %s" % str(toc-tic))
            print("Now saving to file...")

            with open(self.revgeofile, 'w') as rf:
                json.dump(response, rf)
                print('Reverse-geocoded data saved to "%s".' % self.revgeofile)
        
        else:
            print('No action: Reverse-geocoded data already saved to "%s".' % self.revgeofile)
    
    def getCensusData(self):
        '''
        USAGE: GETs census data from the US Census Bureau API and saves it to a file on disk. 
        '''

        # request population estimate, county name, and county code for July 1, 2016 (most recent data available through API)
        url = 'https://api.census.gov/data/2016/pep/population?'
        req = 'get=POP,GEONAME&for=COUNTY:*&DATE=9'
        url += req

        print('Getting census data...')
        countypop = requests.get(url).json()
        with open(self.censusdatafile, 'w') as cdf:
            json.dump(countypop, cdf)

        print('Census data saved to "%s".' % self.censusdatafile)
    
    def countyExtract(self):
        '''
        USAGE:
        
        Extracts a list of county codes for each tweet and distributes a single tally proportionally
        between each associated county. Adds results to a list, which it then saves to a JSON file
        self.countytallyfile. If no code can be found for a given tweet, the tweet is added to the list
        with the label {datetime: {'null': 0}}.
        
        Usually, for each tweet sent from a county, that county gets one tally. Because of fuzziness 
        built into the coordinates2politics algorithm (from datasciencetoolkit.org), however, some 
        tweets are associated with multiple counties. Additionally, some tweets only broadcast
        their geo-location at the state-level, so there is ambiguity across the entire state as to 
        which county the tweet was sent from. In these multi-county cases, the tally of each tweet is
        divided proportionally among all the associated counties according to population (e.g., 
        if a tweet is associated with 2 counties where County A normaly has a population of 30 and 
        County B normally has population of 70, County A receives 3/10 of a tally and County B receives 
        7/10 of a tally.
        
        If the tweet location has only state-level precision, codes for every county in the state are 
        retrieved from "state_file". If the tweet location has point-precision, this method extracts 
        the corresponding county code from the revgeodata file when possible. If the county code is not 
        available, the value None is given. If multiple county codes are found in the "revgeodata" file 
        for a tweet (due to a nearness of the considered coordinate to a county border), all codes are 
        collected. When finished extracting, county codes are saved to "countytallyfile" along with
        their share of a tally value and added to the tweet dataframe.

        If the tweet county code file already exists, the extraction process is bypassed and codes are 
        added directly to the tweet dataframe from the county code file. 
        '''
        
        if 'CountyCode' in self.df.keys():
            print('No action: County codes already added to dataframe')
        
        else:
            
            if os.path.exists(self.countytallyfile):
                print('Loading tweet county codes and tally distributions from "%s"...' % self.countytallyfile)
                with open(self.countytallyfile, 'r') as cf:
                    counties = json.load(cf)
            
            else:
                
                ##### --------------------------------- Helper Function --------------------------------- #####
                
                def calculateTallies(codes):
                    '''
                    USAGE: Calculate appropriate tally distribution across a list of county codes.
                    ARGUMENTS: codes - list of 5-digit CountyCode strings "#####"
                    RETURNS: codetallydict - dictionary of {"code": tally} pairs
                    '''

                    codetallydict = {}

                    if codes and codes not in [[None],[]]:
                        if len(codes) == 1:
                            codetallydict[codes[0]] = 1
                        else:
                            df = cd_df[cd_df['fips'].isin(codes)]  # Create a smaller dataframe with just info on codes
                            pops = pd.to_numeric(df['POP'])        # series of population counts
                            tot = pops.sum()                       # combined population of all counties in series

                            codetallydict = dict(zip(list(df['fips']), list(pops/tot)))

                    else:
                        codetallydict = {None: 0}

                    return codetallydict
                
                ##### ---------------------------------- Control Flow ---------------------------------- #####
                
                if not os.path.exists(self.censusdatafile):
                    self.getCensusData()
                
                # Load census data for county population reference
                print('Loading "%s"...' % self.censusdatafile)
                with open(self.censusdatafile, 'r') as cdf:  
                    censusdata = json.load(cdf)
                cd_df = pd.DataFrame(censusdata[1:])
                cd_df.columns = censusdata[0]
                cd_df['fips'] = cd_df['state'] + cd_df['county']
                cd_df = cd_df[['POP','state','fips']]
                
                # Load reverse geocoding file for county code extraction
                print('Loading "%s"...' % self.revgeofile)
                with open(self.revgeofile, 'r') as fp:
                    revgeodata = fp.read();
                rgddf = pd.DataFrame(json.loads(revgeodata))
                del rgddf['location']

                counties = []
                printer = False # Set to True for feedback on the presence or absence of codes during extraction.
                
                if 'State' not in self.df.keys():
                    self.stateNoState()
                
                state = list(self.df['State'])    
                
                print('Extracting county codes and calculating tally distributions...')
                
                for idx in tqdm(range(len(rgddf['politics']))):
                    
                    timestamp = str(self.df['Datetime'][idx])
                    
                    try:

                        # If better than state-level precision, then...
                        if not state[idx]: 
                            codes = list(pd.DataFrame(rgddf['politics'][idx])['code'])
                            codes = [''.join(code.split('_')) for code in codes if re.match(r'^\d\d_\d\d\d$', code)]
                            if not codes:
                                codes = [None]

                        else:
                            state_code = state[idx]
                            fips = cd_df[cd_df['state'] == state_code]['fips']
                            codes = list(fips)

                        codetallydict = calculateTallies(codes)
                        counties.append({timestamp: codetallydict})

                    except:
                        if printer:
                            print('%d - No codes found: "%s"' % (idx, rgddf['politics'][idx]))

                        self.no_code.append(idx)
                        counties.append({timestamp: {'null':0}})
                    
                print('Saving county codes and tally distributions to "%s"...' % self.countytallyfile)
                
                with open(self.countytallyfile, 'w') as cf:
                    json.dump(counties, cf)
                    
                print('County codes and tally distributions saved to "%s".' % self.countytallyfile)
                        
            self.df['CountyCode'] = counties
            print('County codes and tally distributions added to tweet dataframe.')

    def timeTally(self, increment, block_length, t0=False):
        '''
        USAGE: 
        Create a dictionary and dataframe of tally counts per county such that tweets tallies
        are added up within a specified-length block of time, which is shifted in fixed
        increments forward in time. This generates a time-averaged movie of Twitter activity,
        where each frame of the movie represents tally data from a single time block.
        
        ARGUMENTS:
        increment - length of time between consecutive time blocks (in minutes)
        block_length - length (>= dt) of time block (in minutes)
        t0 - optional: desired datetime-formatted start-time of initial time block

        RETURNS:
        county_tally - master tally dictionary containing {"CountyCode": 
            np.array([Tally, ... , Tally])} pairs

        '''

        ##### ---------------------------- Helper Functions ---------------------------- #####

        def str2date(datetime_string):
            '''
            USAGE: Turn a specifically formatted string into a datetime object
            ARGUMENT: datetime_string - (YY-mm-DD HH:MM:SS)-formatted string
            RETURNS: date - datetime formatted object
            '''
            date = datetime.strptime(datetime_string, '%Y-%m-%d %H:%M:%S')
            return date

        def getBlock(t):
            '''
            USAGE: 
            Create a new dataframe which is a subset spanning a block of time in the original
            dataframe. Specifically, for a given starting time t, return a dataframe with all 
            the rows of df which have a datetime value between (t) and a later time
            (t + deltaT).

            ARGUMENT:
            t - starting time of block

            RETURNS:
            timeblock - dataframe of {Datetime: {codetallydict}} pairs spanning a block of time
            '''

            timeblock = df[(df.Datetime >= t) & (df.Datetime < t + deltaT)]
            return timeblock 

        def blockTally(timeblock):
            '''
            USAGE:
            For a given list of {Datetime: {codetallydict}} pairs, create a dictionary of
            {"CountyCode": Tally} pairs by summing over all the tallies in 
            codetallydict.

            ARGUMENT:
            timeblock - dataframe of {Datetime: {codetallydict}} pairs spanning a block of time

            RETURNS:
            block_tally - dictionary of {"CountyCode": Tally} pairs generated from values
                within the input timeblock dataframe
            '''

            # Initialize all block county code tallies at 0
            block_tally = dict.fromkeys(cd_list, 0)
                        
            for i in range(len(timeblock)):
                codetallydict = timeblock.iloc[i].Codes
                for code in codetallydict:
                    if code != 'null':
                        block_tally[code] += codetallydict[code]

            return block_tally

        def blockCombine(block_tally): ##### RESOLVED: PREVIOUS ISSUES APPENDING LISTS IN LOOP.
            '''
            USAGE:
            Append the tally values within a time block to the master tally dictionary

            ARGUMENT:
            block_tally - dictionary of {"CountyCode": Tally} pairs generated by blockTally()
            ------------------------
            IMPORTANT NOTE:
            I would have liked to implement this procedure by placing either of the two following
            lines of code within the for-loop:

                1. county_tally[c].append(block_tally[c])
                2. county_tally[c] += [block_tally[c]]

            For some reason I still cannot figure out, this actually appends the value of EVERY
            key in the county_tally dictionary on each iteration so that by the end of the loop, 
            each key in the dictionary has the SAME 3220-item list as its corresponding value...

            The code I have actually written in this method appends each new tally value to the 
            list of previously calculated tallies for ONLY the appropriate county code key. 
            '''
            
            for c in self.county_tally:
                self.county_tally[c] = self.county_tally[c] + [block_tally[c]]


        ##### ------------------------------ Control Flow ------------------------------ #####

        if not self.tallyframe.empty:
            print('No action: Tally dataframe already populated.')
            return

        if 'CountyCode' not in self.df.keys():
            self.countyExtract()
        
        self.time_params = '_d%d_delta%d' % (increment, block_length)
        filename = self.timetallyroot.split('.')[0] + self.time_params + '.json'
        
        if os.path.exists(filename): # just load tally data from file
            with open(filename, 'r') as f:
                self.county_tally = json.load(f)
            
        else: # calculate tally data if there is not already a file
            
            if not os.path.exists(self.censusdatafile):
                self.getCensusData()

            # Load census data to get county code list
            with open(self.censusdatafile, 'r') as cdf:
                censusdata = json.load(cdf)
            cd_df = pd.DataFrame(censusdata[1:])
            cd_df.columns = censusdata[0]
            cd_df['fips'] = cd_df['state'] + cd_df['county']
            cd_list = list(cd_df['fips'])

            # Load all tally data
            with open(self.countytallyfile) as ccf:
                codetallydata = json.load(ccf)

            # Load tally data list into dataframe
            k, v = [], []
            for x in codetallydata:
                key = list(x.keys())[0]
                value = list(x.values())[0]
                k.append(str2date(key))
                v.append(value)
            df = pd.DataFrame(np.array([k,v]).transpose(), columns = ['Datetime', 'Codes'])

            # Initialize all county code tallies at []
            self.county_tally = dict.fromkeys(cd_list,[])

            # Format dt and deltaT as deltatime objects
            dt = timedelta(0, increment*60)
            deltaT = timedelta(0, block_length*60)

            # Get start-time
            if t0 == False:
                t = df['Datetime'][0]
            else:
                t = t0
            
            print("Calculating block tallies...")
            block_num = 0
            while t + deltaT < df.Datetime.iloc[-1] or block_num < 1:
                print(t)
                timeblock = getBlock(t)
                block_tally = blockTally(timeblock)
                blockCombine(block_tally)
                t += dt
                block_num += 1

            print("Tallies in all time blocks calculated.")

            print("Writing tally data to file...")
            with open(filename, 'w') as f:
                json.dump(self.county_tally, f)
            print('Tally data written to "%s"' % filename)  
        
        # Create tally dataframe from file
        countytallylist = [[key, tlist] for key, tlist in self.county_tally.items()]
        self.tallyframe = pd.DataFrame(countytallylist, columns=['CountyCode', 'Tally'])
        print('Tally dataframe created with "CountyCode" and "Tally" columns.')
       
    def getCountyPop(self):
        '''
        USAGE: 
        Loads census population data into tally dataframe from a file on disk. If a file containing 
        census data doesn't already exist on disk, this method first GETS population estimates on 
        every US county from the US Census Bureau API, and saves the results to a file. 
        '''
        
        ##### ----------------------------- Helper Functions ----------------------------- ##### 
        
        if not os.path.exists(self.censusdatafile):
            self.getCensusData()
        
        def loadCensusData():
            '''
            USAGE:
            Loads census data into a dataframe from a file (self.censusdatafile) on disk. If the
            file doesn't already exist on disk, it runs getCensusData() to create that file.
            
            RETURNS:
            cd_df - dataframe of census data
            '''
            
            with open(self.censusdatafile, 'r') as cdf:
                censusdata = json.load(cdf)

            cd_df = pd.DataFrame(censusdata[1:])
            cd_df.columns = censusdata[0]
            cd_df.loc[:,'CountyCode'] = cd_df['state'] + cd_df['county']
            cd_df = cd_df.drop(['DATE', 'state', 'county'], axis = 1)
            print('Census data loaded from "%s"...' % self.censusdatafile)
            return cd_df
        
        def mergeCountyPop(): # ISSUE: Must fill with tally values of [0, 0, ... , 0], not 0
            '''
            USAGE: 
            Merges census population data into tally dataframe. If a county code is present
            in the census data but not in the existing tally dataframe, the county is given a
            corresponding tally of 0. The resulting dataframe has keys "CountyCode", 
            "Tally", "Population", and "Geoname".
            '''
            
            cd_df = loadCensusData()
            
            self.tallyframe = pd.merge(self.tallyframe, cd_df, how = 'right', on = ['CountyCode'])
            self.tallyframe.rename(columns={'POP': 'Population', 'GEONAME': 'Geoname'}, inplace=True)
#             self.tallyframe['Tally'] = self.tallyframe['Tally'].fillna(0)
            print('County populations added to tally dataframe.')
            
        ##### ------------------------------ Control Flow ------------------------------ ##### 
        
        if self.tallyframe.empty:
            self.tally()

        # only GET census data from API if censusdatafile doesn't already exist on disk
        if not os.path.exists(self.censusdatafile):
            getCensusData()
        
        mergeCountyPop()
        
    def tally2value(self):
        '''
        USAGE: 
        Converts tally counts to color values (i.e. values for use in color mapping) by scaling
        as a function of county population. 
        
        THEORETICAL BACKGROUND: 
        Since the distribution of population size among counties is roughly log-normal, a simple 
        mapping of {f(tally) --> f(tally/pop)} would result in a uniform distribution if tally counts 
        per county were precisely proportional to county population (thus, our map shading would be 
        uniform: i.e. useless). However, an anomaly in the proportionality between tallies and 
        population would maintain a log-normal distribution after the {f(tally) --> f(tally/pop)}
        mapping. This is useful, since it will illuminate any geographically anomalous Twitter
        activity. 
        
        To map the resulting log-normal distribution to a color scale, we can map the data to a
        normal distribution, then perform feature scaling and mean normalization. In other words, we 
        take the log of the (tally/pop) distribution, subtract out the mean, and divide by the
        standard deviation. This results in a zero-centered normal distribution with a standard
        deviation of 1. For good color contrast, we can set the range of the color scale to [-2, 2] so 
        that in our Javascript map implementation, we can map one color extreme to -2 and the other 
        to 2. Since the distribution is normal, this range encapsulates roughly 95% of the data.
        '''
        
        ##### ----------------------------- Helper Functions ----------------------------- #####
        
        def processValues():
            '''
            USAGE:
            Converts tally and population data into color values by transforming data into a 
            normal distribution with mean = 0 and standard deviation = 1. Updates tally dataframe
            with resulting values. The resulting dataframe has keys "CountyCode", "Tally", 
            "Population", "Geoname", and "Value".
            '''
            
            if 'Value' in self.tallyframe:
                print('No action: Color values already calculated and added to tally dataframe.')
                return
            
            def log_norm2norm():
                
                t_array = np.array(list(self.tallyframe['Tally']))
                p_array = np.array(pd.to_numeric(self.tallyframe['Population']))
                shape = np.shape(t_array)
                v_array = np.zeros(shape)
                
                for i in range(shape[0]):
                    for j in range(shape[1]):
                        if t_array[i][j] and p_array[i]:
                            v_array[i][j] = np.log(t_array[i][j]/p_array[i])
                        else: # eliminate -inf and /0 errors
                            v_array[i][j] = False
                
                return v_array # array
        
            def normScale(myarray):
                
                v_array = log_norm2norm()
                list_noFalse = v_array[np.nonzero(v_array)] # remove "False" terms before processing
                mu = np.mean(list_noFalse)                  # mean
                sigma = np.std(list_noFalse)                # standard deviation
                minimum = min((list_noFalse - mu)/sigma)    # minimum color value
                
                # mean normalization and feature scaling
                shape = np.shape(v_array)
                for i in range(shape[0]):
                    for j in range(shape[1]):
                        if v_array[i][j]:
                            v_array[i][j] = (v_array[i][j] - mu)/sigma
                        else:
                            v_array[i][j] = minimum
                values = []        
                for i in range(shape[0]):
                    values.append(list(v_array[i]))
                
                return values, minimum
            
            value_array = log_norm2norm()
            values, self.mincolor = normScale(value_array)
            self.tallyframe['Value'] = values
        
        def getTopoJSONCounties():
            '''
            USAGE: 
            Creates a set of all county IDs accounted for by a TopoJSON file. This set will 
            be used to populate the tally dataframe with any counties accounted for by the 
            TopoJSON file which are not already present in the tally dataframe.

            RETURNS:
            countyids - set of all county IDs in topoJSONfile
            '''
            
            topoJSONurl = 'https://d3js.org/us-10m.v1.json'
            topoJSONfile = self.topoJSONfile

            if not os.path.exists(topoJSONfile):
                print('Getting US TopoJSON data...')
                topoJSONdata = requests.get(topoJSONurl).json()
                with open(topoJSONfile, 'w') as tjf:
                    json.dump(topoJSONdata, tjf)

                print('TopoJSON file saved to disk from "%s".' % topoJSONurl)
            
            print('Loading TopoJSON data from "%s"...' % topoJSONfile)
            with open(topoJSONfile) as tjf:
                topojson = json.load(tjf)

            tj_df = pd.DataFrame(topojson['objects']['counties']['geometries'])
            countyids = set(tj_df['id'])
            print('Full set of county codes obtained from "%s".' % topoJSONfile)
            return countyids
        
        def fillTallyframe():
            '''
            USAGE:
            Fills tally dataframe with any missing counties which are encoded for by the TopoJSON 
            file but not listed by the US Census Bureau. Assigns tally value of [0, ... , 0], 
            population value of None, and the minimum color value (multiples by an np array of 
            ones) to each such county. 
            '''
            
            countyTopoCodes = getTopoCounties()
            countyCensusCodes = set(list(self.tallyframe['CountyCode']))
            blocks = len(self.tallyframe.Tally[0])
            
            if countyTopoCodes != countyCensusCodes:
                diff = countyTopoCodes.difference(countyCensusCodes)
                for code in list(diff):
                    idx = len(self.tallyframe)
                    # Remember: ['CountyCode', 'Tally', 'Population', 'Geoname', 'Value']
                    self.tallyframe.loc[idx] = [code, np.zeros(blocks), None, None, 
                                                self.mincolor * np.ones(blocks)]
                            
        ##### ------------------------------ Control Flow ------------------------------ ##### 
        
        print('Converting tally counts to color values...')
        processValues()
        getTopoJSONCounties()
        countycolorfile = self.countycolorroot.split('.')[0] + self.time_params + '.csv'
        self.tallyframe.to_csv(countycolorfile, index=False)
        print('County color data saved to "%s".' % countycolorfile)
    
    def df2GeoJSON(self):
        '''
        USAGE: 
        Generates a GeoJSON encoding of tweet events from tweet dataframe, and saves the resulting
        dictionary to a JSON file.
        '''
        
        if os.path.exists(self.tweetGeoJSONfile):
            print('No action. Tweet GeoJSON data already saved to "%s".' % self.tweetGeoJSONfile)
        
        else:
            geoJSON = {'type': 'FeatureCollection'}

            if set(['User', 'Text', 'Datetime', 'Place', 'listLATLON', 'State']) not in set(self.df.keys()):
                self.tweetfile2df()
                self.mkDatetime()
                self.listLATLON()

            featurelist = []

            print('Creating GeoJSON file from tweets...')
            df = self.df[self.df['State'] == False]
            df = df.reset_index(drop=True)
            
            # Note: GeoJSON encodes coordinates in [LON, LAT] like Twitter, not [LAT, LON]!
            for idx in tqdm(range(len(df))):
                item = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point", 
                        "coordinates": [df.loc[idx]['listLATLON'][1], df.loc[idx]['listLATLON'][0]]
                    },
                    "properties": {
                        "User": df.loc[idx]['User'],
                        "Text": df.loc[idx]['Text'],
                        "Datetime": str(df.loc[idx]['Datetime']),
                        "Place": df.loc[idx]['Place'][:-1]
                    }
                }

                featurelist.append(item)

            geoJSON['features'] = featurelist

            with open(self.tweetGeoJSONfile, 'w') as tgf:
                json.dump(geoJSON, tgf)

            print('Tweet GeoJSON data saved to "%s".' % self.tweetGeoJSONfile)
                        
    def analyze(self):
        '''
        USAGE:
        This method fully processes and analyzes the TweetDF object.
        '''
        
        self.tweetfile2df()    # generates tweet dataframe "self.df" from data in datafilepath
        self.mkDatetime()      # changes "CREATED AT" info into datetime-formatted info and places in "Datetime" column
        self.stateNoState()    # determines whether a tweet only has state-level location precision
        self.avgLONLAT()       # averages bbox coordinates and adds to self.df
        self.listLATLON()      # generates [LAT, LON] pairs and adds the pair lists to self.df 
        self.revGeocodePOST()  # submits POST requests to retrieve politics data on coordinates in self.df
        self.countyExtract()   # adds county codes and tally distributions to self.df
        
        self.timeTally(2, 60)  # tallies up time series of tweets/county; adds "CountyCode" and "Tally" to self.tallyframe
        self.getCountyPop()    # gets county population info from US Census Bureau and adds it to self.df
        self.tally2value()     # converts tally counts to color-mapping values assuming an initial log-norm distribution
        self.df2GeoJSON()      # generates GeoJSON file of tweet events from tweet dataframe
        
        print('Analysis complete.')
        
##### -------------------------------------------- MAIN -------------------------------------------- ##### 
        
datafilepath = "Twitter Data/eclipsefile1.json" 

tweets = TweetDF(datafilepath)  # initialize TweetDF object as "tweets"
tweets.analyze()