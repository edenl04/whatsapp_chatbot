from .zoom_tool import ZoomTool  # Use relative import
from langchain_community.tools import TavilySearchResults

zoom_tool = ZoomTool()


all_tools = [zoom_tool, TavilySearchResults(max_results=2)]





