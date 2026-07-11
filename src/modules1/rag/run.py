from loaders import DocumentLoader
from processors import DocumentProcessor
import re
from langchain_core.documents import Document
from vectorstores import VectorStoreManager
# from retrievers import VectorStoreRetriever

import sys , os 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".." ,"..")))
from src.clients.embedding import embeddings_qa
from src.configs import env_config
# from src.clients.databases import qdrant


# from langchain.embeddings import HuggingFaceBgeEmbeddings

# 1 loader 

file_path = r"D:\VKU\Nam_4\ky_I\computer_vision\EDUAGENT\src\modules\documents\CTT10_no_link.docx"

loader = DocumentLoader(file_path)
docs = loader.load()



for doc in docs:
    # print(f"Page content: {doc.page_content}\n-----------------\n")  
    # print("Metadata:", doc.metadata)
    doc.metadata["chapter"] = "nội dung chuẩn chương trình final_version_toan_10"
    doc.metadata["source"] = ""


# 2 chunking (nối metadata vào page_content)

raw_text = "\n".join(doc.page_content for doc in docs)
 

chapter_blocks = re.split(r"(Chương\s+\d+\.?.*)", raw_text)

documents = []
for i in range(1, len(chapter_blocks), 2):  # step by 2
    chapter_title = chapter_blocks[i].strip()
    chapter_content = chapter_blocks[i + 1]

    # tiếp tục tách bài trong chương
    lesson_blocks = re.split(r"(Bài\s+\d+\.?.*)", chapter_content)
    for j in range(1, len(lesson_blocks), 2):
        lesson_title = lesson_blocks[j].strip()
        lesson_content = lesson_blocks[j + 1]

        doc = Document(
            page_content=lesson_content.strip(),
            metadata={
                "chapter": chapter_title,
                "lesson": lesson_title
            }
        )
        documents.append(doc)

processor = DocumentProcessor(chunk_size=1024, chunk_overlap=128)
chunks = processor.split(documents)

for i, chunk in enumerate(chunks):
    chapter = chunk.metadata.get("chapter","")
    lesson = chunk.metadata.get("lesson" , "")
    chunk.page_content = f"[{chapter} - {lesson}]\n{chunk.page_content}"
    print(f"Chunk {i+1}:")
    print(chunk.page_content)

    # # print("------\nMetadata:", chunk.metadata)
    print("-" * 100)


# 3 embedding + lưu trên cloud của Qdrant 
vector_manager = VectorStoreManager(
    url = env_config.qdrant_url,
    api_key=env_config.qdrant_api_key
)

collection_name = "documents_knowledge_toan_10"
vector_store = vector_manager.create_vector_store(
    documents=chunks,
    # documents=docs, # chỉ dùng tạm
    embeddings=embeddings_qa,
    collection_name=collection_name
)