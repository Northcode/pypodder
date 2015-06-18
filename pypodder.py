#!/usr/bin/python3
import importlib

needsinstall = False

def checkmodule(mod):
    loader = importlib.find_loader(mod)
    if loader is None:
        print("Please install python module %s" % mod)
        needsinstall = True

checkmodule('xml')
checkmodule('mutagen')
checkmodule('argparse')

if needsinstall:
    print("exiting")
    exit()

import xml.etree.cElementTree as xml
import os, argparse, sys, string, configparser,signal
from mutagen.easyid3 import EasyID3
from urllib.request import urlretrieve as wget
import urllib

def catchsigint(signum, frame):
    print("Terminated!")
    exit()

signal.signal(signal.SIGINT, catchsigint)

configfile = "pypodder.cfg"

feedlistfile = "feed.list"
feedlist = []
feedlistformat = ['url','name']

taglist = {'artist':'%owner%','album':'%podcast%','track':'%title%'}

argparser = argparse.ArgumentParser(description="Python podcast manager")
argparser.add_argument('--verbose','-v', dest='verbose', help='Be verbose', action='store_true')
argparser.add_argument('--progressbarstyle','-ps', dest="progstyle", help="progress bar style (percent,bar,line,percentbar)", type=str)
argparser.add_argument('--taggingonly','-oid3', help="Only do tagging", action='store_true')
args = argparser.parse_args()
verbose = False
progstyle = "percent" # "percent", "bar", "line", "percentbar"
onlytag = False
if args.verbose:
    verbose = True
if args.progstyle:
    progstyle = args.progstyle
if args.taggingonly:
    onlytag = True    

valid_nt_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
valid_tux_chars = "-:[]_.() %s%s" % (string.ascii_letters, string.digits)
    
def sanitizefilename(filename):
    if os.name == "nt":
        return ''.join([c for c in filename if c in valid_nt_chars])
    else:
        return ''.join([c for c in filename if c in valid_tux_chars])
    
def podcastfile(podcast,item):
    if podcast.outformat:
        outstr = podcast.outformat
        outstr = outstr.replace("{{podcastname}}", podcast.title)
        outstr = outstr.replace("{{episodename}}", item["title"])
        outstr = outstr.replace("{{episodenum}}", str(item["num"]))
        outstr = outstr.replace("{{episodesize}}", item["size"])
        outstr = outstr.replace("{{episodedate}}", item["date"])
        return outstr
    else:
        return os.path.join(podcast.title,sanitizefilename(item["title"] + ".mp3"))

def feedfile(feed):
    return sanitizefilename(feed["name"] + ".rss")

def downloadprogress(blocknum,blocksize,totalsize):
    percent = blocknum * blocksize * 1e2 / totalsize
    barpercent = int(percent / 5)
    if verbose:
        if progstyle == "percent":
            sys.stdout.write("\rdownloading: %d%%" % percent)
        elif progstyle == "bar":
            sys.stdout.write("\r[%s]" % "{0:20s}".format("#" * barpercent))
        elif progstyle == "line":
            sys.stdout.write("\r%s" % "{0:20s}".format("-" * barpercent))
        elif progstyle == "percentbar":
            sys.stdout.write("\r[%s] %d%% of total %d" % ("{0:20s}".format("#" * barpercent), percent,totalsize))
        sys.stdout.flush()

class podcast:
    def __init__(self,xmlreader):
        self.items = []
        treeroot = xmlreader.getroot()
        for channel in treeroot:
            for item in channel:
                if item.tag == "title":
                    self.title = item.text
                elif item.tag == "link":
                    self.link = item.text
                elif item.tag == "itunes:owner":
                    self.owner = item.getchildren()[0].text # itunes owner name
                elif item.tag == "description":
                    self.description = item.text
                elif item.tag == "item":
                    newitem = {}
                    for tag in item:
                        if tag.tag == "title":
                            newitem["title"] = tag.text
                        elif tag.tag == "pubDate":
                            newitem["date"] = tag.text
                        elif tag.tag == "link":
                            newitem["link"] = tag.text
                        elif tag.tag == "enclosure":
                            newitem["download"] = tag.get("url")
                            newitem["size"] = tag.get("length")
                    self.items.append(newitem)
        for item in self.items:
            item["num"] = len(self.items) - self.items.index(item)
        del(xmlreader)
        self.customformat = False

    def id3tag(self,item):
        if verbose:
            print("id3taging %s" % item["title"])
        tags = EasyID3(podcastfile(self,item))
        tags['title'] = item["title"]
        tags['album'] = self.title
        tags['artist'] = "Podcast"
        tags.save()
        
    def downloaditem(self,item):
        if verbose:
            print("downloading %s" % item["title"])
        download = wget(item["download"],podcastfile(self,item),downloadprogress)
        print("")

    def configfile(self):
        return os.path.join(self.title,"podcast.cfg")

    def readconfig(self):
        if not os.path.isfile(self.configfile()):
            if verbose:
                print("no config file for %s" % self.title)
                return
        with open(self.configfile()) as f:
            for line in f:
                if not line.startswith('#'):
                    config = configparser.ConfigParser()
                    config.read(self.configfile())
                    self.outformat = config['podcast'].get('outputformat',False)

# create feed.list if it doesnt exist
if not os.path.isfile(feedlistfile):
    with open(feedlistfile, 'w') as f:
        f.write("# Store your podcasts in here with this format: <url> <podcast name>\n# The first space separates the url from the name, all other spaces are ignored and put in the name")
        
#load feedlist
if verbose:
    print("Reading feedlist:")
with open(feedlistfile) as f:
    for line in f:
        if not line.startswith('#'):
            readfeed = [s.strip() for s in line.split()]
            readfeed = [readfeed[0], " ".join(readfeed[1:])]
            feedlist.append(dict(zip(feedlistformat,readfeed)))

podcasts = []

#load all podcasts in feedlist
for feed in feedlist:
    if verbose:
        print(feed["name"])
    if not os.path.isfile(feedfile(feed)): # download feed if it doesn't exist
        if verbose:
            print("downloading feed for {}".format(feed["name"]))
        wget(feed["url"],feedfile(feed),downloadprogress)
    podcasts.append(podcast(xml.ElementTree(file=feedfile(feed))))

# list podcasts
for podcast in podcasts:
    # check if podcast directory exists
    if not os.path.isdir(podcast.title):
        if verbose:
            print("creating directory for {}".format(podcast.title))
        os.makedirs(podcast.title)
    if not os.path.isfile(podcast.configfile()): # create config files if they don't exist
        config = configparser.ConfigParser()
        config['podcast'] = { 'outputformat' : '', 'useformat' : False }
        with open(podcast.configfile(),'w') as f:
            f.write("# config file for podcast %s\n" % podcast.title)
            config.write(f)
    podcast.readconfig()    

# download new episodes
if not onlytag:
    for podcast in podcasts:
        if verbose:
            print("downloading items for {}".format(podcast.title))
        for item in podcast.items:
            if not item["size"]:
                with urllib.request.urlopen(item["download"]) as site:
                    item["size"] = int(site.getheader("Content-Length"))
                    site.close()
            if not os.path.isfile(podcastfile(podcast,item)):
                podcast.downloaditem(item)
            elif os.stat(podcastfile(podcast,item)).st_size < int(item["size"]):
                print(os.stat(podcastfile(podcast,item)).st_size)
                podcast.downloaditem(item)

# do id3 tagging
for podcast in podcasts:
    for item in podcast.items:
        if os.path.isfile(podcastfile(podcast,item)):
            podcast.id3tag(item)
