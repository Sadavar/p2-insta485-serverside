"""Insta485 development configuration."""

import pathlib

# Root of this application, useful if it doesn't occupy an entire domain
APPLICATION_ROOT = "/"

# Secret key for encrypting cookies
SECRET_KEY = b"\xdf\xc0\xacuWQ\x9a\xd4\xb6Z\x82\xc4TE\xd1 \x9d\xaa\x1e\x7f\xb6\xebP\x1a"
SESSION_COOKIE_NAME = "login"

# File Upload to var/uploads/
INSTA485_ROOT = pathlib.Path(__file__).resolve().parent.parent
UPLOAD_FOLDER = INSTA485_ROOT / "var" / "uploads"
ALLOWED_EXTENSIONS = set(["png", "jpg", "jpeg", "gif"])
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

# Database file is var/insta485.sqlite3
DATABASE_FILENAME = INSTA485_ROOT / "var" / "insta485.sqlite3"
