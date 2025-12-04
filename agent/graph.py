from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from agent.states import AgentState
from agent.nodes import call_model, tools

# Define the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))

# Define edges
workflow.set_entry_point("agent")

# Conditional edge:
# If agent decides to call a tool -> "tools" node
# If agent decides to stop/respond -> END
workflow.add_conditional_edges(
    "agent",
    tools_condition,
)

# If tool is called, go back to agent to interpret result
workflow.add_edge("tools", "agent")

# Compile
agent = workflow.compile()
