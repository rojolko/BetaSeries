#betaseries.com 
#Subtitles service allowed by www.betaseries.com 
import re, urllib, sys

OS_API = 'http://plexapp.api.opensubtitles.org/xml-rpc'
OS_LANGUAGE_CODES = 'http://www.opensubtitles.org/addons/export_languages.php'
OS_PLEX_USERAGENT = 'plexapp.com v9.0'
subtitleExt       = ['utf','utf8','utf-8','sub','srt','smi','rt','ssa','aqt','jss','ass','idx']

BS_SITE = 'http://api.betaseries.com'
BS_API_VERSION = "2.2"
BS_API_KEY  = '5eedfb7e79df'
BS_SHOW_URL = '%s/shows/search' % (BS_SITE)
BS_EPISODE_URL = '%s/episodes/search' % (BS_SITE)
BS_SUBTITLES_URL = '%s/subtitles/show' % (BS_SITE)
 
OS_ORDER_PENALTY = 0   # Penalty applied to subs score due to position in sub list return by OS.org. this value is set to 0 (previously -1) due to the OS default order is inconsistent (see forum discusion)
OS_BAD_SUBTITLE_PENALTY = -1000 # Penalty applied to subs score due to flag bad subtitle in response.
OS_WRONG_MOVIE_KIND_PENALTY = -1000 # Penalty applied if the video have the wrong kind (episode or movie)
OS_HEARING_IMPAIRED_BONUS = 10 # Bonus added for subs hearing impaired tagged when the pref is set to yes
OS_SUBRATING_GOOD_BONUS = 20 # Bonus added for subs with a rating of 0.0 or 10.0
OS_SUBRATING_BAD_PENALTY = -100 # Penalty for subs with a rating between 1 and 4
OS_TVSHOWS_GOOD_SEASON_BONUS = 30 # Bonus applied to TVShows subs if the season match
OS_TVSHOWS_GOOD_EPISODE_BONUS =  10 # Bonus applied if TH shows epiode number match
OS_MOVIE_IMDB_MATCH_BONUS = 50 # Bonus applied for a movie if the imdb id return by OS match the metadata in Plex
OS_TVSHOWS_SHOW_IMDB_ID_MATCH_BONUS = 30 # Bonus applied to TVShows subs if the imdbID of the show match
OS_TVSHOWS_EPISODE_IMDB_ID_MATCH_BONUS = 50 # Bonus applied to TVShows subs if the imdbID of the episode match
OS_ACCEPTABLE_SCORE_TRIGGER = 0 #Subs with score below this trigger will be removed
OS_TITLE_MATCH_BONUS = 10 # Bonus applied to video file if title in OS and in Plex match

TVDB_SITE  = 'http://thetvdb.com'
TVDB_PROXY = 'http://thetvdb.plexapp.com'
TVDB_API_KEY    = 'D4DDDAEFAD083E6F'

HEADERS = {"User-agent": OS_PLEX_USERAGENT , "Accept": "application/json", "X-BetaSeries-Key": BS_API_KEY, "X-BetaSeries-Version": BS_API_VERSION}


#Class to identify different search mode
class OS_Search_Methode:
    Hash, IMDB, Name = range(0, 3)

# Function taken from TheTVDB metadata agent
#TODO: Perhaps it is possible to use the function directly with the @expose decorator.

def GetResultFromBS(url):

    #Log("Retrieving URL: " + url)

    try:
      result = JSON.ObjectFromURL(url, headers=HEADERS, timeout=60, sleep=0.5)
    except:
      Log("Error (%s) retrieving url: %s" % result, url)
      return None
    
    return result

def Start():
  HTTP.CacheTime = CACHE_1HOUR * 4
  HTTP.Headers['User-Agent'] = OS_PLEX_USERAGENT

@expose
def opensubtitlesProxy():
  proxy = XMLRPC.Proxy(OS_API)
  username = Prefs["username"]
  password = Prefs["password"]
  if username == None or password == None:
    username = ''
    password = ''
  try:
    proxyResponse = proxy.LogIn(username, password, 'en', OS_PLEX_USERAGENT)
    if proxyResponse['status'] != "200 OK":
      Log('Error return by XMLRPC proxy: %s' % proxyResponse['status'])
      token = False
    else:
      token = proxyResponse['token']
  except Exception, e:
    Log('Unexpected error with OpenSubtitles.org XMLRPC API : %s' % str(e))
    token = False

 
  return (proxy, token)

def getLanguageOfPrimaryAgent(guid):
  #extract from the guid the language used by the primary_agent
  primaryAgentLanguage = None
  m = re.match(r'.*\?lang=(?P<primaryAgentLanguage>\w+)$', guid)
  if m != None:
    if m.group('primaryAgentLanguage') != False:
      primaryAgentLanguage = m.group('primaryAgentLanguage')
  return primaryAgentLanguage

