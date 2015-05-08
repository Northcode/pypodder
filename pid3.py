import importlib

needsinstall = False

def checkmodule(mod):
    loader = importlib.find_loader(mod)
    if loader is None:
        print("Please install python module %s" % mod)
        needsinstall = True

checkmodule('xml')
checkmodule('pytag')
checkmodule('argparse')

if needsinstall:
    print("exiting")
    exit()

import xml.etree.cElementTree as xml
import pytag, os, argparse, sys
from urllib.request import urlretrieve as wget
import urllib

feedlistfile = "feed.list"
feedlist = []
feedlistformat = ['url','name']

taglist = {'artist':'%owner%','album':'%podcast%','track':'%title%'}

pytag.interface.MIMETYPE['application/octet-stream'] = (pytag.formats.Mp3Reader, pytag.formats.Mp3)

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
    
def podcastfile(podcast,item):
    return os.path.join(podcast.title,item["title"] + ".mp3")

def feedfile(feed):
    return feed["name"] + ".rss"

def downloadprogress(blocknum,blocksize,totalsize):
    percent = blocknum * blocksize * 1e2 / totalsize
    barpercent = int(percent / 5)
    if verbose:
        if progstyle == "percent":
            sys.stdout.write("\rdownloading: %d%%" % percent)
        elif progstyle == "bar":
            sys.stdout.write("\r[%s]" % "#" * barpercent)
        elif progstyle == "line":
            sys.stdout.write("\r%s" % "-" * barpercent)
        elif progstyle == "percentbar":
            sys.stdout.write("\r[%s] %d%% of total %d" % ("#" * barpercent, percent,totalsize))
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
        del(xmlreader)

    def id3tag(self,item):
        if verbose:
            print("id3taging %s" % item["title"])
        tags = pytag.Audio(podcastfile(self,item))
        tags.write_tags({'title': item["title"], 'album': self.title, 'artist': "Podcast" })
        print(tags.get_tags())
                    
    def downloaditem(self,item):
        if verbose:
            print("downloading %s" % item["title"])
        download = wget(item["download"],podcastfile(self,item),downloadprogress)

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

# download new episodes
if not onlytag:
    for podcast in podcasts:
        if verbose:
            print("downloading items for {}".format(podcast.title))
        for item in podcast.items:
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
