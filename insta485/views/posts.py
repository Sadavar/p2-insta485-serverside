"""
Insta485 index (main) view.

URLs include:
/
"""

import flask

import insta485


@insta485.app.route("/posts/")
def show_index():
    """Display /posts/<post> route."""

    # Connect to database
    connection = insta485.model.get_db()

    # Query database
    logname = "awdeorio"
    cur = connection.execute(
        "SELECT username, fullname "
        "FROM users "
        "WHERE username != ?",
        (logname,)
    )
    users = cur.fetchall()

    cur = connection.execute(
        "SELECT * "
        "FROM posts "
        "WHERE owner != ?",
        (logname, )
    )
    posts = cur.fetchall()

    # Add database info to context
    context = {"post": post}
    return flask.render_template("post.html", **context)
