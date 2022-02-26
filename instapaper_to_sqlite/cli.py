import json
import pathlib

import click
import sqlite_utils
from instapaper_to_sqlite import utils


@click.group()
@click.version_option()
def cli():
    "Save data from Instapaper to a SQLite database"


@cli.command()
@click.option(
    "-a",
    "--auth",
    type=click.Path(file_okay=True, dir_okay=False, allow_dash=False),
    default="auth.json",
    help="Path to save tokens to, defaults to ./auth.json.",
)
def auth(auth):
    "Save authentication credentials to a JSON file"
    auth_data = {}
    if pathlib.Path(auth).exists():
        auth_data = json.loads(pathlib.Path(auth).read_text())
    click.echo(
        "In Instapaper, get a Full API key following the process at https://www.instapaper.com/api."
    )
    consumer_id = click.prompt("OAuth Consumer ID")
    consumer_secret = click.prompt("OAuth Consumer Secret")
    login = click.prompt("Instapaper login (email)")
    password = click.prompt("Instapaper password", hide_input=True)
    auth_data.update(
        {
            "instapaper_consumer_id": consumer_id,
            "instapaper_consumer_secret": consumer_secret,
            "instapaper_email": login,
            "instapaper_password": password,
        }
    )

    pathlib.Path(auth).write_text(json.dumps(auth_data, indent=4) + "\n")
    click.echo()
    click.echo(
        "Your authentication credentials have been saved to {}. You can now import articles by running:".format(
            auth
        )
    )
    click.echo()
    click.echo("    $ instapaper-to-sqlite bookmarks instapaper.db")


@cli.command()
@click.argument(
    "db_path",
    type=click.Path(file_okay=True, dir_okay=False, allow_dash=False),
    required=True,
)
@click.option(
    "-a",
    "--auth",
    type=click.Path(file_okay=True, dir_okay=False, allow_dash=False),
    default="auth.json",
    help="Path to save tokens to, defaults to auth.json",
)
def folders(db_path, auth):
    """Save a folder of bookmarks"""
    db = sqlite_utils.Database(db_path)

    instapaper = utils.login(auth)

    print("Fetching folders...")

    folders = [
        {key: getattr(entry, key) for key in utils.FOLDER_ATTRIBUTES}
        for entry in instapaper.get_folders()
    ]

    folders.append({"folder_id": "archive", "title": "archive"})
    folders.append({"folder_id": "unread", "title": "unread"})
    folders.append({"folder_id": "starred", "title": "starred"})

    print(f"Downloaded {len(folders)} folders")

    db["folders"].upsert_all(folders, pk="folder_id", alter=True)


@cli.command()
@click.argument(
    "db_path",
    type=click.Path(file_okay=True, dir_okay=False, allow_dash=False),
    required=True,
)
@click.option(
    "-a",
    "--auth",
    type=click.Path(file_okay=True, dir_okay=False, allow_dash=False),
    default="auth.json",
    help="Path to save tokens to, defaults to auth.json",
)
def bookmarks(db_path, auth):
    """Save a folder of bookmarks"""
    db = sqlite_utils.Database(db_path)
    instapaper = utils.login(auth)

    for folder in db["folders"].rows:
        print(f"Fetching bookmarks of folder {folder['title']}...")
        bookmarks = [
            {key: getattr(entry, key) for key in utils.BOOKMARK_ATTRIBUTES}
            for entry in instapaper.get_bookmarks(folder["folder_id"], limit=500)
        ]
        print(
            "Downloaded {} bookmarks from folder '{}'.".format(
                len(bookmarks), folder["title"]
            )
        )

        for bookmark in bookmarks:
            bookmark["folder_id"] = folder["folder_id"]

        db["bookmarks"].upsert_all(bookmarks, pk="bookmark_id", alter=True)

    db["bookmarks"].create_index(columns=["time"], if_not_exists=True)
    db["bookmarks"].add_foreign_key("folder_id", ignore=True)
    db.index_foreign_keys()


if __name__ == "__main__":
    cli()
