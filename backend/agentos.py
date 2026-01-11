from agno.os import AgentOS
from agno.os.config import AgentOSConfig, ChatConfig
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.yfinance import YFinanceTools
from agno.tools.reasoning import ReasoningTools
from dotenv import load_dotenv

from agents.basic_agent import (
    create_data_analyst_agent,
    create_creative_agent,
)
from agents.deep_research import create_deep_research_team
from utils import get_db_manager

load_dotenv()

# Database manager for all agents (shared connection)
db_manager = get_db_manager()
db_manager.connect_sync()

data_analyst_agent = create_data_analyst_agent(
    tools=[
        DuckDuckGoTools(),
        YFinanceTools(),
        ReasoningTools(add_instructions=True),
    ],
)
creative_agent = create_creative_agent(
    tools=[
        ReasoningTools(add_instructions=True),
    ],
)

# Deep Research team for comprehensive research
deep_research_team = create_deep_research_team()

# Create AgentOS with all agents and teams
agent_os = AgentOS(
    agents=[data_analyst_agent, creative_agent],
    teams=[deep_research_team],
    config=AgentOSConfig(
        chat=ChatConfig(
            quick_prompts={
                "Data Analyst Agent": ["Generate a chart from data"],
                "Creative Agent": ["Generate an image"],
                "Deep Research Team": [
                    "Research the current state of AI agents in 2025",
                    "Analyze the impact of climate change on agriculture",
                ],
            }
        )
    ),
)
app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve("agentos:app", reload=True)
