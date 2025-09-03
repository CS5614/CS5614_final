# server/create_vector_store.py

import os
import json
import shutil
from typing import Any, List, Dict
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS


# ========= 可調參數（查詢端也請用同一 embedding 模型） =========
EMBED_MODEL = "text-embedding-3-small"
INDEX_DIR = "faiss_index"
KB_PATH = "knowledge.jsonl"
# ============================================================


# 會被納入 page_content 的方法學／敘述型欄位白名單（存在才會收）
METHOD_KEYS = [
    "how_weights_calculated", "method", "methodology", "calculation",
    "weight_method", "steps", "guidelines", "notes", "why", "explanation"
]

# 其他常見可讀欄位（存在才會收）
BASIC_TEXT_KEYS = [
    "title", "summary", "section", "q", "a", "equation", "interpretation"
]

# 結構化區塊欄位（list/dict 需要展開成文字）
STRUCT_KEYS = [
    "items", "definitions", "entries", "transformations", "explained_variance"
]


def _flatten_weights(w: Any) -> str:
    """將 weights 以人類可讀文字展開，支援 dict / list[dict|str] / 其他."""
    if w is None:
        return ""
    header = "Weights:"
    if isinstance(w, dict):
        lines = [f"{k}: {v}" for k, v in w.items()]
        return f"{header}\n" + "\n".join(lines)
    if isinstance(w, list):
        lines = []
        for x in w:
            if isinstance(x, dict):
                # 常見鍵名：indicator/name/feature + weight/value
                ind = x.get("indicator") or x.get("name") or x.get("feature") or ""
                val = x.get("weight") or x.get("value") or ""
                lines.append(f"{ind}: {val}".strip(": "))
            else:
                lines.append(str(x))
        return f"{header}\n" + "\n".join(lines)
    return f"{header}\n{w}"


def _flatten_definitions(defs: Any) -> List[str]:
    out: List[str] = []
    if isinstance(defs, list):
        for d in defs:
            if isinstance(d, dict):
                name = d.get("name") or d.get("term") or ""
                desc = d.get("desc") or d.get("definition") or ""
                if name or desc:
                    out.append(f"{name}: {desc}".strip(": "))
            else:
                out.append(str(d))
    elif isinstance(defs, dict):
        for k, v in defs.items():
            out.append(f"{k}: {v}")
    elif defs is not None:
        out.append(str(defs))
    return out


def _flatten_items(items: Any) -> List[str]:
    out: List[str] = []
    if isinstance(items, list):
        for it in items:
            if isinstance(it, dict):
                # 常見鍵：name + use/desc/role
                name = it.get("name") or it.get("table") or ""
                desc = it.get("use") or it.get("desc") or it.get("role") or ""
                if name or desc:
                    out.append(f"{name}: {desc}".strip(": "))
            else:
                out.append(str(it))
    elif isinstance(items, dict):
        for k, v in items.items():
            out.append(f"{k}: {v}")
    elif items is not None:
        out.append(str(items))
    return out


def _flatten_explained_variance(ev: Any) -> List[str]:
    if isinstance(ev, dict):
        return ["ExplainedVariance: " + ", ".join(f"{k}={v}" for k, v in ev.items())]
    return []


def process_json_line_to_document(line_data: Dict[str, Any]) -> Document:
    """
    將單一 JSON 行轉換為 LangChain Document。
    重點：
      - 將方法學與 FAQ 等文字確實納入 page_content。
      - weights 支援 dict / list 兩種結構。
    """
    texts: List[str] = []

    # 1) 基本文字欄位
    for k in BASIC_TEXT_KEYS:
        v = line_data.get(k)
        if v:
            texts.append(str(v))

    # 2) 方法學與規則欄位（最關鍵）
    for k in METHOD_KEYS:
        v = line_data.get(k)
        if v:
            texts.append(f"{k}: {v}")

    # 3) 結構化欄位展開
    for k in STRUCT_KEYS:
        v = line_data.get(k)
        if v is None:
            continue
        if k == "definitions":
            texts.extend(_flatten_definitions(v))
        elif k == "explained_variance":
            texts.extend(_flatten_explained_variance(v))
        elif k in ("transformations",):
            # list of strings
            if isinstance(v, list):
                texts.append(f"{k}:\n" + "\n".join(str(x) for x in v))
            else:
                texts.append(f"{k}: {v}")
        else:
            texts.extend(_flatten_items(v))

    # 4) weights 展開（支援 dict/list）
    if "weights" in line_data:
        texts.append(_flatten_weights(line_data.get("weights")))

    # 5) page_content 與 metadata
    page_content = "\n".join(t for t in texts if t)
    metadata = {
        "doc_id": line_data.get("doc_id", "N/A"),
        "type": line_data.get("type", "generic"),
        "section": line_data.get("section", "N/A"),
        "source": line_data.get("source_id", "N/A"),
    }
    return Document(page_content=page_content, metadata=metadata)


def load_and_process_jsonl(file_path: str) -> List[Document]:
    docs: List[Document] = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            data = json.loads(s)
            docs.append(process_json_line_to_document(data))
    return docs


# ---------------- 主程式 ----------------
load_dotenv()
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found in environment variables.")

# 刪除舊索引（保持你的做法）
if os.path.exists(INDEX_DIR):
    print(f"正在刪除舊的索引資料夾: {INDEX_DIR}...")
    shutil.rmtree(INDEX_DIR)
    print("刪除成功。")

# 1) 載入並處理 KB
print(f"正在載入並處理 {KB_PATH}...")
documents = load_and_process_jsonl(KB_PATH)
print(f"成功處理 {len(documents)} 個知識條目。")

# 2) 分割（適度放大，避免把方法學與表拆開）
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,   # ← 原本 512，調大以保留語境
    chunk_overlap=150
)
chunks = text_splitter.split_documents(documents)
print(f"知識條目被分割成 {len(chunks)} 個區塊用於嵌入。")

# 3) 指定一致的 embedding 模型
embeddings = OpenAIEmbeddings(model=EMBED_MODEL)

# 4) 建索引並儲存
print("正在建立並儲存新的向量索引...")
vector_store = FAISS.from_documents(chunks, embeddings)
vector_store.save_local(INDEX_DIR)
print(f"\n✅ 知識庫索引已成功重建並儲存至 '{INDEX_DIR}'。")
print(f"   - 嵌入模型：{EMBED_MODEL}")
print(f"   - chunk_size/overlap：{text_splitter._chunk_size}/{text_splitter._chunk_overlap}")