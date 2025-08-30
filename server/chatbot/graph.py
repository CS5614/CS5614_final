import os
import re
from typing import TypedDict, Annotated

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langgraph.graph import StateGraph, END

from .prompts import create_sql_prompt
from ..utils.chatbot_db import get_db_connection
from ..config.general_config import settings

# Set up database connection using singleton
db = get_db_connection()
execute_query_tool = QuerySQLDataBaseTool(db=db)

# Set up LLM agent
agent = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    api_key=settings.OPENAI_API_KEY
)


class GraphState(TypedDict):
    messages: Annotated[list[BaseMessage], lambda x, y: x + y]


def sql_generation_node(state: GraphState):
    """Generates the SQL query based on the user's question."""
    print("--- NODE: sql_generation_node ---")
    prompt = create_sql_prompt(db)

    sql_chain = prompt | agent
    response = sql_chain.invoke({"messages": state["messages"]})
    return {"messages": [response]}


def sql_execution_node(state: GraphState):
    """Executes the generated SQL query against the database."""
    print("--- NODE: sql_execution_node ---")
    ai_message = state["messages"][-1]
    ai_message_content = ai_message.content

    # --- 使用正規表達式提取 SQL ---
    match = re.search(r"```sql\s*(.*?)\s*```|SQLQuery:\s*(.*)", ai_message_content, re.DOTALL | re.IGNORECASE)

    if match:
        sql_query = match.group(1) or match.group(2)
        sql_query = sql_query.strip() if sql_query else ""
    else:
        # 如果正規表達式沒匹配到，就直接使用訊息內容 (作為備用方案)
        sql_query = ai_message_content.strip()

    if not sql_query:
        error_message = "Could not extract a valid SQL query from the previous step."
        return {"messages": [HumanMessage(content=error_message, name="tool")]}

    try:
        result = execute_query_tool.invoke(sql_query)
        return {"messages": [HumanMessage(content=str(result), name="tool")]}

    except Exception as e:
        error_message = f"Error executing SQL: {e}\nThe SQL query was: {sql_query}"
        return {"messages": [HumanMessage(content=error_message, name="tool")]}


def final_response_node(state: GraphState):
    """Generates the final natural language response for the user."""
    print("--- NODE: final_response_node ---")
    response_prompt_template = """You are a helpful AI assistant. Your task is to answer the user's original question based on the provided SQL query result.

User's original question was: {question}

The result of the SQL query is:
{sql_result}

**Your Instructions:**
1.  Synthesize a clear, friendly, and concise answer in **English**.
2.  If the SQL result contains an error or is empty, simply respond in **English** that you couldn't find the information (e.g., "Sorry, I couldn't find the information you were looking for.").
3.  Do not mention SQL or the database in your final answer.
4.  **Crucially, you MUST format your entire response using Markdown.** Use headings, bold text, and lists to make the information clear and readable.

**Output Format Example:**

If the result is `[('Great Apartment', 95.5), ('Sunny Loft', 92.1)]`, your response should be:

```markdown
Top Rental Units
Here are the top rental units I found based on your request:
Great Apartment: Score of 95.5
Sunny Loft: Score of 92.1
```

"""
    response_prompt = ChatPromptTemplate.from_template(response_prompt_template)

    final_chain = response_prompt | agent.with_config({"temperature": 0.1})

    original_question = next(
        (msg.content for msg in state["messages"] if isinstance(msg, HumanMessage) and msg.name != "tool"),
        "No original question found"  # 備用訊息，以防萬一
    )

    sql_result = state["messages"][-1].content

    response = final_chain.invoke({"question": original_question, "sql_result": sql_result})
    return {"messages": [response]}


# 3. DEFINE CONDITIONAL LOGIC
def should_execute_sql(state: GraphState):
    """Decides whether to execute SQL or end the process."""
    latest_message = state["messages"][-1]
    if "SQLQuery:" in latest_message.content:
        print("--- DECISION: SQL query found, proceeding to execution. ---")
        return "execute_sql"
    else:
        print("--- DECISION: No SQL query found, ending process. ---")
        return END


# 4. BUILD THE GRAPH
def build_graph():
    """Builds and compiles the LangGraph agent."""
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("generate_sql", sql_generation_node)
    workflow.add_node("execute_sql", sql_execution_node)
    workflow.add_node("final_response", final_response_node)

    # Set the entry point
    workflow.set_entry_point("generate_sql")

    # Add conditional edges
    workflow.add_conditional_edges(
        "generate_sql",
        should_execute_sql,
        {
            "execute_sql": "execute_sql",
            END: END,
        },
    )

    # Add normal edges
    workflow.add_edge("execute_sql", "final_response")
    workflow.add_edge("final_response", END)

    # Compile the graph
    return workflow.compile()


# Create the final runnable app instance
app_graph = build_graph()