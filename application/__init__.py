from flask import Flask
from owslib.wfs import WebFeatureService

import secret


app = Flask(__name__)
app.config['SECRET_KEY'] = secret.secret_key

wfs_url = "https://gis.vantaa.fi/geoserver/wfs?"

wfs = WebFeatureService(url=wfs_url)


from application import routes