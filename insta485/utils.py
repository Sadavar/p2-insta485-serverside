"""
Utility functions for the insta485 application.

Returns the logname of the currently logged-in user
and the database connection.
"""
import insta485


def get_db_connection():
    """
    Retrieve a database connection.

    This function establishes a connection to the database
    using the `insta485.model.get_db` method.

    Returns:
        SQLite connection: The database connection object.
    """
    return insta485.model.get_db()
