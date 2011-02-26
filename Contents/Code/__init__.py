
#import base64
import re
####################################################################################################

VIDEO_PREFIX = "/video/crackle"

NAMESPACES = {'media':'http://search.yahoo.com/mrss/'}

CRACKLE_ROOT = "http://www.crackle.com"
CRACKLE_TV = "http://www.crackle.com/shows/index.aspx?c=114&name=Television#"
CRACKLE_MOVIES = "http://www.crackle.com/shows/shows.aspx?cl=o%3D2%26fa%3D82%26fs%3D%26fx%3D&st=a"
TV_ID = "522632"
ORIGINALS_ID = "522638"
SHOW_JSON = "http://www.crackle.com/browse/MediaListChunk.aspx?ci=644&id=%s&dci=True&startindex=0&itemCount=%s"

MOVIE_RSS = "http://www.crackle.com/rss/media/Zm14PTUwMDAmZmNtdD04MiZmcD0xJmZ4PQ.rss"
TRAILERS_RSS = "http://www.crackle.com/rss/media/bz0xMiZmcGw9NTE5NzQzJmZ4PQ.rss"
IN_THEATERS_RSS = "http://www.crackle.com/rss/media/bz0xMiZmcGw9NTIzMDc5JmZ4PQ.rss"
  ##ORIGINAL_SERIES_TRAILERS_RSS = "http://www.crackle.com/rss/media/bz0xMiZmcGw9NTMwMTE1JmZ4PQ.rss"
  ##WHY_IT_CRACKLES_RSS = "http://www.crackle.com/rss/media/bz0xMiZmcGw9NTE4ODU2JmZ4PQ.rss"
  ##TV_RSS = "http://www.crackle.com/rss/media/Zm14PTUwMDAmZmNtdD0xMTQmZnA9MSZmeD0.rss"
  ##TV   http://www.crackle.com/rss/media/bz0xMiZmcGw9NTIyNjMyJmZ4PQ.rss
  ##  http://www.crackle.com/browse/MediaListChunk.aspx?ci=644&id=522632&l=False&dci=True&m=False&startindex=0&itemCount=74
  ##ORIGINALS_RSS = "http://www.crackle.com/rss/media/Zm14PTUwMDAmZmNtdD00NiZmcD0xJmZ4PQ.rss"

NAME = 'Crackle'
COUNTRY = Locale.Geolocation

ART           = 'Crackle.png'
ICON          = 'Crackle_logo.png'

####################################################################################################

def Start():

    Plugin.AddPrefixHandler(VIDEO_PREFIX, MainMenu, NAME, ICON, ART)

    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
    MediaContainer.art = R(ART)
    MediaContainer.title1 = NAME
    DirectoryItem.thumb = R(ICON)


####################################################################################################
def MainMenu():
    dir = MediaContainer(mediaType='video')
    dir.Append(Function(DirectoryItem(TVList, "TV Shows"), id = TV_ID))
    dir.Append(Function(DirectoryItem(TVList, "Originals"), id = ORIGINALS_ID))
    dir.Append(Function(DirectoryItem(MovieList, "Movies"), pageUrl = MOVIE_RSS))
    dir.Append(Function(DirectoryItem(MovieList, "Trailers"), pageUrl = TRAILERS_RSS))
    dir.Append(Function(DirectoryItem(MovieList, "In Theaters"), pageUrl = IN_THEATERS_RSS))
    return dir
	
####################################################################################################
def TVList(sender, id):
    dir = MediaContainer(title2=sender.itemTitle, viewGroup="List")
    showMap = dict()
    link = "http://www.crackle.com/c/georestrictions"
    predicate = "//span[@id='mediaCount%s']" % id
    count = HTML.ElementFromURL(link).xpath(predicate)[0].text
    content = JSON.ObjectFromURL(SHOW_JSON % (id, count))
    for item in content:
        showcontent = HTML.ElementFromString(item['content'])
        link = CRACKLE_ROOT + showcontent.xpath('//a')[0].get('href')
        thumb = showcontent.xpath('//img')[0].get('src')
        title = showcontent.xpath('//p')[0].text
        sortTitle = title.replace('A ', '').replace('The ', '')
        eventList = showMap.get(sortTitle)
        if eventList == None:
            eventList = []
            showMap[sortTitle] = eventList
        # Tuple order here matters
        eventList.append((link, thumb, title))
            
    events = showMap.keys()[:]
    events.sort()
    for show in events:
        for event in showMap[show]:
            Log(event[0])
            dir.Append(Function(DirectoryItem(EpisodeList, title=event[2], thumb=event[1]), link=event[0]))
    return dir

