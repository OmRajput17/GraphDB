from typing import Annotated
from typing_extensions import TypedDict


from langchain_community.utilities import ArxivAPIWrapper, WikipediaAPIWrapper
from langchain_community.tools import ArxivQueryRun, WikipediaQueryRun


arxiv_wrapper = ArxivAPIWrapper(top_k_results=1, doc_content_chars_max=300)
arxiv_tool = ArxivQueryRun(arxiv_wrapper)

wikipedia_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=300)
wikipedia_tool = WikipediaQueryRun(wikipedia_wrapper)

from langgraph.graph.message import add_messages

## Langgraph Application
class State(TypedDict):
    messages:Annotated[list, add_messages]


from langgraph.graph import StateGraph, START, END

tools = [arxiv_tool, wikipedia_tool]

graph_builder = StateGraph(State)

import os
from dotenv import load_dotenv

load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")

from langchain_groq import ChatGroq

llm = ChatGroq(api_key=groq_api_key, model_name = "llama-3.1-8b-instant")

llm_with_tools = llm.bind_tools(tools=tools)


def chatbot(state:State):
    return {"messages":[llm_with_tools.invoke(state["messages"])]}

from langgraph.prebuilt import ToolNode, tools_condition

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, chatbot)
tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)


graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition
)

graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge("chatbot", END)

graph = graph_builder.compile()

from IPython.display import Image, display

try:
    display(Image(graph.get_graph().draw_mermaid_png()))
except Exception as e:
    pass


user_input = "What is LORA and QLORA?"

events = graph.stream(
    {"messages":[("user", user_input)]},
    stream_mode="values"
)

for event in events:
    event["messages"][-1].pretty_print()