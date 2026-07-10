from langchain_community.document_loaders import (
    PyPDFLoader,
    CSVLoader,
    Docx2txtLoader,
    WebBaseLoader,
    UnstructuredFileLoader,
    UnstructuredMarkdownLoader
)

class DocumentLoader:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def get_loader(self, file_path: str):
        if file_path.endswith(".pdf"):
            return PyPDFLoader(file_path)
        elif file_path.endswith(".csv"):
            return CSVLoader(file_path)
        elif file_path.endswith(".docx"):
            return Docx2txtLoader(file_path)
        elif file_path.endswith(".md") or file_path.endswith(".markdown"):
            return UnstructuredMarkdownLoader(file_path)
        elif file_path.startswith("http"):
            return WebBaseLoader(file_path)
        else:
            return UnstructuredFileLoader(file_path)

    def load(self):
        loader = self.get_loader(self.file_path)
        docs = loader.load()

        if docs:
            print("loaders.py => Đã load file thành công")
        else:
            print("loaders.py => Chưa load được file ???")

        return docs
