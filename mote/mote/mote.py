import re
from flask_babel import _
from flask import Blueprint, render_template, g, redirect, url_for, current_app, request
from flask import abort, jsonify
from flask_babel import _, get_locale
from mote.mote import util
from mote.mote import soke
import logging

import requests
import json
from bs4 import BeautifulSoup
from six.moves import html_parser
import dateutil
import collections


mote_bp = Blueprint('mote', __name__)


def get_cache_data(key_name):
    if key_name == "mote:team_meetings":
        meeting_type = "team"
    elif key_name == "mote:channel_meetings":
        meeting_type = "channel"
    elif key_name == "mote:latest_meetings":
        meeting_type = "latest_meetings"
    else:
        meeting_type = None
    try:
        res = util.get_json_cache(meeting_type)
    except RuntimeError:
        print(f'runtimeerror in mote.get_cache_data {RuntimeError}')
        soke.run()
        res = util.get_json_cache(meeting_type)
    return res


def handle_meeting_date_request(group_type, meeting_group, date_stamp):
    try:
        meetings = get_cache_data("mote:{}_meetings".format(group_type))

        workable_array = meetings[meeting_group][date_stamp]
        minutes = workable_array["minutes"]
        logs = workable_array["logs"]
        return render_template(
            "date-list.html",
            minutes=minutes,
            date=date_stamp,
            logs=logs,
            type=group_type,
            group_name=meeting_group
        )
    except KeyError:
        raise ValueError("Meetings unable to be located.")


def return_error(msg):
    return render_template('error.html', error=msg)


def get_friendly_name(group_id, channel=False):
    if channel == True:
        group_id = "#{}".format(group_id)

    try:
        friendly_name = current_app.config['NAME_MAPPINGS'][group_id]["friendly-name"]
    except KeyError:
        friendly_name = False

    return friendly_name


@mote_bp.route('/1')
def motehome():

    return render_template("motehome.html", title=_('Fedora møte'))


@mote_bp.route('/', methods=['GET'])
def index():
    # init here for now

    # Get latest meetings
    latest_meetings = get_cache_data('mote:latest_meetings')

    # Renders main page template.
    return render_template('index.html',
                           latest_meetings=latest_meetings)


@mote_bp.app_errorhandler(404)
@mote_bp.app_errorhandler(404)
def error_404(error):
    return render_template("404.html"), 404


@mote_bp.app_errorhandler(500)
def error_500(error):
    return render_template("500.html"), 500


@mote_bp.route('/<meeting_channel>/<regex("([0-9]{4}\-[0-9]{2}\-[0-9]{2})"):date_stamp>')
@mote_bp.route('/<meeting_channel>/<regex("([0-9]{4}\-[0-9]{2}\-[0-9]{2})"):date_stamp>/')
def catch_channel_date_request(meeting_channel, date_stamp):
    try:
        return handle_meeting_date_request("channel", meeting_channel, date_stamp)
    except ValueError:
        return return_error("Requested meetings could not be located.")


@mote_bp.route('/teams/<meeting_team>/<regex("([0-9]{4}\-[0-9]{2}\-[0-9]{2})"):date_stamp>')
@mote_bp.route('/teams/<meeting_team>/<regex("([0-9]{4}\-[0-9]{2}\-[0-9]{2})"):date_stamp>/')
def catch_team_date_request(meeting_team, date_stamp):
    try:
        return handle_meeting_date_request("team", meeting_team, date_stamp)
    except ValueError:
        return return_error("Requested meetings could not be located.")


@mote_bp.route('/teams/<meeting_team>')
@mote_bp.route('/teams/<meeting_team>/')
def catch_team_baserequest(meeting_team):
    url = url_for('sresults', group_id=meeting_team, type='team')
    return redirect(url)


