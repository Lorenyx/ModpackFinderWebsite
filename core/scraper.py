import logging, threading

logFormatter = '[%(asctime)s]  %(levelname)s - %(message)s'
logging.basicConfig(format=logFormatter, level=logging.DEBUG)
log = logging.getLogger(__name__)
# handler = logging.FileHandler('myLogs.log')
# handler.setLevel(logging.WARNING)
# log.addHandler(handler)

import requests
from bs4 import BeautifulSoup
import logging

class Scraper:
  def __init__(self, url):
    self.lock = threading.Lock()
    self.url = str(url) # the URL that is passed (FINAL)
    self.name = None # name of the modpack
    self.max_page = 1 # amount of pages in the mod dependents (assigned at start)
    self.page_per_thread = 1 # how many pages each thread should handle (assigned at start)
    self.mod_dict={} # dictionary of all the modpacks {mod_name : mod_link}
    self.response_code = self.start() # initializes everything


  def start(self):
    "main method to get everything running"
    soup = self.request_url()
    if soup in ['Invalid URL', 'Forbidden', 'Not Found']:
      log.warning(f'[-] URL request failed: REASON - {soup}')
      return soup
    else:
      self.get_mod_name(soup)
      self.get_max_page(soup)
      log.info(f'[=] Getting modpacks for {self.url}')
      
    if self.max_page < 2:
      self.thread_dependents()
    else:
      self.page_per_thread = self.max_page / 10
      from math import floor, ceil
      if round(self.page_per_thread) > self.page_per_thread:
        self.page_per_thread=ceil(self.page_per_thread)
      elif self.page_per_thread < 1:
        self.page_per_thread = 2
      else:
        self.page_per_thread=floor(self.page_per_thread)
      for worker_id in range(10):
        t = threading.Thread(target=self.thread_dependents, args=(worker_id,))
        t.start()

      logging.debug('Waiting for worker threads')
      main_thread = threading.main_thread()
      for t in threading.enumerate():
        if t is not main_thread:
            t.join()
    return self.mod_dict


  def thread_dependents(self, worker_id=-1):
    "Sets up the get dependents in a thread way, worker id MUST BE zero order (ie. 0, 1, 2)"
    if worker_id == -1:
      for x in range(1,self.max_page+1):
        self.get_page(x)
    else:
      start = (self.page_per_thread * (worker_id+1)) - self.page_per_thread
      log.info(f'id:{worker_id} Pages - {self.page_per_thread}')
      end = start + self.page_per_thread
      log.info(f'var END = {end}')
      for x in range(start, end):
        if x > self.max_page:
          break
        self.get_page(x)


  def get_page(self, page_num):
    "Parses the page and adds the mod name and link to the mod_dict"
    soup = self.request_url(page_num)
    table = soup.find('ul', class_='listing listing-project project-listing')
    for mod in table.findAll('li'):
      name = mod.h3.text.strip()
      link = mod.a.get('href')
      if 'modpacks' in link:
        self.mod_dict[name]=Scraper.fill_href(link)
      # print(f'{name} <==> {link}')

  
  def get_max_page(self, soup):
    "Returns the max page count of the mod dependecies"
    html = soup.find('div', class_='mb-4')
    numbers = html.find_all('span', class_='text-primary-500')
    if len(numbers) == 0:
      self.max_page = 1
    elif len(numbers) == 1:
      self.max_page = int(numbers[0].text)
    else: 
      self.max_page = int(numbers[-1].text)
    return self.max_page


  def request_url(self, page_num=1):
    "Grabs the URL and returns the error code of if it happens else returns the html code"
    if not self.url.startswith('https://www.curseforge.com/minecraft/mc-mods/'):
      return 'Invalid URL'
    headers = { 'User-Agent':'Mozilla/5.0' }
    response = requests.get(self.make_url(page_num), headers=headers)
    # print(response.status_code)
    if response.status_code == 403:
      return 'Forbidden'
    if response.status_code == 404:
      return 'Not Found'
    return BeautifulSoup(response.content, 'html.parser') 


  def make_url(self, page_num):
    "Updates the url for the next page"
    if '/relations/dependents?page=' not in self.url:
      url = f'{self.url}/relations/dependents?page={page_num}'
    else:
      url = f'{self.url[:-1]}{page_num}'
    return url


  def get_mod_name(self, soup):
    "Gets the name of the mod"
    self.name = soup.find('h2', class_='font-bold text-lg break-all').text
    return self.name


  @staticmethod
  def fill_href(text):
    "Turns the hyperlink into a full link"
    return f'https://www.curseforge.com{text}'

# s = Scraper('https://www.curseforge.com/minecraft/mc-mods/better-crates')
# s.start()
# print(f'22 | {len(s.mod_dict)}')
