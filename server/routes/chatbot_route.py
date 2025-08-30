from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage, AIMessage
from ..chatbot.graph import app_graph
from ..models.chat import ChatRequest, ChatResponse

# init API Router
router = APIRouter(prefix="/api/chatbot", tags=["Chatbot"])


@router.post("/query", response_model=ChatResponse, tags=["Chatbot"])
async def handle_chatbot_query(request: ChatRequest):
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        # LangGraph 的入口需要一個包含 messages 列表的字典
        inputs = {"messages": [HumanMessage(content=request.question)]}

        # 非同步執行 LangGraph 以獲得更佳效能
        final_state = await app_graph.ainvoke(inputs)

        # 增強的狀態檢查：確保 final_state 和 messages 鍵存在
        if not final_state or not final_state.get("messages"):
            print("Chatbot Error: Graph returned an empty or invalid final state.")
            raise HTTPException(status_code=500, detail="Failed to get a valid response from the model.")

        # 提取最後一則訊息作為答案
        final_message = final_state["messages"][-1]
        bot_answer = ""

        # 判斷最後一則訊息的類型
        # - 如果是 AIMessage，代表 graph 完整運行，我們使用其內容。
        # - 如果 graph 因為沒有生成 SQL 而提前終止，最後一則訊息可能是 HumanMessage。
        #   在這種情況下，我們回傳一個通用的提示訊息。
        if isinstance(final_message, AIMessage):
            bot_answer = final_message.content
        else:
            bot_answer = "I'm sorry, I couldn't process that request. Please try rephrasing your question."

        # 確保我們總是有內容可以回傳
        if not bot_answer:
            bot_answer = "I apologize, but I received an empty response. Please try again."

        return ChatResponse(answer=bot_answer)

    except Exception as e:
        # 在伺服器日誌中印出詳細的錯誤，方便除錯
        print(f"Chatbot execution error in router: {e}")
        # 回傳一個通用的 500 錯誤給前端
        raise HTTPException(status_code=500,
                            detail="An internal server error occurred while processing the chat query.")