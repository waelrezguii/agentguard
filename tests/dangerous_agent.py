from langchain.agents import initialize_agent
from langchain_community.tools import GmailTool, ShellTool, FileSystemTool, RequestsTool

llm = None

agent = initialize_agent(
    tools=[GmailTool, ShellTool, FileSystemTool, RequestsTool],
    llm=llm,
    agent_kwargs={
        "system_message": "You are an email assistant that reads and summarizes incoming emails."
    }
)