@mote_bp.route('/<meeting_channel>/<date>/<regex("(.*?)\.[0-9]{4}\-[0-9]{2}\-[0-9]{2}\-.*"):file_name>')
def catch_channel_logrequest(date, file_name, meeting_channel):
    # This route catches standard log requests (.log.html, .html, or .txt)
    # Links referencing a meeting channel will be caught by this route.
    # These URLs include those provided by MeetBot at the end of a meeting,
    # or links referencing a specific meeting channel,
    # such as #fedora-meeting or #fedora-ambassadors
    # example: https://meetbot.fedoraproject.org/fedora-meeting-1/2015-02-09/releng.2015-02-09-16.31.html

    m = re.search(current_app.config['FN_SEARCH_REGEX'], file_name)
    if m == None:
        return abort(404)

    log_extension = m.group(3)  # type of log requested: log.html, html, or txt

    meeting_date = date  # date of log requested: YYYY-MM-DD
    log_type = util.get_meeting_type(log_extension)

    if log_type == "plain-text":
        # Redirect to the plaintext file is one is requested.
        built_url = "{}/{}/{}/{}".format(
            current_app.config['MEETBOT_PREFIX'], meeting_channel, date, file_name)
        return redirect(built_url)

    return render_template("single-log.html", gtype="channel", ltype=log_type, group=meeting_channel, date=meeting_date, filename=file_name)


@mote_bp.route('/teams/<meeting_team>/<regex("(.*?)\.[0-9]{4}\-[0-9]{2}\-[0-9]{2}\-.*"):file_name>')
def catch_team_logrequest(file_name, meeting_team):
    # This route catches standard log requests (.log.html, .html, or .txt)
    # Links referencing a meeting team will be caught by this route.
    # e.g referencing famna or infrastructure
    # example: https://meetbot.fedoraproject.org/teams/fedora-mktg/fedora-mktg.2013-10-07-19.02.html

    m = re.search(current_app.config['FN_SEARCH_REGEX'], file_name)
    if m == None:
        return abort(404)

    group_name = m.group(1)  # name of team, e.g famna
    meeting_date = m.group(2)  # date of log requested: YYYY-MM-DD
    log_extension = m.group(3)  # type of log requested: log.html, html, or txt
    log_type = util.get_meeting_type(log_extension)

    if log_type == "plain-text":
        built_url = "{}/teams/{}/{}".format(current_app.config['MEETBOT_PREFIX'],
                                            meeting_team, file_name)
        return redirect(built_url)

    return render_template("single-log.html", gtype="team", ltype=log_type, group=group_name, date=meeting_date, filename=file_name)


@mote_bp.route('/request_logs')
@mote_bp.route('/request_logs/')
def request_logs():
    """ Return a list of filenames for minutes and/or logs
    for a specified date.
    """
    group_id = request.args["group_id"]
    group_type = request.args["group_type"]
    date_stamp = request.args["date_stamp"]
    if group_type == "team":
        meetings = get_cache_data("mote:team_meetings")
    elif group_type == "channel":
        meetings = get_cache_data("mote:channel_meetings")
    try:
        workable_array = meetings[group_id][date_stamp]
        minutes = workable_array["minutes"]
        logs = workable_array["logs"]

        response = json.dumps({"minutes": minutes, "logs": logs})
        return response
    except:
        abort(404)


@mote_bp.route('/get_meeting_log')
@mote_bp.route('/get_meeting_log/')
def get_meeting_log():
    """ Return specific logs or minutes to client. """
    group_type = request.args['group_type']
    date_stamp = request.args['date_stamp']
    group_id = request.args['group_id']

    file_name = request.args['file_name']
    file_type = request.args.get('file_type')

    file_name = html_parser.unescape(file_name)

    if group_type == "team":
        link_prefix_ending = "/teams/" + group_id + "/"
    else:
        link_prefix_ending = "/" + group_id + "/" + date_stamp + "/"

    url = current_app.config['MEETBOT_FETCH_PREFIX'] + \
        link_prefix_ending + file_name

    try:
        fetch_result = requests.get(url)
        fetch_soup = BeautifulSoup(fetch_result.text)
        if file_type == "log":
            full_log_links = fetch_soup.findAll('a', text="full logs")
            for a in full_log_links:
                # prefix "full logs" links with correct paths
                full_log_file_name = a['href']
                a['href'] = link_prefix_ending + full_log_file_name
                a['target'] = "_blank"

        body_content = str(fetch_soup.body)
        body_content = body_content.replace("</br>", "")
        return body_content
    except Exception:
        abort(404)


