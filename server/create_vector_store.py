import os
import json
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv


def preprocess_line(line_data: dict) -> Document:
    """
    根據 JSON 物件的類型，智能地組合文本內容並提取元數據。
    返回一個 LangChain Document 物件。
    """
    doc_type = line_data.get("type", "generic")
    content = ""

    if doc_type == "doc_meta":
        content = f"Title: {line_data.get('title', '')}. Summary: {line_data.get('summary', '')}"
    elif doc_type == "concept":
        content = f"Concept: {line_data.get('title', '')}. Formula: {line_data.get('equation', '')}. Explanation: {line_data.get('explanation', '')}"
    elif doc_type == "facts" and "items" in line_data:
        processed_items = []
        for item in line_data["items"]:
            if isinstance(item, dict):
                # Handles cases where items are dictionaries
                processed_items.append(f"{item.get('name', '')}: {item.get('use', '') or item.get('desc', '')}")
            elif isinstance(item, str):
                # Handles cases where items are just strings
                processed_items.append(item)
        items_str = "; ".join(processed_items)
        content = f"Fact Section: {line_data.get('section', '')}. Details: {items_str}"

    elif doc_type == "definitions" and "definitions" in line_data:
        defs_str = "; ".join([f"{d.get('name', '')}: {d.get('desc', '')}" for d in line_data["definitions"]])
        content = f"Definitions for {line_data.get('section', '')}: {defs_str}"
    elif doc_type == "method":
        steps_str = "; ".join(line_data.get("steps", []))
        content = f"Method for {line_data.get('section', '')}: {steps_str}. Justification: {line_data.get('why', '')}"
    elif doc_type == "qa":
        content = f"Question: {line_data.get('q', '')}\nAnswer: {line_data.get('a', '')}"
    elif doc_type == "glossary" and "entries" in line_data:
        entries_str = "; ".join([f"{e.get('term', '')}: {e.get('definition', '')}" for e in line_data["entries"]])
        content = f"Glossary of Key Terms: {entries_str}"
    elif doc_type == "results" and "weights" in line_data:
        weights_str = ", ".join([f"{w['indicator']} ({w['weight']})" for w in line_data.get("weights", [])])
        content = f"Results for QoL Weights: {weights_str}"
    else:
        content = ". ".join(str(v) for k, v in line_data.items() if isinstance(v, (str, list, dict)))

    # 提取元數據
    metadata = {
        "doc_id": line_data.get("doc_id", "N/A"),
        "type": doc_type,
        "section": line_data.get("section", "N/A"),
        "source": line_data.get("source_id", "N/A")
    }

    return Document(page_content=content, metadata=metadata)


def load_and_process_jsonl(file_path: str) -> list[Document]:
    """從 JSONL 檔案讀取、處理並轉換成 Document 物件列表"""
    documents = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                doc = preprocess_line(data)
                documents.append(doc)
    return documents


# 載入環境變數
load_dotenv()


# --- 1. 載入並處理你的 JSONL 文件 ---
file_path = 'knowledge.jsonl'
print(f"正在載入並處理 {file_path}...")
documents = load_and_process_jsonl(file_path)
print(f"成功處理 {len(documents)} 個知識條目。")

# --- 2. 分割文件 ---
print("正在分割文件成適當的區塊...")
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)
chunks = text_splitter.split_documents(documents)
print(f"知識條目被分割成 {len(chunks)} 個區塊用於嵌入。")

# --- 3. 初始化 OpenAI 嵌入模型 ---
embeddings = OpenAIEmbeddings()

# --- 4. 建立 FAISS 向量儲存並存檔 ---
print("正在建立向量索引...")
vector_store = FAISS.from_documents(chunks, embeddings)
vector_store.save_local("faiss_index")

print("\n知識庫建立完成！索引已使用新的 JSONL 結構更新至 'faiss_index' 資料夾。")