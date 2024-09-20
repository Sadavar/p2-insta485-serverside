"""Views, one for each Insta485 page."""

from insta485.views.index import show_index
from insta485.views.uploads import get_upload
from insta485.views.posts import show_post
from insta485.views.explore import show_explore
from insta485.views.users import show_user, show_followers, show_following
from insta485.views.likes import update_likes
from insta485.views.comments import update_comments
