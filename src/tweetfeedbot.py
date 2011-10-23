'''
Created on 21/10/2011

@author: gdelfresno
'''
from libgreader import GoogleReader, OAuthMethod, ClientAuthMethod, Feed, ItemsContainer, Item, BaseFeed, SpecialFeed, ReaderUrl
import bitly
import twitter

READER_FOLDER = "Demonstration"

readerUser = 'user@gmail.com'
readerPassword = 'password'

bitlyapikey ="YOUR_API_KEY"
bitlyuser = "YOUR_BITLY_USER"

twitterConsumerKey = ''
twitterConsumerSecret = ''
accessTokenKey = ''
accessTokenSecret = ''

apiTwitter = twitter.Api(consumer_key=twitterConsumerKey,consumer_secret=twitterConsumerSecret,access_token_key=accessTokenKey, access_token_secret=accessTokenSecret)
apiBitly = bitly.Api(login=bitlyuser, apikey=bitlyapikey)

#Iniciamos la conexion a Google Reader
ca = ClientAuthMethod(readerUser,readerPassword)
reader = GoogleReader(ca)

#Obtenemos los no leidos
reader.buildSubscriptionList()
feeds = reader.getSubscriptionList()
categories = reader.getCategories()


#Recorremos cada uno de los elementos
for category in categories:
    label = category.label
    if (label == READER_FOLDER):
        category.loadItems(True)
        news = category.items
        
        #Recorremos cada uno de los elementos
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
                apiTwitter.PostUpdate(tweet)
                
            #Marcamos el item de Google Reaer como leido    
            item.markRead()
    
    
    
