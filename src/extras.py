'''
Created on 17/11/2012

@author: gdelfresno
'''
from mechanize import Browser

def getURLTitle(url):
    print '        searching title: %s' % url
    br = Browser()
    br.open(url,timeout=5)
    title = br.title()
    br.close()
    print '        title -> %s ' % (title)
     
    return title