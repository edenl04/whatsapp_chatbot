from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

LLM = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

"""  node names  """
CHECK_IF_NEED_TO_TRANSLATE = "translate conditional"
TRANSLATE_TO_ENG_NODE = "translate to english"
ROUTER_NODE = "router node"
CHECK_IF_USER_HAVE_ADMIN_NODE = "admin conditional node"
REACT_NODE = "react_agent"
ORGANIZE_ANSWER_NODE = "organize response"
FORMAT_PROBLEM_TO_ADMINS = "organize to admins"
ASK_FOR_MORE_INFO_NODE = "ask for more info"
SEND_A_FORM_NOD = "send a form"
TRANSLATE_BACK_CONDITIONAL = "translate back conditional"
TRANSLATE_BACK_NODE = "translate back"
SEND_TO_USER_OR_ADMIN = "send to whatsapp"

ADMIN_GROUP_NAME = "taklot tikshuv"

WHATSAPP_LINK = 'https://web.whatsapp.com/'
CHROME_PATH = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
SELENIUM_PROFILE_PATH = 'C:/Users/eden2/selenium_profile'

TIME_PHRASES_LIST = [
    "today",
    "tomorrow",
    "yesterday",
    "day after tomorrow",
    "day before yesterday",
    "this Monday",
    "this Tuesday",
    "this Wednesday",
    "this Thursday",
    "this Friday",
    "this Saturday",
    "this Sunday",
    "next Monday",
    "next Tuesday",
    "next Wednesday",
    "next Thursday",
    "next Friday",
    "next Saturday",
    "next Sunday",
    "last Monday",
    "last Tuesday",
    "last Wednesday",
    "last Thursday",
    "last Friday",
    "last Saturday",
    "last Sunday",
    "this week",
    "next week",
    "last week",
    "this month",
    "next month",
    "last month",
    "this morning",
    "this afternoon",
    "this evening",
    "tonight",
    "tomorrow morning",
    "tomorrow afternoon",
    "tomorrow evening",
    "in 1 hour",
    "in 2 hours",
    "in 3 hours",
    "in a few minutes",
    "in a couple of hours",
    "in 1 day",
    "in 2 days",
    "in 3 days",
    "by the end of the day",
    "by tomorrow"
]