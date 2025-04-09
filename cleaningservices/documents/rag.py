import os
import tempfile
from typing import List, Dict, Any, Optional
import json

from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from pypdf import PdfReader

from django.conf import settings
from .models import Document as DocModel

# Initialize OpenAI API
openai_api_key = settings.OPENAI_API_KEY

# Initialize embeddings
embeddings = OpenAIEmbeddings(api_key=openai_api_key)

# The newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
llm = ChatOpenAI(model="gpt-4o", api_key=openai_api_key)

# Text splitter for chunking documents
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
)

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text content from a PDF file."""
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

def create_document_chunks(document_id: int) -> List[Document]:
    """Create document chunks from a document in the database."""
    try:
        doc = DocModel.objects.get(id=document_id)
        
        # Create a temporary file to write the PDF content
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(doc.file.read())
            temp_path = temp_file.name
        
        # Extract text from PDF
        text = extract_text_from_pdf(temp_path)
        
        # Clean up temporary file
        os.unlink(temp_path)
        
        if not text.strip():
            return []
        
        # Create metadata for the document
        metadata = {
            "source": f"document_{doc.id}",
            "title": doc.title,
            "document_type": doc.document_type,
            "category": doc.category.name,
            "created_by": doc.created_by.email,
            "created_at": doc.created_at.isoformat(),
        }
        
        # Split text into chunks
        chunks = text_splitter.split_text(text)
        
        # Create document objects with metadata
        documents = [
            Document(page_content=chunk, metadata=metadata)
            for chunk in chunks
        ]
        
        return documents
    except DocModel.DoesNotExist:
        print(f"Document with ID {document_id} does not exist")
        return []
    except Exception as e:
        print(f"Error creating document chunks: {e}")
        return []

def create_or_load_vector_store(document_ids: List[int], force_reload: bool = False) -> Optional[FAISS]:
    """Create or load FAISS vector store for given documents."""
    try:
        # Create a unique identifier for this combination of documents
        store_id = f"docs_{'_'.join(map(str, sorted(document_ids)))}"
        save_path = os.path.join(settings.MEDIA_ROOT, 'vector_stores', store_id)
        
        # Check if vector store already exists
        if os.path.exists(save_path) and not force_reload:
            try:
                # Load existing vector store
                return FAISS.load_local(save_path, embeddings)
            except Exception as e:
                print(f"Error loading vector store: {e}")
                # Fall back to creating a new one
                pass
        
        # Collect all document chunks
        all_chunks = []
        for doc_id in document_ids:
            chunks = create_document_chunks(doc_id)
            all_chunks.extend(chunks)
        
        if not all_chunks:
            print("No document chunks created")
            return None
        
        # Create vector store
        vector_store = FAISS.from_documents(all_chunks, embeddings)
        
        # Save vector store
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        vector_store.save_local(save_path)
        
        return vector_store
    except Exception as e:
        print(f"Error creating vector store: {e}")
        return None

def get_rag_response(question: str, document_ids: List[int], conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
    """Get a response from the RAG system."""
    try:
        # Create or load vector store
        vector_store = create_or_load_vector_store(document_ids)
        if not vector_store:
            return {
                "answer": "I'm sorry, I couldn't process the documents. Please try again later.",
                "sources": []
            }
        
        # Create retriever
        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}
        )
        
        # Format conversation history for context
        conversation_context = ""
        if conversation_history:
            for message in conversation_history[-3:]:  # Use last 3 messages for context
                role = "Human" if message.get("is_bot") is False else "Assistant"
                conversation_context += f"{role}: {message.get('message', '')}\n"
        
        # Create prompt template
        prompt_template = """You are a helpful assistant for a cleaning services platform.
        
        <context>
        {context}
        </context>
        
        <conversation_history>
        {conversation_history}
        </conversation_history>
        
        Human: {question}
        
        Answer the question based on the context provided. 
        If you don't know the answer, say so. Do not make up information.
        Be helpful, concise, and accurate.
        Use bullet points for lists and keep paragraphs short.
        
        Assistant:"""
        
        prompt = ChatPromptTemplate.from_template(prompt_template)
        
        # Create document chain
        document_chain = create_stuff_documents_chain(
            llm=llm,
            prompt=prompt,
            document_variable_name="context"
        )
        
        # Create retrieval chain
        retrieval_chain = create_retrieval_chain(retriever, document_chain)
        
        # Run the chain
        response = retrieval_chain.invoke({
            "question": question,
            "conversation_history": conversation_context
        })
        
        # Extract sources
        sources = []
        seen_sources = set()
        if "context" in response and response["context"]:
            for doc in response["context"]:
                if doc.metadata and "source" in doc.metadata:
                    source_id = doc.metadata["source"]
                    if source_id not in seen_sources:
                        seen_sources.add(source_id)
                        doc_id = int(source_id.replace("document_", ""))
                        try:
                            doc_obj = DocModel.objects.get(id=doc_id)
                            sources.append({
                                "id": doc_id,
                                "title": doc_obj.title,
                                "category": doc_obj.category.name,
                            })
                        except DocModel.DoesNotExist:
                            continue
        
        return {
            "answer": response["answer"],
            "sources": sources
        }
    except Exception as e:
        print(f"Error in RAG response: {e}")
        return {
            "answer": f"I encountered an error while processing your question. Please try again later.",
            "sources": []
        }

def get_related_documents(query: str, exclude_ids: List[int] = None) -> List[Dict[str, Any]]:
    """Get related documents for a query."""
    try:
        # Get all documents
        all_docs = DocModel.objects.all()
        
        if not all_docs:
            return []
        
        # Extract document information
        doc_infos = []
        for doc in all_docs:
            if exclude_ids and doc.id in exclude_ids:
                continue
                
            doc_infos.append({
                "id": doc.id,
                "title": doc.title,
                "description": doc.description,
                "category": doc.category.name,
                "document_type": doc.get_document_type_display(),
            })
        
        # If we have no documents, return empty list
        if not doc_infos:
            return []
            
        # Create a prompt for the LLM to rank documents
        prompt = PromptTemplate.from_template(
            """Given the query: "{query}"
            
            And the following documents:
            {documents}
            
            Rank the documents by relevance to the query. Return a JSON array of document IDs in order of relevance.
            Only include documents that are actually relevant to the query.
            Return in the following format:
            [id1, id2, id3, ...]
            """
        )
        
        # Format documents for the prompt
        docs_text = "\n\n".join([
            f"ID: {doc['id']}\nTitle: {doc['title']}\nDescription: {doc['description']}\nCategory: {doc['category']}\nType: {doc['document_type']}"
            for doc in doc_infos
        ])
        
        # Get rankings
        chain = prompt | llm | StrOutputParser()
        
        result = chain.invoke({
            "query": query,
            "documents": docs_text
        })
        
        try:
            # Parse the result
            ranked_ids = json.loads(result)
            
            # Filter and sort doc_infos based on ranking
            ranked_docs = []
            for doc_id in ranked_ids:
                for doc in doc_infos:
                    if doc["id"] == doc_id:
                        ranked_docs.append(doc)
                        break
            
            return ranked_docs[:5]  # Return top 5 relevant documents
        except json.JSONDecodeError:
            # Fall back to returning all documents if parsing fails
            return doc_infos[:5]
            
    except Exception as e:
        print(f"Error getting related documents: {e}")
        return []