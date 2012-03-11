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
from twitter import TwitterError
from bitly import BitlyError

import logging
import time
import threading
import urllib2
import os.path
import sys
from warnings import catch_warnings
reload(sys)
sys.setdefaultencoding( "latin-1" )




def getURLTitle(url):
    print '        searching title: %s' % url
    br = Browser()
    br.open(url,timeout=10)
    title = br.title()
    br.close()
    print '        title -> %s ' % (title)
     
    return title

def textPassFilters(text,filters):
    passFilter = True
    if (len(filters)>0):
        for filterword in filters:
            if (text.find(filterword)>-1):
                passFilter = False
    
    return passFilter
    
def getCategoryItems(categories,name):
    for category in categories:
        label = category.label
        if (label == name):
            category.loadItems(True)
            category.loadMoreItems(True) 
            return category.items
    
    return []



def internet_on():
    try:
        response=urllib2.urlopen('http://twitter.com',timeout=2)
        return True
    except urllib2.URLError as err: 
        pass
    return False

class BotThread(threading.Thread):
    def __init__(self,bot):
        threading.Thread.__init__(self)
        self.bot = bot
    def run(self):
        tph = bot.GetTweetsPerHour()
        tweetlimit = tph if tph > -1 else DEFAULT_MAX_TWEETS 
        
               
        while True:
            nextUpdateSeconds = 0 
            timeRemain = PERIOD_SECONDS
            count = 0
            try:
                logging.info('[%s] -> Trying to post %i Twitter updates', self.bot.botfolder,self.bot.GetTweetsPerHour())
                
                while (count < tweetlimit):
                    nextUpdateSeconds = random.randint(0, timeRemain)
                    timeRemain -= nextUpdateSeconds
                    logging.info("[%s] -> Next update in %d seconds",self.bot.botfolder,nextUpdateSeconds)
                    time.sleep(nextUpdateSeconds)
                    if self.bot.update():
                        count += 1
                
            except Exception as (e):
                logging.error("[%s] -> Error updating bot",self.bot.botfolder)
                print e
            logging.info('[%s] -> Posted %i Twitter updates. Would start again in %d seconds ', self.bot.botfolder,count,timeRemain)
            time.sleep(timeRemain)
            
class Bot(object):
    def __init__(self,config):
        self.botfolder = config.folder
        self.botTK = config.accessTokenKey
        self.botTS = config.accessTokenSecret
        self.tph = config.maxtweets
        
        self.hashtags = {}
        if 'hashtags' in config.keys():
            self.hashtags = config.hashtags
        
        
        self.config = config
    def GetTweetsPerHour(self):
        return self.tph
    
    def tuitAndMark(self,tweet,item):
        #Si el tweet es de menos de 140 caracteres publicamos
        if len(tweet) <= 140:
            try:
                logging.info("[%s] ->     Tweeting....",self.botfolder)
                self.twitterClient.PostUpdate(tweet)
            except TwitterError as (e):
                logging.error("[%s] ->     Error Posting update (%s): %s" ,self.botfolder,tweet,e.message)
                raise e
        
        #Marcamos el item de Google Reaer como leido    
        try:
            item.markRead()
        except Exception as (e):
            logging.error("[%s] ->     Error marking as read",self.botfolder)
            raise e
    def generateTweet(self,title,url,hashtags={}):
    
       
        shortlink = url
        try:
            shortlink = apiBitly.shorten(url)
        except BitlyError as (e):
            logging.warning("[%s] ->     Error shortening link (%s)",self.botfolder,url)
            
    
        tweet = "%s %s" % (title,shortlink)
        
        try:
            if len(tweet) < 140:
                if title.find('...') > -1:
                    longTitle = '' #getURLTitle(url)
                    if longTitle != '':
                        longTweet = "%s %s" % (longTitle,shortlink)
                        if len(longTweet) < 140:
                            tweet = longTweet
        except Exception as (e):
            logging.warning("[%s] ->         Error while getting title: %s",self.botfolder,e.message)
            raise
        
        hashtagedtweet = tweet
        for key, value in hashtags.iteritems():
            hashtagedtweet = hashtagedtweet.replace(key,value)
            if hashtagedtweet != tweet:
                break
            
        if len(hashtagedtweet) > 140:
            hashtagedtweet = tweet
            
        return hashtagedtweet

    def update(self):
        
        categories = reader.getCategories()
        news = getCategoryItems(categories,self.botfolder)
        success = False
        
        if (len(news)>0):
            self.twitterClient = twitter.Api(consumer_key=twitterConsumerKey,
                                             consumer_secret=twitterConsumerSecret,
                                             access_token_key=self.botTK, 
                                             access_token_secret=self.botTS)
            
            if not DEBUG_MODE:
                random.shuffle(news)
            
            item = news[0]
            
            #Titulo
            title = item.title
            
            passFilter = textPassFilters(title,self.config.filters)
            
            if passFilter:
                        
                #Parseamos el original id que lleva el link original
                gnlink = item.url
                posURL = gnlink.find("url=")
                link = gnlink[posURL+len("url="):len(gnlink)] 
                
                tweet = ''
                try:
                    logging.info("[%s] ->     Generating Tweet....",self.botfolder)
                    
                    #Creamos el tweet
                    tweet = self.generateTweet(title, link, self.hashtags)
                    
                    if not DEBUG_MODE:
                        self.tuitAndMark(tweet, item)

                    logging.info("[%s] ->     Tweeted!!!: %s (%i)",self.botfolder, tweet, len(tweet))
                    success = True
                except Exception as (e):
                    
                    logging.error("[%s] ->     ### Error while tweeting ###\n" +
                                  "    ### Tweet: %s\n" + 
                                  "    ### URL: %s ###\n" +
                                  "    ### %s ###",self.botfolder,tweet, link,e.message)
                    try:
                        item.markRead()
                    except Exception as (e):
                        logging.error("[%s] ->     Error marking as read", self.botfolder)
                   
                
            else:
                logging.info("[%s] ->     !!! Tweet Rejected: %s",self.botfolder,title)
                if not DEBUG_MODE:
                    item.markRead()
        else:
            success = True
        
        return success

###########################################################
argv = sys.argv
if (len(argv)<2):
    print "Usage: %s %s" % (argv[0], "configFile.cfg")
    exit()

f = file(argv[1])
cfg = Config(f)

DEBUG_MODE = os.path.isfile('debug')
if DEBUG_MODE:
    logging.basicConfig(format='[%(asctime)s] %(levelname)s - %(message)s',level=logging.DEBUG)
    logging.info("################    DEBUG MODE    ##############")
else:
    logging.basicConfig(format='[%(asctime)s] %(levelname)s - %(message)s',level=logging.INFO)

if (not internet_on()):
    logging.critical("Couldn't connect to internet") 
    exit()
else:
    logging.info("Connected to Internet")

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
if reader.buildSubscriptionList():
    logging.info("Google Reader request ok")
else:
    logging.critical("Error retrieving subscriptions from Google Reader")
    exit()

DEFAULT_MAX_TWEETS = 2
PERIOD_SECONDS = 3600

if DEBUG_MODE:
    PERIOD_SECONDS = 80

for botConfig in cfg.bots:
    
    if (botConfig.active):
        bot = Bot(botConfig)
        botThread = BotThread(bot)
        botThread.start()