@mote_bp.route('/sresults', methods=['GET'])
@mote_bp.route('/sresults/', methods=['GET'])
def sresults():
    # Display results for a meeting group.
    group_id = request.args.get('group_id', '')
    group_type = request.args.get('type', '')

    friendly_name = get_friendly_name(group_id)

    if (group_id == '') or (group_type == ''):
        return return_error("Invalid group ID or type.")

    if group_type == "team":
        meetings = get_cache_data("mote:team_meetings")
    elif group_type == "channel":
        meetings = get_cache_data("mote:channel_meetings")
    else:
        return return_error("Invalid group type.")

    try:
        groupx_meetings = meetings[group_id]
    except:
        return return_error("Group not found.")

    sorted_dates = list(groupx_meetings.keys())

    try:
        sorted_dates.sort(key=dateutil.parser.parse, reverse=True)
    except:
        return return_error("An error occured while fetching meetings.")

    avail_dates = collections.OrderedDict()

    try:
        for date in sorted_dates:
            parsed_date = dateutil.parser.parse(date)
            month = parsed_date.strftime("%B")
            year = parsed_date.year
            if year not in avail_dates:
                avail_dates[year] = collections.OrderedDict()
            if month not in avail_dates[year]:
                avail_dates[year][month] = []
            avail_dates[year][month].append(date)

        sorted_date_items = avail_dates.items()
        avail_dates = collections.OrderedDict(sorted_date_items)
    except:
        pass

    return render_template('sresults.html',
                           friendly_name=friendly_name,
                           name=group_id,
                           type=group_type,
                           avail_dates=avail_dates,
                           meetbot_location=current_app.config['MEETBOT_PREFIX'],
                           latest_meeting=list(list(avail_dates.items())[
                                               0][1].items())[0][1][0]
                           )


@mote_bp.route('/search_sugg', methods=['GET'])
@mote_bp.route('/search_sugg/', methods=['GET'])
def search_sugg():
    # Find and return the top 20 search results.
    search_term = request.args.get('q', '')
    channel_meetings = get_cache_data("mote:channel_meetings")
    team_meetings = get_cache_data("mote:team_meetings")
    results = []
    res_num = 0
    display_num = 20

    for cmk in channel_meetings:
        if res_num >= display_num:
            break

        if search_term in cmk:
            friendly_name = get_friendly_name(
                cmk) or "A friendly meeting group."

            try:
                dates, latest = util.get_arrow_dates(channel_meetings[cmk])
            except KeyError:
                continue

            if not dates:
                continue

            results.append({
                "id": cmk,
                "name": cmk,
                "type": "channel",
                "description": friendly_name,
                "latest": latest.timestamp,
                "latest_human": latest.humanize(),
            })

            res_num += 1

    for tmk in team_meetings:
        if res_num >= display_num:
            break

        if search_term in tmk:
            friendly_name = get_friendly_name(
                tmk) or "A friendly meeting group."
            try:
                dates, latest = util.get_arrow_dates(team_meetings[tmk])
            except KeyError:
                continue

            results.append({
                "id": tmk,
                "name": tmk,
                "type": "team",
                "description": friendly_name,
                "latest": latest.timestamp,
                "latest_human": latest.humanize(),
            })

            res_num += 1

    # Sort results based on relevance.
    results = list(reversed(sorted(results, key=lambda k: k['latest'])))
    return jsonify(dict(items=results))


@mote_bp.route('/browse', methods=['GET'])
@mote_bp.route('/browse/', methods=['GET'])
def browse():
    browse_nmappings = dict()
    for category_index in current_app.config['CATEGORY_MAPPINGS']:
        for category in current_app.config['CATEGORY_MAPPINGS'][category_index]:
            try:
                browse_nmappings[category] = current_app.config['NAME_MAPPINGS'][category]["friendly-name"]
            except KeyError:
                browse_nmappings[category] = category

    return render_template('browse.html', category_mappings=current_app.config['CATEGORY_MAPPINGS'], browse_nmappings=browse_nmappings)
