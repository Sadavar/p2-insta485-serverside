"""
Insta485 index (main) view.

URLs include:
/
"""

import flask
from flask import session, request, session, abort, redirect
import arrow
import pathlib
from pathlib import Path
import uuid
import os

import insta485


@insta485.app.route("/posts/<postid_url_slug>/")
def show_post(postid_url_slug):
    """Display /posts/<post> route."""

    # Connect to database
    connection = insta485.model.get_db()

    # get post from database
    logname = session.get("logname")
    if logname is None:
        return flask.redirect("/accounts/login/")

    cur = connection.execute(
        "SELECT * "
        "FROM posts "
        "WHERE postid = ? ",
        (postid_url_slug, )
    )
    post = cur.fetchone()
    if post is None:
        return ("", 404)

    # add image urls to post
    post["url"] = f"/uploads/{post['filename']}"

    # get owner of post
    post_owner = post["owner"]
    cur = connection.execute(
        "SELECT * FROM users WHERE username = ?",
        (post_owner, )
    )
    owner = cur.fetchone()

    # add image url to owner
    owner["url"] = f"/uploads/{owner['filename']}"

    # Get likes for the post
    cur = connection.execute(
        "SELECT COUNT(*) AS like_count FROM likes WHERE postid = ?",
        (postid_url_slug, )
    )
    likes = cur.fetchone()["like_count"]

    # Get comments for the post
    cur = connection.execute(
        "SELECT * FROM comments WHERE postid = ?",
        (postid_url_slug, )
    )
    comments = cur.fetchall()

    # Check if owner has liked post
    cur = connection.execute(
        "SELECT * FROM likes WHERE postid = ? AND owner = ?",
        (postid_url_slug, logname)
    )
    owner_liked = cur.fetchone()

    # Convert timestamp of post to human readable format
    post["created"] = arrow.get(post["created"]).humanize()

    # Add all information to context
    context = {
        "post": post,
        "owner": owner,
        "likes": likes,
        "comments": comments,
        "logname": logname,
        "owner_liked": owner_liked
    }
    return flask.render_template("post.html", **context)


@insta485.app.route("/posts/", methods=["POST"])
def update_post():
    operation = request.form["operation"]
    logname = session.get("logname")
    target = request.args.get("target", f"/users/{logname}/")
    if logname is None:
        abort(403)

    connection = insta485.model.get_db()

    if operation == "create":
        fileobj = request.files.get("file")
        # Check if the file is empty
        if not fileobj or fileobj.filename == "":
            abort(400)

        filename = fileobj.filename

        # Generate UUID-based filename
        stem = uuid.uuid4().hex
        suffix = pathlib.Path(filename).suffix.lower()
        uuid_basename = f"{stem}{suffix}"

        # Define the file path
        upload_folder = insta485.app.config["UPLOAD_FOLDER"]
        filepath = pathlib.Path(upload_folder) / uuid_basename

        # Save the file to the uploads directory
        fileobj.save(filepath)

        # Insert the post into the database
        connection.execute(
            "INSERT INTO posts (filename, owner) VALUES (?, ?)",
            (uuid_basename, logname)
        )

        # Redirect to target URL
        return redirect(target)

    # Save file to uploads directory
    elif operation == "delete":
        postid = request.form.get("postid")

        # Fetch the post details
        post = connection.execute(
            "SELECT filename, owner FROM posts WHERE postid = ?",
            (postid,)
        ).fetchone()

        # Check if the post exists and if the user owns the post
        if post is None or post['owner'] != logname:
            abort(403)

        # Delete the image file from the filesystem
        filepath = pathlib.Path(
            insta485.app.config["UPLOAD_FOLDER"]) / post['filename']
        if filepath.exists():
            filepath.unlink()

        # Delete related entries (comments, likes) in the database
        connection.execute("DELETE FROM comments WHERE postid = ?", (postid,))
        connection.execute("DELETE FROM likes WHERE postid = ?", (postid,))
        connection.execute("DELETE FROM posts WHERE postid = ?", (postid,))

        # Redirect to target URL
        return redirect(target)

    # If operation is not recognized, abort
    else:
        abort(400)
