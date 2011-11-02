'''
Created on 21/10/2011

@author: gdelfresno
'''
from libgreader import GoogleReader, ClientAuthMethod
import bitly
import twitter
from config import Config
from mechanize import Browser
import random

import os.path
import sys
reload(sys)
sys.setdefaultencoding( "latin-1" )

def generateTweet(title,url,hashtags=[]):
    
       
    shortlink = url
    try:
        shortlink = apiBitly.shorten(url)
    except BitlyError as e:
        print 'Error shortening link (%s): %s' % (url, e.message)
        

    tweet = "%s %s" % (title,shortlink)
    
    if len(tweet) < 140:
        if title.find('...') > -1:
            longTitle = getURLTitle(url)
            if longTitle != '':
                longTweet = "%s %s" % (longTitle,shortlink)
                if len(longTweet) < 140:
                    tweet = longTweet
    
    return tweet

def getURLTitle(url):
    br = Browser()
    br.open(url,timeout=10)
    title = br.title()
    print '    %s title -> %s ' % (url,title)
    return title

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

def tuitAndMark(tweet,item):
    #Si el tweet es de menos de 140 caracteres publicamos
    if len(tweet) <= 140:
        try:
            twitterClient.PostUpdate(tweet)
        except TwitterError as e:
            print 'Error Posting update (%s): %s' % (tweet,e.message)
            raise e
    
    #Marcamos el item de Google Reaer como leido    
    item.markRead()

argv = sys.argv
if (len(argv)<2):
    print "Usage: %s %s" % (argv[0], "configFile.cfg")
    exit()

f = file(argv[1])
cfg = Config(f)

DEBUG_MODE = os.path.isfile('debug')
if DEBUG_MODE:
    print "################    DEBUG MODE    ##############"
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
                    
                    
                    try:
                        print "    Tweeting...."
                        
                        #Creamos el tweet
                        tweet = generateTweet(title, link)
                        
                        if not DEBUG_MODE:
                            tuitAndMark(tweet, item)

                        print "    Tweet: %s (%i)" % (tweet, len(tweet))
                        count=count+1 
                    except Exception as e:
                        print "    ### Error while tweeting ###"
                        print e.message
                       
                    
                else:
                    print "    !!! Tweet Rejected: %s" % (title)
                    if not DEBUG_MODE:
                        item.markRead()
                
                if (count == tweetlimit):
                    break
    
