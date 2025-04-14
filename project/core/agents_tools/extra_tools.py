from datetime import datetime

from agents import function_tool


@function_tool(strict_mode=False)
def retrieve_date():
    date = datetime.now().strftime("%Y-%m-%d")
    return date
