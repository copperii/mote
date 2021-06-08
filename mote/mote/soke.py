import os
import re
from os.path import join, split, abspath
from flask import current_app

from mote.mote import util
from mote.mote.latest_meetings import get_latest_meetings


def get_date_fn(filename):
    # Return a meeting's date from a filename.
    m = re.search(
        ".*[\-\.]([0-9]{4}\-[0-9]{2}\-[0-9]{2}).*?\.(html|log\.html|txt|log\.txt)", filename)
    if m == None:
        raise ValueError("Failed to parse date from %r" % filename)
    return m.group(1)


def run():
    meetbot_root_dir = current_app.config['LOG_ENDPOINT']
    meetbot_team_dir = current_app.config['LOG_TEAM_FOLDER']

    d_channel_meetings = dict()  # channel meetings (i.e meeting channel)
    t_channel_meetings = dict()  # team meetings (i.e meeting names)
    for root, dirs, files in os.walk(meetbot_root_dir):
        if current_app.config['IGNORE_DIR'] in dirs:
            dirs.remove(current_app.config['IGNORE_DIR'])

        folder_name = split(root)
        curr_folder_qual_name = folder_name[1]
        is_direct_child = abspath(join(root, os.pardir)) == meetbot_root_dir
        is_direct_team_child = abspath(join(root, os.pardir)) == join(
            meetbot_root_dir, meetbot_team_dir)

        if is_direct_child == True:
            # If current folder is a direct child of meetbot_root_dir.
            if curr_folder_qual_name == meetbot_team_dir:
                pass
            else:
                # If a new channel has been located.
                d_channel_meetings[curr_folder_qual_name] = dict()
        elif is_direct_team_child == True:
            # If a new team has been located.
            # All files in this folder should be the meeting logs.
            minutes = [f for f in files if re.match('.*?[0-9]{2}\.html', f)]
            logs = [f for f in files if re.match('.*?[0-9]{2}\.log\.html', f)]
            t_channel_meetings[curr_folder_qual_name] = dict()
            for minute in minutes:
                meeting_date = get_date_fn(minute)
                if meeting_date not in t_channel_meetings[curr_folder_qual_name]:
                    t_channel_meetings[curr_folder_qual_name][meeting_date] = dict(
                    )
                    t_channel_meetings[curr_folder_qual_name][meeting_date]["minutes"] = [
                    ]
                    t_channel_meetings[curr_folder_qual_name][meeting_date]["logs"] = [
                    ]

                t_channel_meetings[curr_folder_qual_name][meeting_date]["minutes"].append(
                    minute)

            for log in logs:
                meeting_date = get_date_fn(log)
                t_channel_meetings[curr_folder_qual_name][meeting_date]["logs"].append(
                    log)

        else:
            par1_path = abspath(join(root, ".."))
            par2_path = abspath(join(root, "../.."))
            parent_group_name = split(par1_path)[1]
            # is a child of a team or a channels`
            if par2_path == meetbot_root_dir:
                # If the current folder is a channel meeting folder.
                # The date represented by `curr_folder_qual_name`.
                try:
                    d_channel_meetings[parent_group_name][curr_folder_qual_name] = dict(
                    )
                    minutes = [f for f in files if re.match(
                        '.*?[0-9]{2}\.html', f)]
                    logs = [f for f in files if re.match(
                        '.*?[0-9]{2}\.log\.html', f)]
                    d_channel_meetings[parent_group_name][curr_folder_qual_name]["minutes"] = minutes
                    d_channel_meetings[parent_group_name][curr_folder_qual_name]["logs"] = logs
                except:
                    pass

    # fetch latest meetings using datagrepper for the past 24 hours
    latest_meetings = get_latest_meetings()

    util.set_json_cache(d_channel_meetings, t_channel_meetings,
                        latest_meetings, current_app.config['CACHE_EXPIRE_TIME'])