####################################################################################################
def EpisodeList(sender, link):
    dir = MediaContainer(title2=sender.itemTitle, viewGroup="InfoList")
    feed = HTML.ElementFromURL(link).xpath("//div[contains(@id, 'playlistRSS')]/a")[0].get('href')
    feed = CRACKLE_ROOT + feed
    content = XML.ElementFromURL(feed).xpath("//item", namespaces=NAMESPACES)
    for item in content:
        title = item.xpath("./media:title", namespaces=NAMESPACES)[0].text
        title = title.replace('amp;', '')
        link = item.xpath("./media:content", namespaces=NAMESPACES)[0].get('url')  ## FULL SCREEN PLAYER
        id = re.findall('id=(.+?)&', link)[0]
        #Log("id: " + id)
        #player = "http://www.crackle.com/flash/ReferrerRedirect.ashx?id=" + id  #NEEDS A COOKIE
        player = "http://www.crackle.com/gtv/WatchShow.aspx?id=" + id
        duration = int(item.xpath("./media:content", namespaces=NAMESPACES)[0].get('duration')) * 1000
        #link = item.xpath("./media:player", namespaces=NAMESPACES)[0].get('url')  ## EMBEDED PLAYER
        #Log(player)
        thumb = item.xpath("./media:thumbnail", namespaces=NAMESPACES)[2].get('url')
        summary = item.xpath("./media:description", namespaces=NAMESPACES)[0].text
        rating = item.xpath("./media:rating", namespaces=NAMESPACES)[0].text
        rating = rating.upper()
        restriction = item.xpath("./media:restriction", namespaces=NAMESPACES)[0].text
        if COUNTRY in restriction:
            dir.Append(Function(WebVideoItem(PlayVideo, summary=summary, thumb=thumb, title=title, subtitle=rating, duration=duration), link=player))
    return dir

####################################################################################################
def PlayVideo(sender, link):
    return Redirect(WebVideoItem(link))
####################################################################################################
def MovieList(sender, pageUrl):
    dir = MediaContainer(title2=sender.itemTitle, viewGroup="InfoList")
    content = XML.ElementFromURL(pageUrl).xpath("//item", namespaces=NAMESPACES)
    movieMap = dict()
    for item in content:
        title = item.xpath("./media:title", namespaces=NAMESPACES)[0].text
        title = title.replace('amp;', '')
        sortTitle = title.replace('A ', '').replace('The ', '')
        link = item.xpath("./media:content", namespaces=NAMESPACES)[0].get('url')  ## FULL SCREEN PLAYER
        id = re.findall('id=(.+?)&', link)[0]
        #Log("id: " + id)
        #player = "http://www.crackle.com/flash/ReferrerRedirect.ashx?id=" + id + "&width=1920&height=1080"  #NEEDS A COOKIE
        player = "http://www.crackle.com/gtv/WatchShow.aspx?id=" + id
        duration = int(item.xpath("./media:content", namespaces=NAMESPACES)[0].get('duration')) * 1000
        #link = item.xpath("./media:player", namespaces=NAMESPACES)[0].get('url')  ## EMBEDED PLAYER
        #Log(player)
        thumb = item.xpath("./media:thumbnail", namespaces=NAMESPACES)[2].get('url')
        summary = item.xpath("./media:description", namespaces=NAMESPACES)[0].text
        rating = item.xpath("./media:rating", namespaces=NAMESPACES)[0].text
        rating = rating.upper()
        restriction = item.xpath("./media:restriction", namespaces=NAMESPACES)[0].text
        if COUNTRY in restriction:
            eventList = movieMap.get(sortTitle)
            if eventList == None:
                eventList = []
                movieMap[sortTitle] = eventList
            # Tuple order here matters
            eventList.append((player, thumb, summary, title, rating, duration))
            
    events = movieMap.keys()[:]
    events.sort()
    for movie in events:
        for event in movieMap[movie]:
            dir.Append(Function(WebVideoItem(PlayVideo, summary=event[2], thumb=event[1], title=event[3], subtitle=event[4], duration=event[5]), link=event[0]))
            # Same order they went into the tuple
    return dir