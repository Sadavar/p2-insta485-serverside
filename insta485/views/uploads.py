"""
Insta485 uploadss

URLs include:
/upload
"""

from pathlib import Path
import sys

from flask import Flask, request, abort, send_from_directory, session

import insta485


@insta485.app.route("/uploads/<filename>")
def get_upload(filename):
    logname = session.get("logname")
    if logname is None:
        abort(403)

    if not filename:
        abort(404)

    return send_from_directory(insta485.app.config["UPLOAD_FOLDER"], filename)
