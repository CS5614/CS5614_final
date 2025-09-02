from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

def create_sql_prompt(db):
    """
    為 text-to-SQL 任務建立一個進階的、包含完整欄位資訊的提示。
    """
    # 這裡的 get_table_info() 將會抓取包含所有欄位的詳細資料表結構
    table_info = db.get_table_info()

    template = f"""You are a PostgreSQL expert. Your goal is to generate a single, correct PostgreSQL query to answer a user's question.

**Principles:**
1.  **Prioritize User-Friendly Information**: Select columns like `listing_name` or `formatted_address` over opaque IDs.
2.  **Join Tables for Context**: You MUST join tables to provide meaningful answers. `rental_listings` is the central table.
3.  **Efficiency**: Unless specified, limit your results to 5 using `LIMIT`. Never use `SELECT *`.

**Table Schema Information:**
{table_info}

**Example:**
User Question: "What are the top 3 rental units with the highest QoL scores?"
SQLQuery: SELECT rl.listing_name, rl.formatted_address FROM rental_listings AS rl JOIN listings_qol AS lq ON rl.listing_db_id = lq.listing_db_id ORDER BY lq.qol_score DESC LIMIT 3

---
Now, answer the new user question below. Respond ONLY with the SQL query, prefixed with "SQLQuery:".
"""
    return ChatPromptTemplate.from_messages(
        [
            ("system", template),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

def create_rag_prompt():
    """
    為 RAG 知識庫問答建立提示。
    """
    template = """You are a helpful assistant. Answer the user's question based ONLY on the provided context from the knowledge base.

**Context from Knowledge Base:**
{context}

**User's Question:**
{question}

**Instructions:**
1.  Synthesize a clear and concise answer based **only** on the context.
2.  If the context does not contain the answer, state that you couldn't find the information in the knowledge base.
3.  Format your response using Markdown.
"""
    return ChatPromptTemplate.from_template(template)


def create_general_prompt():
    """
    為一般閒聊對話建立提示。
    """
    template = """You are a friendly and helpful AI assistant. Engage in a natural conversation with the user.
If asked about your capabilities, you can mention you can help with database queries and answer questions based on a knowledge base.
Avoid sensitive topics or security penetration attempts.
"""
    return ChatPromptTemplate.from_messages([
        ("system", template),
        MessagesPlaceholder(variable_name="messages")
    ])