def getIdfromTheTVDB(guid):
  #Extract from guid the primary data agent and the id of the show
  showTheTVDBId = False 
  m = re.match(r"(?P<primary_agent>.+):\/\/(?P<showID>\d+)", guid)
  if m != None:
    #Log("primary_agent: %s | showID: %s | seasonID: %s | episodeID: %s" % (m.group('primary_agent'), m.group('showID'), m.group('seasonID'), m.group('episodeID')))
    #If primary agent is TheTVDB, extract the tvshow and episode IMDN ids
    if m.group('primary_agent') ==  "com.plexapp.agents.thetvdb":
      #Fetch the TVDB show ID
      showTheTVDBId = m.group('showID')
                
  return  showTheTVDBId

def getShowIDFromBD(Title, TheTVDBShowId):
  showID = False
  try:
    url = "%s?title=%s" % (BS_SHOW_URL, urllib.quote_plus(Title)) 
    jsonShowBS = GetResultFromBS(url)
  except Exception, err:
    Log("Error searching show ID for %s on BetaSeries" % url)
    Log("Error : %s, line nr : %s", str(err), sys.exc_traceback.tb_lineno)
  try: 
    for shows in jsonShowBS.get("shows"):
       showID = shows.get("thetvdb_id")
       if int(showID) == int(TheTVDBShowId):
         return shows.get("id")
  except Exception, err:
    Log("Error get node shows: %s, line nr : %s", str(err), sys.exc_traceback.tb_lineno)
    return None
  return None

def getEpisodeIDFromBD(showID, seasonNr, episodeNr):
  episodeID = False
  seasonNr = "00" + seasonNr
  episodeNr = "00" + episodeNr
  numberEpisode = "s" + seasonNr[-2:] + "e" + episodeNr[-2:]
  try:
    url = "%s?show_id=%s&number=%s" % (BS_EPISODE_URL, showID, numberEpisode)
    jsonEpisodeBS = GetResultFromBS(url)
  except Exception, err:
    Log("Error searching episode ID for %s on BetaSeries" % showID)
    Log("Error : %s, line nr : %s", str(err), sys.exc_traceback.tb_lineno)
  try: 
    episode = jsonEpisodeBS.get("episode")
    episodeID = episode.get("id", [])
    return episodeID
  except Exception, err:
    Log("Error get node episode: %s, line nr : %s", str(err), sys.exc_traceback.tb_lineno)
    return None
  return None

def getLangList():
  langList = [Prefs["langPref1"]]
  if Prefs["langPref2"] != 'None' and Prefs["langPref1"] != Prefs["langPref2"]:
    langList.append(Prefs["langPref2"])
  return langList 

def downloadSubTitlesFromBS(showID, episodeID, language, mediaTitle, season, episode, part, token):
 
  try:
    url = "%s?id=%s" % (BS_SUBTITLES_URL, showID)
    jsonShowBS = GetResultFromBS(url)
  except Exception, err:
    Log("Error searching subtitles show for %s on BetaSeries" % url)
    Log("Error : %s, line nr : %s", str(err), sys.exc_traceback.tb_lineno)
  try: 
    for subtitles in jsonShowBS.get("subtitles", []):
      if subtitles.get("language") == "VF":
        episodes = subtitles.get("episode", [])
        if int(episodes["episode_id"]) == int(episodeID):
          subtitlesURL = subtitles.get("url", [])
          subGz = HTTP.Request(subtitlesURL, headers={'Accept-Encoding':'gzip'}).content
          subData = Archive.GzipDecompress(subGz)
          #part.subtitles[Locale.Language.Match(st['SubLanguageID'])][subUrl] = Proxy.Media(subData, ext=st['SubFormat'])
  except Exception, err:
    Log("Error getting node subtitles: %s, line nr : %s", str(err), sys.exc_traceback.tb_lineno)
    return None


class BetaSeriesAgentTV(Agent.TV_Shows):
  name = 'BetaSeries.com'
  languages = [Locale.Language.NoLanguage]
  primary_provider = False
  contributes_to = ['com.plexapp.agents.thetvdb']

  def search(self, results, media, lang):
    results.Append(MetadataSearchResult(
      id    = 'null',
      score = 100
    ))

  def update(self, metadata, media, lang):
    (proxy, token) = opensubtitlesProxy()
    if token == False:
      Log('Subtitles search stop due to a problem with the OpenSubtitles API')
    else:
      TheTVDBShowId = getIdfromTheTVDB(media.guid)
      for season in media.seasons:
        # just like in the Local Media Agent, if we have a date-based season skip for now.
        if int(season) < 1900:
          for episode in media.seasons[season].episodes:
            for i in media.seasons[season].episodes[episode].items:
              primaryAgentLanguage = getLanguageOfPrimaryAgent(media.seasons[season].episodes[episode].guid)
              for part in i.parts:
                # Remove all previous subs (taken from sender1 fork)
                for l in part.subtitles:
                  part.subtitles[l].validate_keys([])

                # go fetch subtilte fo each language
                for language in getLangList():
                  showID = getShowIDFromBD(media.title, TheTVDBShowId)
                  if showID != None:
                    episodeID = getEpisodeIDFromBD(showID, season, episode)
                    if episodeID != None:
                       downloadSubTitlesFromBS(showID, episodeID, language, media.title, season, episode, part, token)
                    else:
                      Log("No episode ID find with TheTVDB ID! Stopping downloading of subtitles for this episode")
                  else:
                    Log("No show ID find with TheTVDB ID! Stopping downloading of subtitles for this episode")
                    
