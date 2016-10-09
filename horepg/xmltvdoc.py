import xml.dom.minidom
import time
import datetime
import calendar

class XMLTVDocument(object):
  # this renames some of the channels
  add_display_name = {}
  category_map = {
    'tv drama': 'movie/drama (general)',
    'actie': 'movie/drama (general)',
    'familie': 'movie/drama (general)',
    'thriller': 'detective/thriller',
    'detective': 'detective/thriller',
    'avontuur': 'detective/thriller',
    'western': 'detective/thriller',
    'horror': 'science fiction/fantasy/horror',
    'sci-fi': 'science fiction/fantasy/horror',
    'komedie': 'comedy',
    'melodrama': 'science fiction/fantasy/horror',
    'romantiek': 'romance',
    'drama': 'serious/classical/religious/historical movie/drama',
    'erotiek': 'adult movie/drama',
    'nieuws': 'news/current affairs (general)',
    'weer': 'news/weather report',
    'nieuws documentaire': 'news magazine',
    'documentaire': 'documentary',
    'historisch': 'documentary',
    'waar gebeurd': 'documentary',
    'discussie': 'discussion/interview/debate',
    'show': 'game show/quiz/contest',
    'variété': 'variety show',
    'talkshow': 'talk show',
    'sport': 'sports (general)',
    'gevechtssport': 'martial sports',
    'wintersport': 'winter Sports',
    'paardensport': 'equestrian',
    'evenementen': 'special event',
    'sportmagazine': 'sports magazine',
    'voetbal': 'football/soccer',
    'tennis/squash': 'tennis/squash',
    'teamsporten': 'Team sports',
    'atletiek': 'athletics',
    'motorsport': 'motor sport',
    'extreme': 'motor sport',
    'watersport': 'water sport',
    'kids/jeugd': 'children\'s/youth program (general)',
    'kids 0 - 6': 'pre-school children\'s program',
    'jeugd 6 - 14': 'entertainment (6-14 year old)',
    'jeugd 10 - 16': 'entertainment (10-16 year old)',
    'poppenspel': 'cartoon/puppets',
    'educatie': 'information/educational/school program',
    'muziek': 'music/ballet/dance',
    'ballet': 'ballet',
    'easy listening': 'music/ballet/dance',
    'musical': 'musical/opera',
    'rock/pop': 'rock/pop',
    'klassiek': 'serious music/classical music',
    'volksmuziek': 'folk/traditional music',
    'jazz': 'jazz',
    'musical': 'musical/opera',
    'lifestyle': 'arts/culture (without music, general)',
    'beeldende kunst': 'performing arts',
    'mode': 'fashion',
    'kunst magazine': 'arts/culture magazines',
    'kunst/cultuur': 'arts/culture magazines',
    'religie': 'religion',
    'popart': 'popular culture/traditional arts',
    'literatuur': 'literature',
    'speelfilm': 'film/cinema',
    'shorts': 'experimental film/video',
    'special': 'broadcasting/press',
    'maatschappelijk': 'social/political issues/economics (general)',
    'actualiteiten': 'magazines/reports/documentary',
    'economie': 'economics/social advisory',
    'beroemdheden': 'remarkable people',
    'educatie': 'education/science/factual topics (general)',
    'natuur': 'nature/animals/environment',
    'technologie': 'technology/natural sciences',
    'geneeskunde': 'medicine/physiology/psychology',
    'expedities': 'foreign countries/expeditions',
    'sociologie': 'social/spiritual sciences',
    'educatie divers': 'further education',
    'talen': 'languages',
    'vrije tijd': 'leisure hobbies (general)',
    'reizen': 'tourism/travel',
    'klussen': 'handicraft',
    'auto en motor': 'motoring',
    'gezondheid': 'fitness & health',
    'koken': 'cooking',
    'shoppen': 'advertisement/shopping',
    'tuinieren': 'gardening'
    }

  def __init__(self):
    impl = xml.dom.minidom.getDOMImplementation()
    doctype = impl.createDocumentType('tv', None, 'xmltv.dtd')
    self.document = impl.createDocument(None, 'tv', doctype)
    self.document.documentElement.setAttribute('source-info-url', 'https://horizon.tv')
    self.document.documentElement.setAttribute('source-info-name', 'UPC Horizon API')
    self.document.documentElement.setAttribute('generator-info-name', 'HorEPG v1.0')
    self.document.documentElement.setAttribute('generator-info-url', 'beralt.nl/horepg')
  def addChannel(self, channel_id, display_name, icon = None):
    element = self.document.createElement('channel')
    element.setAttribute('id', channel_id)

    if display_name in XMLTVDocument.add_display_name:
      for name in XMLTVDocument.add_display_name[display_name]:
        dn_element = self.document.createElement('display-name')
        dn_text = self.document.createTextNode(name)
        dn_element.appendChild(dn_text)
        element.appendChild(dn_element)
    else:
      if type(display_name) == list:
        for name in display_name:
          dn_element = self.document.createElement('display-name')
          dn_text = self.document.createTextNode(name)
          dn_element.appendChild(dn_text)
          element.appendChild(dn_element)
      else:
        dn_element = self.document.createElement('display-name')
        dn_text = self.document.createTextNode(display_name)
        dn_element.appendChild(dn_text)
        element.appendChild(dn_element)

    if(icon):
      lu_element = self.document.createElement('icon')
      lu_element.setAttribute('src', icon)
      element.appendChild(lu_element)

    self.document.documentElement.appendChild(element)

  def addProgramme(self, channel_id, title, start, end, episode = None, episode_title = None, description = None, categories = None):
    element = self.document.createElement('programme')
    element.setAttribute('start', XMLTVDocument.convert_time(int(start)))
    element.setAttribute('stop', XMLTVDocument.convert_time(int(end)))
    element.setAttribute('channel', channel_id)
    # quick tags
    self.quick_tag(element, 'title', title)
    if episode:
      self.quick_tag(element, 'episode-num', episode, {'system': 'onscreen'})
    if description:
      self.quick_tag(element, 'desc', description) 
    if episode_title:
      self.quick_tag(element, 'sub-title', episode_title)
    # categories
    if categories:
      for cat in categories:
        if '/' not in cat:
          cat_title = XMLTVDocument.map_category(cat.lower())
          if cat_title:
            self.quick_tag(element, 'category', cat_title)
          else:
            self.quick_tag(element, 'category', cat)
    self.document.documentElement.appendChild(element)
  def map_category(cat):
    if cat in XMLTVDocument.category_map:
      return XMLTVDocument.category_map[cat]
    return False
  def quick_tag(self, parent, tag, content, attributes = False):
    element = self.document.createElement(tag)
    text = self.document.createTextNode(content)
    element.appendChild(text)
    if attributes:
      for k, v in attributes.items():
        element.setAttribute(k, v)
    parent.appendChild(element)
  def convert_time(t):
    return time.strftime('%Y%m%d%H%M%S', time.gmtime(t))
