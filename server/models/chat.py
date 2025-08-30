from pydantic import BaseModel

# 定義前端請求的資料格式，與 Chatbot.tsx 中的 body 匹配
class ChatRequest(BaseModel):
    question: str

# 定義回傳給前端的回應格式，與 Chatbot.tsx 中的 data.answer 匹配
class ChatResponse(BaseModel):
    answer: str