'''
Created on 21/10/2011

@author: gdelfresno
'''
from libgreader import GoogleReader, OAuthMethod, ClientAuthMethod, Feed, ItemsContainer, Item, BaseFeed, SpecialFeed, ReaderUrl
import bitly
import twitter
from config import Config

import sys

def getCategoryItems(categories,name):
    for category in categories:
        label = category.label
        if (label == name):
            category.loadItems(True)
            return category.items
    
    return []

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

for bot in cfg.bots:
    
    if (bot.active):
        botfolder = bot.folder
        botTK = bot.accessTokenKey
        botTS = bot.accessTokenSecret
        print "Bot %s info -> Access Token:%s Access Token Secret:%s" % (botfolder,botTK,botTS)
        
        news = getCategoryItems(categories,botfolder)
        
        if (len(news)>0):
            twitterClient = twitter.Api(consumer_key=twitterConsumerKey,consumer_secret=twitterConsumerSecret,access_token_key=botTK, access_token_secret=botTS)
    
            for item in news:
                #Titulo
                title = item.title
                
                #Parseamos el original id que lleva el link original
                gnlink = item.url
                posURL = gnlink.find("url=")
                link = gnlink[posURL+len("url="):len(gnlink)] 
            
                #Ahora obtenemos el link acortado.
                shortLink = apiBitly.shorten(link)
                
                #Creamos el tweet
                tweet = "%s %s" % (title,shortLink)
                tweetLen = len(tweet)
                print "    Tweet: %s (%i)" % (tweet, tweetLen)
    
                #Si el tweet es de menos de 140 caracteres publicamos
                if (tweetLen <= 140):
                    twitterClient.PostUpdate(tweet)
                    
                #Marcamos el item de Google Reaer como leido    
                item.markRead()
        
    
