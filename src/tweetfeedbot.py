'''
Created on 21/10/2011

@author: gdelfresno
'''
from libgreader import GoogleReader, OAuthMethod, ClientAuthMethod, Feed, ItemsContainer, Item, BaseFeed, SpecialFeed, ReaderUrl
import bitly
import twitter
from config import Config
import random


import sys
reload(sys)
sys.setdefaultencoding( "latin-1" )

def textPassFilters(text,filters):
    passFilter = True
    if (len(filters)>0):
        for filterword in filters:
            if (title.find(filterword)>-1):
                passFilter = False
    
    return passFilter
    
def getCategoryItems(categories,name):
    for category in categories:
        label = category.label
        if (label == name):
            category.loadItems(True)
            return category.items
    
    return []

def postNewsWithUrl(title,url,item):
    
    #Ahora obtenemos el link acortado.
    try:
        shortlink = apiBitly.shorten(url)
    except BitlyError as e:
        print 'Error shortening link (%s): %s' % (url, e.message)
        raise e
    
    #Creamos el tweet
    tweet = "%s %s" % (title,shortlink)
    tweetLen = len(tweet)
                
                
    #Si el tweet es de menos de 140 caracteres publicamos
    if (tweetLen <= 140):
        try:
            twitterClient.PostUpdate(tweet)
        except TwitterError as e:
            print 'Error Posting update (%s): %s' % (tweet,e.message)
            raise e
            
            
    
    #Marcamos el item de Google Reaer como leido    
    item.markRead()
        
    return shortlink
    
#def getLongTitle(link):
#    br = Browser()
#    br.open(link)
#    return br.title()


argv = sys.argv
if (len(argv)<2):
    print "Usage: %s %s" % (argv[0], "configFile.cfg")
    exit()

f = file(argv[1])
cfg = Config(f)

readerUser = cfg.readerUser
readerPassword = cfg.readerPassword

bitlyapikey = cfg.bitlyapikey
bitlyuser = cfg.bitlyuser

twitterConsumerKey = cfg.twitterConsumerKey
twitterConsumerSecret = cfg.twitterConsumerSecret

apiBitly = bitly.Api(login=bitlyuser, apikey=bitlyapikey)

#Iniciamos la conexion a Google Reader
ca = ClientAuthMethod(readerUser,readerPassword)
reader = GoogleReader(ca)

#Obtenemos los no leidos
reader.buildSubscriptionList()
feeds = reader.getSubscriptionList()
categories = reader.getCategories()

DEFAULT_MAX_TWEETS = 2

for bot in cfg.bots:
    
    if (bot.active):
        botfolder = bot.folder
        botTK = bot.accessTokenKey
        botTS = bot.accessTokenSecret
        
        news = getCategoryItems(categories,botfolder)
        print 'Bot %s info -> Total News: %i  Access Token:%s Access Token Secret: %s' % (botfolder,len(news),'botTK','botTS')
        
         
        if (len(news)>0):
            twitterClient = twitter.Api(consumer_key=twitterConsumerKey,consumer_secret=twitterConsumerSecret,access_token_key=botTK, access_token_secret=botTS)
            
            tweetlimit = bot.maxtweets if bot.maxtweets > -1 else DEFAULT_MAX_TWEETS 
            count = 0
            random.shuffle(news)
            for item in news:
                #Titulo
                title = item.title
                
                passFilter = textPassFilters(title,bot.filters)
                
                if passFilter:
                            
                    #Parseamos el original id que lleva el link original
                    gnlink = item.url
                    posURL = gnlink.find("url=")
                    link = gnlink[posURL+len("url="):len(gnlink)] 
    
                    shortlink = link
                    
#                    longTitle = getLongTitle(link)
#                    print "Long Title %s" % longTitle
                    
                    try:
                        print "    Tweeting...."
                        shortlink = postNewsWithUrl(title,link,item)
                        
                        #Creamos el tweet
                        tweet = "%s %s" % (title,shortlink)
                        tweetlen = len(tweet)
                        print "    Tweet: %s (%i)" % (tweet, tweetlen)
                        count=count+1 
                    except:
                        print "    ### Error while tweeting ###"
                       
                    
                else:
                    print "    !!! Tweet Rejected: %s" % (title)
                    item.markRead()
                
                if (count == tweetlimit):
                    break
    
