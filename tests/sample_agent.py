from langchain.agents import initialize_agent
from langchain_community.tools import GitHubTool, SlackTool, SQLDatabaseTool

llm = None

agent = initialize_agent(
    tools=[GitHubTool, SlackTool, SQLDatabaseTool],
    llm=llm,
    agent_kwargs={
        "system_message": "You are an assistant that summarizes pull requests."
    }
)