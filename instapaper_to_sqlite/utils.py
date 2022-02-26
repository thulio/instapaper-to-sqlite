import json
import pathlib
import sys

import click
from pyinstapaper.instapaper import Bookmark, Folder, Instapaper

BOOKMARK_ATTRIBUTES = set(Bookmark.ATTRIBUTES)
FOLDER_ATTRIBUTES = set(Folder.ATTRIBUTES)


def error(message):
    click.secho(message, bold=True, fg="red")
    sys.exit(-1)


def login(auth: pathlib.Path):
    try:
        data = json.loads(pathlib.Path(auth).read_text())
        consumer_id = data["instapaper_consumer_id"]
        consumer_secret = data["instapaper_consumer_secret"]
        login = data["instapaper_email"]
        password = data["instapaper_password"]
    except (KeyError, FileNotFoundError):
        error(
            "Cannot find authentication data, please run `instapaper-to-sqlite auth`!"
        )

    instapaper = Instapaper(consumer_id, consumer_secret)
    instapaper.login(login, password)

    return instapaper
