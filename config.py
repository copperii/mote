"""Flask configuration."""
from os import environ, path
import random
import string
from dotenv import load_dotenv

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))


class Config(object):
    """Config for all instances."""
    SECRET_KEY = environ.get(
        'SECRET_KEY') or 'Some-really-long-key-for-secret-change-this-to-be-secure'
    OLD_APP_SECRET_KEY = ''.join(random.SystemRandom().choice(
        string.ascii_uppercase + string.digits) for _ in range(20))

    FAS_OPENID_ENDPOINT = 'http://id.fedoraproject.org/'
    FAS_CHECK_CERT = True
    '''
    General Configuration
    '''
    # admin_groups currently has no effect on the application
    # it is reserved for future use
    ADMIN_GROUPS = ["sysadmin-mote"]
    MEMCACHED_IP = "127.0.0.1:11211"
    # memcached must be installed for this feature
    # use_memcached = False # Use a memcached store for greater performance
    USE_MEMCACHED = False  # Use a memcached store for greater performance

    # JSON cache store location
    JSON_CACHE_LOCATION = "./cache.json"

    # Use group/name mappings fetched from GitHub
    USE_MAPPINGS_GITHUB = True

    # If use_mappings_github is False, set alternate path
    NAME_MAPPINGS_PATH = "/usr/share/mote/name_mappings.json"
    CATEGORY_MAPPINGS_PATH = "/usr/share/mote/category_mappings.json"

    '''
    Crawler Configuration
    '''

    LOG_ENDPOINT = "/srv/web/meetbot"
    #log_endpoint = "/home/user/mote/test_data/meetbot"

    # Fedora has a "teams" folder which contains
    # logs from meetings started with a certain team name
    # for instance, `#startmeeting famna` will save in "/teams/famna"
    # Folders not in "teams" reflect the channel name of the meeting
    LOG_TEAM_FOLDER = "teams"

    # Directories to ignore in crawling the logs.
    # These folders are ignored. The "meetbot" folder is
    # an infinite loop on Fedora's meetbot instance.
    IGNORE_DIR = "meetbot"

    # Location where raw logs/minutes are stored (remote location)
    MEETBOT_PREFIX = "http://meetbot-raw.fedoraproject.org"

    # Location to fetch raw logs/minutes from (remote or local location)
    MEETBOT_FETCH_PREFIX = "http://meetbot-raw.fedoraproject.org"

    # Time (in seconds) after which the log/meeting cache expires
    CACHE_EXPIRE_TIME = 60 * 60 * 1

    # datagrepper URL
    DATAGREPPER_BASE_URL = "https://apps.fedoraproject.org"


class ProductionConfig(Config):
    FLASK_ENV = 'production'
    DEBUG = False
    TESTING = False
    PROD_READ = 'Just a string telling ProductionConfig has been read'


class DevConfig(Config):
    FLASK_ENV = 'development'
    DEBUG = True
    TESTING = True
    DEV_READ = 'Just a string telling Development Config has been read'
    ENABLE_DEBUG = True
    APP_PORT = 5000
    APP_HOST = "127.0.0.1"


config_options = {
    'development': DevConfig,
    'production': ProductionConfig
}
