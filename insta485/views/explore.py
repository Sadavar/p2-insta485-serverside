"""
Insta485 index (main) view.

URLs include:
/
"""

import flask
from flask import session, redirect

import insta485

from insta485.utils import get_db_connection


@insta485.app.route("/explore/")
def show_explore():
    """Display /explore/ route."""
    # Connect to database
    logname = session.get("logname")
    if logname is None:
        return redirect("/accounts/login/")
    connection = get_db_connection()

    # Get users not followed by the logged-in user
    cur = connection.execute(
        """
        SELECT username, fullname, filename AS user_img_url
        FROM users
        WHERE username != ? AND username NOT IN
        (SELECT username2 FROM following WHERE username1 = ?)
        """,
        (logname, logname)
    )
    not_following = cur.fetchall()

    print(not_following)

    # Add image URLs to not_following
    for follower in not_following:
        follower["url"] = f"/uploads/{follower['user_img_url']}"

    context = {
        "logname": logname,
        "not_following": not_following,
    }

    return flask.render_template("explore.html", **context)
