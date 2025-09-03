import re
from typing import TypedDict, Annotated, Literal
from pathlib import Path

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers.string import StrOutputParser

from langchain_openai import ChatOpenAI
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

from langgraph.graph import StateGraph, END
from langchain.retrievers.multi_query import MultiQueryRetriever

from .prompts import create_sql_prompt, create_rag_prompt, create_general_prompt
from ..utils.chatbot_db import get_db_connection
from ..config.general_config import settings

# Set up database connection using singleton
db = get_db_connection()
execute_query_tool = QuerySQLDataBaseTool(db=db)

# Set up RAG
embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=settings.OPENAI_API_KEY)
BASE_DIR = Path(__file__).resolve().parent    # .../server/chatbot
INDEX_DIR = BASE_DIR.parent / "faiss_index"   # .../server/faiss_index
vector_store = FAISS.load_local(str(INDEX_DIR), embeddings, allow_dangerous_deserialization=True)

# Set up LLM agent
agent = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    api_key=settings.OPENAI_API_KEY,
)

base_retriever = vector_store.as_retriever(search_kwargs={"k": 7})
retriever = MultiQueryRetriever.from_llm(
    retriever=base_retriever, llm=agent
)
print("Successfully loaded RAG knowledge base with Multi-Query Retriever.")


class GraphState(TypedDict):
    messages: Annotated[list[BaseMessage], lambda x, y: x + y]
    context: str  # Store RAG retrieved content


def general_conversation_node(state: GraphState):
    """Handles general conversation."""
    print("--- NODE: General Conversation ---")
    prompt = create_general_prompt()
    chat_chain = prompt | agent
    response = chat_chain.invoke({"messages": state["messages"]})
    return {"messages": [response]}


def sql_generation_node(state: GraphState):
    """Generates a SQL query."""
    print("--- NODE: SQL Generation ---")
    prompt = create_sql_prompt(db)
    sql_chain = prompt | agent
    response = sql_chain.invoke({"messages": state["messages"]})
    return {"messages": [response]}


def sql_execution_node(state: GraphState):
    """Executes the SQL query."""
    print("--- NODE: SQL Execution ---")
    ai_message = state["messages"][-1]
    match = re.search(r"```sql\s*(.*?)\s*```|SQLQuery:\s*(.*)", ai_message.content, re.DOTALL | re.IGNORECASE)
    sql_query = (match.group(1) or match.group(2) or "").strip() if match else ""

    if not sql_query:
        return {"messages": [HumanMessage(content="Could not extract a valid SQL query from the previous step.", name="tool")]}
    try:
        result = execute_query_tool.invoke(sql_query)
        return {"messages": [HumanMessage(content=str(result), name="tool")]}
    except Exception as e:
        return {"messages": [HumanMessage(content=f"Error executing SQL: {e}", name="tool")]}


def final_response_node(state: GraphState):
    """
    Generates the final natural language response for the user based on the SQL query result.
    """
    print("--- NODE: Final Response (SQL) ---")

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
    ### Top Rental Units
    
    Here are the top rental units I found based on your request:
    
    * **Great Apartment**
    * **Sunny Loft**
    """
    response_prompt = ChatPromptTemplate.from_template(response_prompt_template)

    # Use a slightly higher temperature for more creative/natural language generation
    final_chain = response_prompt | agent.with_config({"temperature": 0.1})

    # Extract the original question from the message history
    original_question = next(
        (msg.content for msg in state["messages"] if isinstance(msg, HumanMessage) and msg.name != "tool"),
        "No original question found"  # Fallback message in case something goes wrong
    )

    # Get the latest message, which is the SQL query result from the tool
    sql_result = state["messages"][-1].content

    response = final_chain.invoke({"question": original_question, "sql_result": sql_result})

    return {"messages": [response]}

def rag_retrieval_node(state: GraphState):
    """Retrieves documents from the knowledge base."""
    print("--- NODE: RAG Retrieval ---")
    last_message = state["messages"][-1].content
    retrieved_docs = retriever.invoke(last_message)

    # --- 在這裡加上偵錯用的 print 迴圈 ---
    print("\n--- DOCUMENTS RETRIEVED ---")
    for i, doc in enumerate(retrieved_docs):
        print(f"--- Document {i+1} ---")
        print(doc.page_content)
        print("-----------------------\n")
    # --- 偵錯程式碼結束 ---

    context_str = "\n\n".join([doc.page_content for doc in retrieved_docs])
    return {"context": context_str}


def rag_generation_node(state: GraphState):
    """Generates a response based on the retrieved content."""
    print("--- NODE: RAG Generation ---")
    prompt = create_rag_prompt()
    rag_chain = prompt | agent
    response = rag_chain.invoke({"question": state["messages"][-1].content, "context": state["context"]})
    return {"messages": [response]}


# ==============================================================================
# 4. Define the Router
# ==============================================================================

def route_question(state: GraphState) -> Literal["sql", "rag", "chat"]:
    """Determines the type of the user's question and decides the next node."""
    print("--- ROUTER: Classifying question ---")
    last_message = state["messages"][-1].content

    router_prompt = f"""Classify the user's question below into one of the following categories: 'sql', 'rag', or 'chat'.
    - 'sql': The question requires querying a database, e.g., about rental listings, scores, etc.
    - 'rag': The question is about specific project formulas, calculations, or definitions, such as 'User Engagement Score' or 'Project Phoenix'.
    - 'chat': The question is a general greeting, small talk, or unrelated to the other two categories.

    Question: "{last_message}"

    Return only the category name.
    """

    router_chain = ChatPromptTemplate.from_template(router_prompt) | agent | StrOutputParser()
    route = router_chain.invoke({}).strip().lower()

    print(f"--- ROUTER decided: {route} ---")
    print(f"Last message was: {last_message}")

    if "sql" in route:
        return "sql"
    if "rag" in route:
        return "rag"
    return "chat"


# ==============================================================================
# 5. Build the Graph
# ==============================================================================

def build_graph():
    """Builds and compiles the LangGraph."""
    workflow = StateGraph(GraphState)

    # Add all nodes
    workflow.add_node("general_conversation", general_conversation_node)
    workflow.add_node("sql_generation", sql_generation_node)
    workflow.add_node("sql_execution", sql_execution_node)
    workflow.add_node("final_sql_response", final_response_node)
    workflow.add_node("rag_retrieval", rag_retrieval_node)
    workflow.add_node("rag_generation", rag_generation_node)

    # Set the entry point to be the router
    workflow.set_conditional_entry_point(
        route_question,
        {
            "sql": "sql_generation",
            "rag": "rag_retrieval",
            "chat": "general_conversation",
        },
    )

    # Define the edges between nodes
    workflow.add_edge("general_conversation", END)
    workflow.add_edge("sql_generation", "sql_execution")
    workflow.add_edge("sql_execution", "final_sql_response")
    workflow.add_edge("final_sql_response", END)
    workflow.add_edge("rag_retrieval", "rag_generation")
    workflow.add_edge("rag_generation", END)

    # Compile the graph
    return workflow.compile()


app_graph = build_graph()