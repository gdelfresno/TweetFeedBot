'''
Created on 21/10/2011

@author: gdelfresno
'''
from libgreader import GoogleReader, OAuthMethod, ClientAuthMethod, Feed, ItemsContainer, Item, BaseFeed, SpecialFeed, ReaderUrl
import bitly
import twitter
from config import Config

import sys
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
    shortlink = apiBitly.shorten(url)
    
    #Creamos el tweet
    tweet = "%s %s" % (title,shortlink)
    tweetLen = len(tweet)
                
                
    #Si el tweet es de menos de 140 caracteres publicamos
    if (tweetLen <= 140):
        twitterClient.PostUpdate(tweet)
    
    #Marcamos el item de Google Reaer como leido    
    item.markRead()
        
    return shortlink
    
    
argv = sys.argv
if (len(argv)<2):
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

MAX_TWEETS = 2

for bot in cfg.bots:
    
    if (bot.active):
        botfolder = bot.folder
        botTK = bot.accessTokenKey
        botTS = bot.accessTokenSecret
        
        news = getCategoryItems(categories,botfolder)
        print "Bot %s info -> Total News: %i  Access Token:%s Access Token Secret:%s" % (botfolder,len(news),'botTK','botTS')
        
         
        if (len(news)>0):
            twitterClient = twitter.Api(consumer_key=twitterConsumerKey,consumer_secret=twitterConsumerSecret,access_token_key=botTK, access_token_secret=botTS)
            
            count = 0
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
                    
                    try:
                        print '    Tweeting....'
                        shortlink = postNewsWithUrl(title,link,item)
                        
                        #Creamos el tweet
                        tweet = "%s %s" % (title,shortlink)
                        tweetlen = len(tweet)
                        print "    Tweet: %s (%i)" % (tweet, tweetlen)
                        count=count+1 
                    except:
                        print '    ### Error while tweeting ###'
                       
                    
                else:
                    print '    !!! Tweet Rejected: %s' % title
                    item.markRead()
                
                if (count == MAX_TWEETS):
                    break
    
