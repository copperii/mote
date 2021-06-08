# Møte

Møte - Fedora meetbot log wrangler

### About

Møte is an interface to MeetBot logs that allows the Fedora community to search and explore IRC meetings.
More information on meetings can be found [here](https://fedoraproject.org/wiki/Meeting_channel).

møte organises and serves meetings as a drop-in replacement, without needing any modification to the MeetBot plugin itself.

### Using møte

This is new version of Møte featuring:

Flask 2
Python 3
Poetry
Tox

### Basic usage

Setting up environment:
poetry install

Starting up environment:
poetry shell

Starting up program:
python run-mote.py

view at: http://127.0.0.1:5000/

Running tests:
tox
