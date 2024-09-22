"""
Insta485 Index (Main) View.

This module handles the main index view of the application,
displaying posts from the logged-in user and those they follow.

URLs include:
    /
"""

import flask
from flask import session, redirect

import arrow

import insta485

from insta485.utils import get_db_connection


@insta485.app.route("/")
def show_index():
    """
    Display the main index page.

    This function retrieves all posts from the logged-in user and
    the users they follow, sorts them by creation time, and adds
    additional information such as comments, likes, and human-readable
    timestamps.

    Returns:
        Flask Response: The rendered index page
        or a redirect to login if not logged in.
    """
    logname = session.get("logname")
    if logname is None:
        return redirect("/accounts/login/")
    connection = get_db_connection()

    # get all posts from logged in user
    # and all other users that logged in user follows
    cur = connection.execute(
        "SELECT * "
        "FROM posts "
        "WHERE owner = ? "
        "OR owner IN (SELECT username2 FROM following WHERE username1 = ?)",
        (logname, logname)
    )
    posts = cur.fetchall()

    # most recent post at the top, break tie with post id
    posts = sorted(posts, key=lambda x: (
        x["created"], x["postid"]), reverse=True)

    # give human readable times
    for post in posts:
        post["created_human"] = arrow.get(post["created"]).humanize()

    # get comments for each post
    for post in posts:
        cur = connection.execute(
            "SELECT * "
            "FROM comments "
            "WHERE postid = ?",
            (post["postid"], )
        )
        post["comments"] = cur.fetchall()
        for comment in post["comments"]:
            comment["created_human"] = arrow.get(comment["created"]).humanize()

        # Fetch likes for the post
        cur = connection.execute(
            "SELECT COUNT(*) AS like_count FROM likes WHERE postid = ?",
            (post["postid"],)
        )
        post["likes"] = cur.fetchone()["like_count"]

        # Fetch like status for the post
        cur = connection.execute(
            "SELECT * FROM likes WHERE postid = ? AND owner = ?",
            (post["postid"], logname)
        )
        owner_liked = cur.fetchone()
        post["owner_liked"] = owner_liked

        # get img urls for post
        post["url"] = f"/uploads/{post['filename']}"

        # get post owner img url
        cur = connection.execute(
            "SELECT * "
            "FROM users "
            "WHERE username = ?",
            (post["owner"], )
        )
        owner = cur.fetchone()
        post["owner_img_url"] = f"/uploads/{owner['filename']}"

        # oldest comment at the top, break tie with comment id
        post["comments"] = sorted(
            post["comments"], key=lambda x: (x["created"], x["commentid"]))

    # Add database info to context
    context = {"posts": posts, "logname": logname}
    return flask.render_template("index.html", **context)
