import logging
import re
from typing import Any, Dict, List, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

# Configuration constants
DEFAULT_CHUNK_SIZE = 1024
DEFAULT_CHUNK_OVERLAP = 128
DEFAULT_SEPARATORS = ["Bài"]

class DocumentProcessor:
    """
    Document processor using recursive character-based splitting.

    This class wraps LangChain's RecursiveCharacterTextSplitter to provide
    consistent document chunking for the RAG pipeline. It splits documents
    based on a hierarchy of separators while maintaining specified chunk
    sizes and overlaps.

    Attributes:
        splitter (RecursiveCharacterTextSplitter): The underlying text splitter
        chunk_size (int): Maximum size of each chunk
        chunk_overlap (int): Overlap between chunks
    """

    def __init__(
        self,
        separators: Optional[List[str]] = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> None:
        """
        Initialize the document processor.

        Args:
            separators: List of separators in order of preference.
                       Defaults to DEFAULT_SEPARATORS
            chunk_size: Maximum size of each chunk in characters.
                       Must be positive. Defaults to 1024
            chunk_overlap: Number of characters to overlap between chunks.
                          Must be non-negative and less than chunk_size.
                          Defaults to 128

        Raises:
            ValueError: If parameters are invalid
        """
        self._validate_parameters(chunk_size, chunk_overlap)
        
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        self.splitter = RecursiveCharacterTextSplitter(
            separators=separators or DEFAULT_SEPARATORS,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        
        logger.info(f"DocumentProcessor initialized with chunk_size={chunk_size}, "
                   f"chunk_overlap={chunk_overlap}")

    def _validate_parameters(self, chunk_size: int, chunk_overlap: int) -> None:
        """Validate initialization parameters."""
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be non-negative")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize text content.
        
        Handles encoding issues, normalizes whitespace, and removes unwanted characters.
        
        Args:
            text: Input text to clean
            
        Returns:
            Cleaned and normalized text
        """
        if not isinstance(text, str):
            text = str(text) if text is not None else ""
        
        if not text.strip():
            return ""
        
        try:
            # Handle encoding issues
            text = text.encode("utf-8", errors="ignore").decode("utf-8")
            
            # Remove control characters
            text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x84\x86-\x9f]', ' ', text)
            
            # Normalize whitespace
            text = re.sub(r"[\r\n\t]+", " ", text)
            text = re.sub(r"\s+", " ", text)
            text = text.strip()
            
            return text
            
        except Exception as e:
            logger.warning(f"Error cleaning text: {str(e)}")
            return str(text).strip() if text else ""
        
    @staticmethod
    def normalize_metadata(metadata: Dict[str, Any]) -> Dict[str, str]:
        """
        Normalize metadata to ensure all values are strings.

        Args:
            metadata: Dictionary with mixed-type values

        Returns:
            Dictionary with all values converted to strings
        """
        if not isinstance(metadata, dict):
            logger.warning("Invalid metadata type, returning empty dict")
            return {}
            
        normalized = {}

        for key, value in metadata.items():
            try:
                if isinstance(value, (str, int, float, bool)):
                    normalized[key] = str(value)
                elif isinstance(value, list):
                    normalized[key] = ",".join(map(str, value))
                elif isinstance(value, dict):
                    normalized[key] = str(value)
                elif value is not None:
                    normalized[key] = str(value)
            except Exception as e:
                logger.warning(f"Error normalizing metadata key '{key}': {str(e)}")
                continue

        logger.debug(f"Normalized metadata: {len(metadata)} -> {len(normalized)} fields")
        return normalized
    
    def split(self, documents: List[Document]) -> List[Document]:
        """
        Split a list of documents into smaller chunks.

        Args:
            documents: List of Document objects to split

        Returns:
            List of Document objects representing the chunks

        Raises:
            ValueError: If documents list is None
            Exception: If splitting fails
        """
        if documents is None: # khong có doc 
            raise ValueError("Documents list cannot be None")
        
        if not documents: # khong có gì trong doc , tức có doc nhưng doc null 
            logger.info("No documents to split")
            return []
        
        try:
            cleaned_documents = self._clean_documents(documents)
            
            if not cleaned_documents: # khong có gì trong cleaned_docuent
                logger.warning("No valid content found after cleaning documents")
                return []
            
            chunks = self.splitter.split_documents(cleaned_documents)
            logger.info(f"Split {len(documents)} documents into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Error when splitting documents: {str(e)}")
            raise

    def _clean_documents(self, documents: List[Document]) -> List[Document]:
        """Clean document content before splitting."""
        cleaned_documents = []
        
        for doc in documents:
            if not doc.page_content:
                continue
                
            cleaned_content = self.clean_text(doc.page_content)
            if cleaned_content:
                normalized_metadata = self.normalize_metadata(doc.metadata or {})
                cleaned_doc = Document(
                    page_content=cleaned_content,
                    metadata=normalized_metadata
                )
                cleaned_documents.append(cleaned_doc)
        
        return cleaned_documents
