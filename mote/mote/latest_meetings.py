import requests
import json
from flask import current_app
from mote.mote import util

seconds_delta = 86400
topic = 'org.fedoraproject.prod.meetbot.meeting.complete'


def get_latest_meetings():
    # config = util.config()
    url_template = "{}/datagrepper/raw?delta={}&topic={}".format(
        current_app.config['DATAGREPPER_BASE_URL'], seconds_delta, topic)

    # fetch meetings from the last day using datagrepper
    last_day_raw = requests.get(url_template)

    if not bool(last_day_raw):
        return []

    last_day = json.loads(last_day_raw.text)['raw_messages']

    # keep five latest meetings
    last_day_truncated = [k['msg'] for k in last_day[:4]]

    return last_day_truncated
