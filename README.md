# Eclipse Twitter Tracker:

Inspired by this [Google Trends map](wapo.st/2vkgIBv) of eclipse searches in the week leading up to the "Great American Eclipse" of 2017, I decided to see if I could track the path of the moon's shadow as it crossed the continental United States by using only Twitter mentions of the eclipse. 

### Intro - *August 18, 2017*:

I am working on writing a program to mine Twitter data from August 21, 2017 (about 9am PDT to 3pm EDT) for mentions of the solar eclipse to see if by using frequency of mentions alone, we can track the path of the moon's shadow throughout the day. Using this data, I hope to generate a changing map of the United States with counties shaded according to proportional tweet volume referencing the eclipse. I will also compare this path to the true path and see if there are any interesting conclusions to be made (Twitter-mentions lagging behind or anticipating the eclipse, Twitter-shadow-area compared to the actual region of totality, tweet content of partial eclipse experiencers vs total eclipse experiencers, etc.)

The rate-limiting of the Twitter REST API is too restricting for the type of large data-acquisition this project requires, so I will try to write up and test a program which will use Twitter's Streaming API to collect data live during the eclipse. Since I will have no internet access in Mitchell, OR (where I will be viewing the eclipse from), I will leave a computer running the program at home to automatically collect the relevent Tweets. I will not be able to monitor the progress of the program during collection, so I will program in failsafes to ensure that the total data collected as well as the size of each data file does not get too large. Hopefully, I can get it done before I leave for the airport early tomorrow morning.

### UPDATE - *September 4, 2017*:

Success! The data set ([eclipsefile1.json](https://github.com/chrismbryant/eclipse-twitter-tracker/blob/master/eclipsefile1.json)) is smaller than expected, but it looks like the program did what it was supposed to do! 

Now home from my extended eclipse-trip, I am beginning the process of figuring out how to process and map my data. I just posted the [EclipseTracker.ipynb](https://github.com/chrismbryant/eclipse-twitter-tracker/blob/master/EclipseTracker.ipynb) Jupyter Notebook which collected data from Twitter's streaming API while I was away. It appears that roughly 1M tweets in the 6-hour data acquisition period mentioned either the word "eclipse" or "sun," of which 20,933 were geo-tagged. A quick scatter plot of each of these geo-tagged points on an (X,Y) = (Longitude, Latitude) chart reaveals an image which strikingly appears to match the population density of the United States, but with an added faint trail of points crossing the country in the path of totality.

Moving forward, I will work to bin these points by county (probably using TopoJSON to create the county map) and normalize each measurement by dividing the tweet-count by the county population. Hopefully, this process will accent the path of the eclipse amidst the Twitter noise. 

Some other things took into:
 * using the [Albers projection](https://en.wikipedia.org/wiki/Albers_projection) to accurately preserve county area;
 * obtaining and plotting the [NASA eclipse path data](https://eclipse.gsfc.nasa.gov/SEpath/SEpath2001/SE2017Aug21Tpath.html); 
 * creating a time-series of images to display shadow movement.  
