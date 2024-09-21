"""
Insta485 users

URLs include:
/users/<user_url_slug>/
/users/<user_url_slug>/followers/
/users/<user_url_slug>/following/
"""

from pathlib import Path
import sys
import flask
from flask import session, abort

import insta485


@insta485.app.route("/users/<user_url_slug>/")
def show_user(user_url_slug):
    username = user_url_slug
    logname = session.get("logname")
    if logname is None:
        return flask.redirect("/accounts/login/")

    # Connect to database
    connection = insta485.model.get_db()

    # get user
    cur = connection.execute(
        "SELECT * "
        "FROM users "
        "WHERE username == ?",
        (username, )
    )
    user = cur.fetchone()
    if user is None:
        abort(404)

    # Get array of posts
    cur = connection.execute(
        "SELECT * "
        "FROM posts "
        "WHERE owner == ?",
        (username, )
    )
    posts = cur.fetchall()

    # Get following
    cur = connection.execute(
        "SELECT COUNT(*) AS following_count FROM following WHERE username1 == ?",
        (username, )
    )
    following = cur.fetchone()["following_count"]

    # Get followers
    cur = connection.execute(
        "SELECT COUNT(*) AS follower_count FROM following WHERE username2 == ?",
        (username, )
    )
    followers = cur.fetchone()["follower_count"]
    for post in posts:
        post["filename"] = f"/uploads/{post['filename']}"

    is_user = logname == username
    # check if logname is following
    cur = connection.execute(
        "SELECT * FROM following WHERE username1 == ? AND username2 == ?",
        (logname, username)
    )
    is_following = cur.fetchone() is not None

    print(user, file=sys.stderr)
    # Add database info to context
    context = {"username": user["username"], "posts": posts, "fullname": user["fullname"], "total_posts": len(
        posts), "following": following, "followers": followers, "is_user": is_user, "is_following": is_following, "logname": logname}
    return flask.render_template("user.html", **context)


@insta485.app.route("/users/<user_url_slug>/followers/")
def show_followers(user_url_slug):
    username = user_url_slug
    logname = session.get("logname")
    if logname is None:
        return flask.redirect("/accounts/login/")

    # Connect to database
    connection = insta485.model.get_db()
    # Get followers
    cur = connection.execute(
        "SELECT * FROM following WHERE username2 == ?",
        (username, )
    )
    followers = cur.fetchall()
    followers = [follower["username1"] for follower in followers]
    print(followers, file=sys.stderr)
    # Get follower profiles
    cur = connection.execute(
        "SELECT * FROM users WHERE username IN ({seq})".format(
            seq=','.join(['?']*len(followers))),
        followers
    )
    followers = cur.fetchall()
    for follower in followers:
        follower["filename"] = f"/uploads/{follower['filename']}"
        # check if logname is following
        cur = connection.execute(
            "SELECT * FROM following WHERE username1 == ? AND username2 == ?",
            (logname, follower["username"])
        )
        follower["is_following"] = cur.fetchone() is not None
    context = {"followers": followers,
               "logname": logname, "username": username}
    return flask.render_template("followers.html", **context)


@insta485.app.route("/users/<user_url_slug>/following/")
def show_following(user_url_slug):
    username = user_url_slug
    logname = session.get("logname")
    if logname is None:
        return flask.redirect("/accounts/login/")

    # Connect to database
    connection = insta485.model.get_db()
    # Get followers
    cur = connection.execute(
        "SELECT * FROM following WHERE username1 == ?",
        (username, )
    )
    following = cur.fetchall()
    following = [follower["username2"] for follower in following]
    print(following, file=sys.stderr)
    # Get follower profiles
    cur = connection.execute(
        "SELECT * FROM users WHERE username IN ({seq})".format(
            seq=','.join(['?']*len(following))),
        following
    )
    following = cur.fetchall()
    for follower in following:
        follower["filename"] = f"/uploads/{follower['filename']}"
        # check if logname is following
        cur = connection.execute(
            "SELECT * FROM following WHERE username1 == ? AND username2 == ?",
            (logname, follower["username"])
        )
        follower["is_following"] = cur.fetchone() is not None
    context = {"following": following,
               "logname": logname, "username": username}
    return flask.render_template("following.html", **context)
