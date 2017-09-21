import numpy as np
import matplotlib.pyplot as plt
import json

def getPopData():
    '''
    USAGE: Get population data and put it in a dataframe.
    RETURN: cd_df - census dataframe with 'POP', 'GEONAME', and 'CountyCode' columns 
    '''
    censusdatafile = 'Resources/censusdata.json'
    with open(censusdatafile, 'r') as cdf:
        censusdata = json.load(cdf)

    cd_df = pd.DataFrame(censusdata[1:])
    cd_df.columns = censusdata[0]
    cd_df.loc[:,'CountyCode'] = cd_df['state'] + cd_df['county']
    cd_df = cd_df.drop(['DATE', 'state', 'county'], axis = 1)
    print('Census data loaded from "%s"...' % censusdatafile)

    return cd_df

def histPop(histlist, scale, bins, name=None):
    '''
    USAGE: Plot and export population histogram.
    '''
    plt.xlabel('Population', size = 14)
    plt.ylabel('# of Counties', size = 14)
    plt.title('Population: Lognormal Distribution', size = 20)
    plt.xlim(scale)
    
    n, bins, patches = plt.hist(histlist, color='lightgray', bins=bins)
    
    if name:
        plt.savefig(name, dpi=200)
        
    plt.show()
    
def getStats(histlist):
    '''
    USAGE: Calculate mean and standard deviation of list.
    RETURNS: [mu, sigma] - mean and standard deviation of histlist
    '''
    mu = np.mean(histlist)
    sigma = np.std(histlist)
    return [mu, sigma]
    
def plotStatLines(histlist):
    '''
    USAGE: Plot mean and 2 standard deviation lines on histogram
    RETURNS: [mu, sigma] - mean and standard deviation of histlist
    '''
    [mu, sigma] = getStats(histlist)
    
    plt.axvline(mu, color = 'darkred')
    plt.axvline(mu + sigma, color = 'darkblue', ls = '--')
    plt.axvline(mu - sigma, color = 'darkblue', ls = '--')
    plt.axvline(mu + 2*sigma, color = 'darkgreen', ls = '--')
    plt.axvline(mu - 2*sigma, color = 'darkgreen', ls = '--')
    
    return [mu, sigma]

def plotMuSig(mu, sigma):
    '''
    USAGE: Plot mu and sigma labels.
    '''
    plt.text(mu + 0.1, 100, r'$\mu$ = %s' % str(np.round(mu,1)), size = 13)
    plt.text(mu + sigma + 0.2, 80, r'$\sigma$ = %s' % str(np.round(sigma,1)), size = 13)

def normPopLabels():
    '''
    USAGE: Plot x, y, and title labels for log(pop) plot.
    '''
    plt.xlabel('log(Population)', size = 14)
    plt.ylabel('# of Counties', size = 14)
    plt.title('log(Pop): Normal Distribution', size = 20)

def featScaledLabels():
    '''
    USAGE: Plot x, y, and title labels for feature-scaled and mean-normalized log(pop) plot.
    '''
    plt.xlabel('Standard Deviations from Mean', size = 14)
    plt.ylabel('# of Counties', size = 14)
    plt.title('log(Pop): Scaled, Mean-Normalized', size = 20)
    
def histNorm(histlist, scale, bins, featscaled=None, name=None):
    '''
    USAGE: 
    Generate a labeled histogram of normally distributed data.
    
    ARGUMENTS: 
    histlist - list or array of data
    scale - specify bounds of x-axis [min, max]
    bins - number of histogram bins
    '''
    
    [mu, sigma] = plotStatLines(histlist)
        
    plotMuSig(mu, sigma)
    plt.rcParams["font.family"] = "Open Sans"
    plt.xlim(scale)
    if not featscaled:
        normPopLabels()
    else:
        featScaledLabels()
    
    n, bins, patches = plt.hist(histlist, color='lightgray', bins=bins)
    
    if name:
        plt.savefig(name, dpi=200)
    
    plt.show()


cd_df = getPopData()
poparray = np.array(list(pd.to_numeric(cd_df['POP'])))
logpop = np.log(poparray)
    
histPop(poparray, scale = [0, 250000], bins = 2000, name = 'Images/HistogramPopulation.png')
histNorm(logpop, scale = [6,15], bins = 80, name = 'Images/HistogramLogPop.png')

[mu, sigma] = getStats(logpop)
scaled = (logpop - mu) / sigma
histNorm(scaled, featscaled='y', scale = [-3,3], bins = 80, name = 'Images/HistogramScaled')