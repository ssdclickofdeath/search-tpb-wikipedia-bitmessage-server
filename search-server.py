#!/usr/bin/env python

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import xmlrpclib
import json
import time
import sys
import urllib2
import re
import wikipedia
from tpb import TPB
from tpb import CATEGORIES, ORDERS

# Enter an address that you have already created
mySendingAddress = "XXXXXXXXXXXXXXXXXXXXXXXXXXXX"

# Prepend a string to the message that is about to be sent
signature = "If you like this service, please help to expand it. BTC: 1CNwa4y27U7xbUGkEdrrq2fNDwo9dktCKU  LTC: LZeeS5AKctbuAkxN9i8snVhHgSfDjQy9AS"

try:
    api = xmlrpclib.ServerProxy("http://USERNAME-FOR-API:PASSWORD-FOR-API@127.0.0.1:8442/")
except:
    print "Error connecting to Bitmessage"
    sys.exit()

#TPB method takes theRequestType (search or top), and theTerms (the search terms)
def piratebay(theRequestType, theTerms):
    try:
        t = TPB('https://thepiratebay.org')
        if theRequestType.lower() == "search":
            allResults = ""
            print "Searching TPB for: "+theTerms
            for torrent in t.search(theTerms).page(1):
                result = """
		-----------------------------------------------------------------
		Title:\t %(fTitle)s
		Seeders:\t %(fSeeders)s / %(fLeechers)s
		Category:\t %(fCat)s / %(fSubcat)s
		Uploader:\t %(fUploader)s
		Size:\t %(fSize)s
		Uploaded:\t %(fUploaded)s
		%(fMagnet)s
		-----------------------------------------------------------------

                """ % {'fTitle': torrent.title, 'fSeeders': torrent.seeders, 'fLeechers': torrent.leechers, 'fCat':torrent.category, 'fSubcat':torrent.sub_category, 'fUploader':torrent.user, 'fSize':torrent.size, 'fUploaded':torrent.created, 'fMagnet': torrent.magnet_link}

                allResults+=result
            if len(allResults) == 0:
                allResults = "Nothing found for search term: "+theTerms

        elif theRequestType.lower() == "top":
            allResults = ""
            whichTop = t.top().category(CATEGORIES.VIDEO.ALL) #set a default category incase nothing matches below

            if theTerms.lower() == "videos" or theTerms.lower() == "video": whichTop = t.top().category(CATEGORIES.VIDEO.ALL)
            if theTerms.lower() == "tv" or theTerms.lower() == "tvshows" or theTerms.lower() == "tv shows": whichTop = t.top().category(CATEGORIES.VIDEO.TV_SHOWS)
            if theTerms.lower() == "movies" or theTerms.lower() == "films": whichTop = t.top().category(CATEGORIES.VIDEO.MOVIES)
            if theTerms.lower() == "music": whichTop = t.top().category(CATEGORIES.AUDIO.MUSIC)
            if theTerms.lower() == "audiobooks" or theTerms.lower() == "audio books": whichTop = t.top().category(CATEGORIES.AUDIO.AUDIO_BOOKS)
            if theTerms.lower() == "games": whichTop = t.top().category(CATEGORIES.GAMES.ALL)
            if theTerms.lower() == "ebooks" or theTerms.lower() == "e-books" or theTerms.lower() == "e-book" or theTerms.lower() == "books": whichTop = t.top().category(CATEGORIES.OTHER.EBOOKS)
            print "TOP TPB for: "+theTerms
            for torrent in whichTop:
                result = """
		-----------------------------------------------------------------
		Title:\t %(fTitle)s
		Seeders:\t %(fSeeders)s / %(fLeechers)s
		Category:\t %(fCat)s / %(fSubcat)s
		Uploader:\t %(fUploader)s
		Size:\t %(fSize)s
		Uploaded:\t %(fUploaded)s
		%(fMagnet)s
		-----------------------------------------------------------------
                """ % {'fTitle': torrent.title, 'fSeeders': torrent.seeders, 'fLeechers': torrent.leechers, 'fCat':torrent.category, 'fSubcat':torrent.sub_category, 'fUploader':torrent.user, 'fSize':torrent.size, 'fUploaded':torrent.created, 'fMagnet': torrent.magnet_link}
                allResults+=result

        return allResults
    except Exception as e:
        print "Error from piratebay function"
        print e

# Wikipedia method used for parsing wikipedia
def wiki(theRequestType, theTerms):
    if theRequestType.lower() == "search":
        print "Searching wiki for: "+theTerms
        results = wikipedia.search(theTerms)
        allResults = ""
        for result in results:
            allResults+=result+"\n"
        if len(allResults) == 0:
            allResults = "Nothing found for search term: "+theTerms
        return allResults
    elif theRequestType.lower() == "get":
        print "Getting wiki article for: "+theTerms
        page = wikipedia.page(theTerms)
        page = page.content
        return page


def sendMessage(sendSubject, result, sendersAddress):
    try:
        print "Sending to: "+sendersAddress+" subject: "+sendSubject
        sendSubject = sendSubject.encode('base64')
        sendSubject = sendSubject.encode('utf8')
        result = signature+"\n\n"+result
        result = result.encode('utf8')
        result = result.encode('base64')
        print api.sendMessage(sendersAddress, mySendingAddress, sendSubject, result)
    except Exception as e:
        print "Error trying to send message"
        print e

# loop through all the messages we have. If they are valid terms (tpb, wiki, search, get, top)
# send them off to the correct method. Finally delete the message.
try:
    inboxMessages = json.loads(api.getAllInboxMessages())
    count = 0
    for message in inboxMessages['inboxMessages']:
        count+=1
        msgid = str(message['msgid'])
        sendersAddress = str(message['fromAddress'])
        subject = str(message['subject'].decode('base64'))
        body = str(message['message'].decode('base64'))
        body = body.encode('utf8')
        splitBody = body.split(' ')
        requestType = splitBody[0]
        terms = splitBody[1:]
        terms = " ".join(terms)

        print api.trashMessage(msgid)+"\n"

        if len(body) > 1 and subject.lower() == "tpb" and requestType.lower() == "search":
            result = piratebay(requestType, terms)
            sendSubject = "TPB results for: "+terms
            sendMessage(sendSubject, result, sendersAddress)
        elif len(body) > 1 and subject.lower() == "tpb" and requestType.lower() == "top":
            result = piratebay(requestType, terms)
            sendSubject = "TPB top 30 "+terms+" torrents"
            sendMessage(sendSubject, result, sendersAddress)
        elif len(body) > 1 and subject.lower() == "wiki" and requestType.lower() == "search":
            result = wiki(requestType, terms)
            sendSubject = "Wikipedia search results for: "+terms
            sendMessage(sendSubject, result, sendersAddress)
        elif len(body) > 1 and subject.lower() == "wiki" and requestType.lower() == "get":
            result = wiki(requestType, terms)
            sendSubject = "Wikipedia article for: "+terms
            sendMessage(sendSubject, result, sendersAddress)
        else:
            pass

    if count == 0:
        print "No new messages"
except Exception as e:
    print e
    print "Deleting invalid message"
    print api.trashMessage(msgid)+"\n"
