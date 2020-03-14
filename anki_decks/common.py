import requests
from jinja2 import Environment, PackageLoader, select_autoescape

jinja_env = Environment(
    loader=PackageLoader("anki_decks", "templates"),
    autoescape=select_autoescape(["html", "xml"]),
)

css = requests.get(
    "https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css"
).text
