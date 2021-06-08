from mote.mote.mote import mote_bp
from flask import Flask, request
from config import config_options
from flask_babel import Babel
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
import requests
import json
from mote.mote import util


# translations
babel = Babel()


def create_app(config_name):
    app = Flask(__name__, template_folder='templates')

    # Load default configuration
    app.config.from_object(config_options[config_name])

    # fix trailing slash issues
    app.url_map.strict_slashes = False

    # enable multiple languages
    babel.init_app(app)

    # add attributes to app.config
    with app.app_context():
        if config_name == "development":
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240,
                                               backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

            app.logger.setLevel(logging.INFO)
            app.logger.info('App has been startup')
            if app.config['FAS_OPENID_ENDPOINT'] is not None:
                print(app.config['FAS_OPENID_ENDPOINT'])

        app.config['fn_search_regex'] = "(.*?)\.([0-9]{4}\-[0-9]{2}\-[0-9]{2})\-.*?\..*?\.(.*)"

        app.url_map.converters['regex'] = util.RegexConverter

        if app.config['USE_MAPPINGS_GITHUB'] == True:
            app.config['NAME_MAPPINGS'] = requests.get(
                "https://raw.githubusercontent.com/fedora-infra/mote/master/name_mappings.json").text
            app.config['CATEGORY_MAPPINGS'] = requests.get(
                "https://raw.githubusercontent.com/fedora-infra/mote/master/category_mappings.json").text
        else:
            with open(app.config['NAME_MAPPINGS_PATH'], 'r') as f:
                app.config['NAME_MAPPINGS'] = f.read()
            with open(app.config['CATEGORY_MAPPINGS_PATH'], 'r') as f:
                app.config['CATEGORY_MAPPINGS'] = f.read()

        app.config['NAME_MAPPINGS'] = util.map_name_aliases(
            json.loads(app.config['NAME_MAPPINGS']))
        app.config['CATEGORY_MAPPINGS'] = json.loads(
            app.config['CATEGORY_MAPPINGS'])

        logging_format = '%(asctime)-15s %(message)s'
        logging.basicConfig(format=logging_format)
        logger = logging.getLogger(__name__)

    app.register_blueprint(mote_bp)

    return app
