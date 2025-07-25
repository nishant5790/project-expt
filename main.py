from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.yfinance import YFinanceTools
from dotenv import load_dotenv
load_dotenv()



# agent = Agent(
#     model=Gemini(id="gemini-2.5-flash", search=True),
#     show_tool_calls=True,
#     markdown=True,
# )

# agent.print_response("What's happening in India?")





agent = Agent(
    model=Gemini(id="gemini-2.5-flash"),
    tools=[YFinanceTools(stock_price=True, analyst_recommendations=True, company_info=True, company_news=True)],
    instructions="Use tables to display data.",
    show_tool_calls=True,
    markdown=True,
    # reasoning_model=Gemini(id="gemini-2.5-flash"),

)
agent.print_response("list down 5 stokes in indian market", stream=True)