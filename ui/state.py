import sys
sys.dont_write_bytecode = True

import solara

COOKIE_NAME = "entil_session"

# Global app state
current_view = solara.reactive("login") 
current_user = solara.reactive(None)
current_role = solara.reactive("user")
current_session_id = solara.reactive(None)
show_logout_confirm = solara.reactive(False)

# Dashboard state
input_mode = solara.reactive("manual") 
sidebar_open = solara.reactive(True) 
show_help_modal = solara.reactive(False)
rss_link = solara.reactive("")
is_loading = solara.reactive(False)
current_page = solara.reactive(0)
items_per_page = 10
error_message = solara.reactive("")
# UI state for results
display_mode = solara.reactive("summary")  # "summary" or "original"
notes_input = solara.reactive("")
save_status = solara.reactive("")
sidebar_search = solara.reactive("")

# Manual input fields
news_title = solara.reactive("")
news_description = solara.reactive("")

# Data storage
selected_article_data = solara.reactive(None)
rss_feed_results = solara.reactive([]) # Stores the list of titles/dates

# Session check gate
is_checking_session = solara.reactive(True)