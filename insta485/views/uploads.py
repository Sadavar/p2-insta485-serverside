"""
Insta485 uploadss

URLs include:
/upload
"""

from pathlib import Path

import flask
from flask import abort, request

import insta485

uploads_path = Path.cwd().parent.parent / "sql" / "uploads"


@insta485.app.route("/uploads/")
def get_upload():
    filename = request.args.get("filename")
    if filename is None:
        abort(404)
    return flask.send_from_directory(uploads_path, filename)
