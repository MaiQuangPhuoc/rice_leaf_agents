from loaders import DocumentLoader
from processors import DocumentProcessor
import re
from langchain_core.documents import Document
from vectorstores import VectorStoreManager
from retrievers import VectorStoreRetriever

import sys , os 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".." ,"..")))
from src.clients.embedding import embeddings_qa
from src.configs import env_config
# from src.clients.databases import qdrant


# from langchain.embeddings import HuggingFaceBgeEmbeddings

# 1 loader 

file_path = r"D:\VKU\Nam_3\thuc_tap_doanh_nghiep_he_eSTI\EDUAGENT\src\modules\rag\documents/CTT10_no_link.docx"

loader = DocumentLoader(file_path)
docs = loader.load()

# ----------------------------temp-------------------
# from transformers import AutoTokenizer

# # dùng tokenizer tương ứng với model
# tokenizer = AutoTokenizer.from_pretrained("dangvantuan/vietnamese-embedding")

# for i, doc in enumerate(docs):
#     text = doc.page_content.strip()
#     tokens = tokenizer.encode(text, add_special_tokens=True)
#     print(f"Chunk {i}:")
#     print("  Ký tự:", len(text))
#     print("  Tokens:", len(tokens))
#     print("  Preview:", text[:100].replace("\n", " "), "...")

# vec = embeddings.embed_query("xin chào")
# print("Embedding length:", len(vec))



for doc in docs:
    # print(f"Page content: {doc.page_content}\n-----------------\n")  
    # print("Metadata:", doc.metadata)
    doc.metadata["chapter"] = "nội dung chuẩn chương trình final_version_toan_10"
    doc.metadata["source"] = ""

# ----------------------------temp-------------------




# print("docs:", docs)

# 2 chunking (nối metadata vào page_content)

# raw_text = "\n".join(doc.page_content for doc in docs)
 

# chapter_blocks = re.split(r"(Chương\s+\d+\.?.*)", raw_text)

# documents = []
# for i in range(1, len(chapter_blocks), 2):  # step by 2
#     chapter_title = chapter_blocks[i].strip()
#     chapter_content = chapter_blocks[i + 1]

#     # tiếp tục tách bài trong chương
#     lesson_blocks = re.split(r"(Bài\s+\d+\.?.*)", chapter_content)
#     for j in range(1, len(lesson_blocks), 2):
#         lesson_title = lesson_blocks[j].strip()
#         lesson_content = lesson_blocks[j + 1]

#         doc = Document(
#             page_content=lesson_content.strip(),
#             metadata={
#                 "chapter": chapter_title,
#                 "lesson": lesson_title
#             }
#         )
#         documents.append(doc)

# processor = DocumentProcessor(chunk_size=1024, chunk_overlap=128)
# chunks = processor.split(documents)

# for i, chunk in enumerate(chunks):
#     chapter = chunk.metadata.get("chapter","")
#     lesson = chunk.metadata.get("lesson" , "")
#     chunk.page_content = f"[{chapter} - {lesson}]\n{chunk.page_content}"
#     print(f"Chunk {i+1}:")
#     print(chunk.page_content)

#     # # print("------\nMetadata:", chunk.metadata)
#     print("-" * 100)

# # print("chunk_0", chunks[0])





# 3 embedding + lưu trên cloud của Qdrant 

vector_manager = VectorStoreManager(
    url = env_config.qdrant_url,
    api_key=env_config.qdrant_api_key
)


collection_name = "documents_new"
vector_store = vector_manager.create_vector_store(
    # documents=chunks,
    documents=docs, # chỉ dùng tạm
    embeddings=embeddings_qa,
    collection_name=collection_name
)

# ----------------------------temp-------------------


# client = vector_manager.get_client()

# collection_info = client.get_collection(collection_name="toan10_chunks")
# print("Collection info:", collection_info)

# # Hoặc in số lượng vector đã lưu
# points_count = collection_info.vectors_count
# print(f"Số vector đã lưu: {points_count}")


# query = "hàm số bậc hai"s

# retrieved_docs = vector_store.similarity_search(query, k=3)
# for i, doc in enumerate(retrieved_docs, 1):
#     print(f"\nKết quả {i}:")
#     print(doc.page_content[:300])  # In 300 ký tự đầu tiên

#### end temp

# 4. retreiver 

#4.1 retriever with similarity 
# retriever = VectorStoreRetriever(vector_store=qdrant)

# query = "hàm số lượng giác"
# results = retriever.retrieve(query)
# for i, result in enumerate(results ,1):
#     print(f"\n----documents : {i}-----")
#     print(result.page_content)
#     print("metadata : {result.metadata}")


# 4.2 retriever with as_retriever 

# my_retriever = VectorStoreRetriever(vector_store=qdrant)
# base_retriever  = my_retriever.as_retriever()

# query = "mệnh đề và hàm số bậc hai"
# docs = base_retriever.invoke(query)

# for i,doc in enumerate(docs , 1):
#     print(f"\n----- Documents :{i}-----")
#     print(doc.page_content)
#     print("-" * 40 )


# ----------------------------temp-------------------
