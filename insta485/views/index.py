"""
Insta485 index (main) view.

URLs include:
/
"""

import flask
import arrow

import insta485


@insta485.app.route("/")
def show_index():
    """Display / route."""

    # Connect to database
    connection = insta485.model.get_db()

    # Get users
    logname = "awdeorio"

    # get all posts from logged in user, and all other users that logged in user follows
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
        post["url"] = f"/uploads/{post['filename']}/"

        # get post owner img url
        cur = connection.execute(
            "SELECT * "
            "FROM users "
            "WHERE username = ?",
            (post["owner"], )
        )
        owner = cur.fetchone()
        post["owner_img_url"] = f"/uploads/{owner['filename']}/"
        print(f"post img url: {post["owner_img_url"]}")

        # oldest comment at the top, break tie with comment id
        post["comments"] = sorted(
            post["comments"], key=lambda x: (x["created"], x["commentid"]))

    # Add database info to context
    context = {"posts": posts, "logname": logname}
    return flask.render_template("index.html", **context)
