from sanic import Sanic
from sanic.response import html, redirect, text
from sanic_session import Session, InMemorySessionInterface
import jinja2, sanic

app = Sanic(name='lore_test_run')
session = Session(app, interface=InMemorySessionInterface())

templateLoader = jinja2.FileSystemLoader(searchpath="./templates")
templateEnv = jinja2.Environment(loader=templateLoader)
app.static('/static', './static')
app.static('/font', './font')


@app.route('/')
async def home(request):
  return render('home.html')


@app.route('/dependents')
async def show_dependents(request):
  urls = dict(request.get_args())['mod_url']
  print(urls)
  scraps = await make_scraps(urls) 
  print(type(scraps))
  if isinstance(scraps, sanic.response.HTTPResponse):
    return scraps
  mod_dict, mod_name = scraps
  return render("list.html", mod_dict=mod_dict, mod_name=mod_name)


def render(file_name, **args):
  return html(templateEnv.get_template(file_name).render(args))


from .scraper import Scraper
async def make_scraps(urls):
  "Turns URLS into Scraper objects then returns tuple of (mod_dict, mod_name)"
  scraps = [Scraper(url) for url in urls]
  error_log=''
  for scrap in scraps:
    if scrap.response_code in ['Invalid URL', 'Forbidden', 'Not Found']:
      error_log+=f'[-] Error: {scrap.url} is {scrap.response_code}\n'
  if error_log:
    return text(error_log)
  mod_dict = await make_mod_dict(scraps)
  mod_name = await make_mod_name(scraps)
  return (mod_dict, mod_name)


async def make_mod_dict(scraps):
    mod_dict = {}
    for s in scraps:
        mod_dict.update(s.mod_dict)
    return mod_dict


async def make_mod_name(scraps):
    "Combines all the mod names into a nice view"
    return ', '.join([s.name for s in scraps])


def run():
    app.run(host='0.0.0.0')
