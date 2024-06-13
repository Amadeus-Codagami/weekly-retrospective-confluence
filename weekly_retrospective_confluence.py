from datetime import datetime, date, timedelta
import os

from atlassian import Confluence
from dotenv import dotenv_values


# Authentication constants for local use
ENV = dotenv_values(".env")
USERNAME_LOCAL = ENV.get("KEY_USERNAME", "<No .env username>")
TOKEN_LOCAL = ENV.get("KEY_TOKEN", "<No .env token>")

# Authentication constants for Actions use
USERNAME_ACTIONS = os.environ.get("KEY_USERNAME", "<No Actions username>")
TOKEN_ACTIONS = os.environ.get("KEY_TOKEN", "<No Actions token>")

# Page data for template page
URL_BASE = "https://codagami.atlassian.net/wiki"
SPACE_ID = "COPS"
WR_STR = "Weekly Retrospective"
PAGE_TEMPLATE_TITLE = f"GMA {WR_STR}"


def get_page(title: str) -> tuple[str, dict]:
    """ Returns the page ID and page dictionary of a given page title """
    page_id = confluence.get_page_id(SPACE_ID, title)
    return page_id, confluence.get_page_by_id(page_id, expand="body.storage")


def get_link(page: dict) -> str:
    """ Returns full link of page from given page dict """
    return URL_BASE + page["_links"]["webui"]


# If called by Action, use repo secrets
# Otherwise, use values from local .env file
# Also create version comment that depends on who called the script
if "GITHUB_WORKFLOW" in os.environ:
    username = USERNAME_ACTIONS
    token = TOKEN_ACTIONS
else:
    username = USERNAME_LOCAL
    token = TOKEN_LOCAL

# Connect to Codagami Confluence website with API
confluence = Confluence(
    url=URL_BASE,
    username=username,
    password=token)

# Title of new page = {Date of Next Friday (or today if today is Friday)} Weekly Retrospective
date_today = date.today()
date_next_friday = date_today + timedelta((4 - date_today.weekday()) % 7)
page_new_title = f"{date_next_friday} {WR_STR}"

# Only create if page does not exist yet
if confluence.page_exists(SPACE_ID, page_new_title):
    _, page_exist = get_page(page_new_title)
    print(f"{WR_STR} page with that date already exists at {get_link(page_exist)}, and it may be filled. Halting.")
else:
    # Find template page, then extract HTML contained therein
    page_template_id, page_template = get_page(PAGE_TEMPLATE_TITLE)
    page_template_content = page_template["body"]["storage"]["value"]

    # Create new page with template pasted therein
    time_now = datetime.now()
    try:
        resp = confluence.create_page(SPACE_ID,
                                      page_new_title,
                                      page_template_content,
                                      parent_id=page_template_id)

        print(f"{time_now}: ✅ Succeeded in creating \"{page_new_title}\".\nCheck it out at {get_link(resp)}")
    except:
        print(f"{time_now}: ❌ Failed in creating \"{page_new_title}\", which the script's creator is used to")
