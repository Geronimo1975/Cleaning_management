"""
Chatbot service for document support with LangChain RAG implementation.
"""
import os
import json
import tempfile
from openai import OpenAI
from django.conf import settings
from .rag import get_rag_response, get_related_documents, create_or_load_vector_store

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def extract_document_content(document):
    """
    Extract content from a document based on its file type.
    Currently supports basic text extraction.
    """
    try:
        content = ""
        if document.file.name.endswith('.txt'):
            with open(document.file.path, 'r', encoding='utf-8') as f:
                content = f.read()
        elif document.file.name.endswith('.pdf'):
            from pypdf import PdfReader
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(document.file.read())
                temp_path = temp_file.name
            
            reader = PdfReader(temp_path)
            content = ""
            for page in reader.pages:
                content += page.extract_text() + "\n"
            
            # Clean up temporary file
            os.unlink(temp_path)
        
        # For demo purposes, return document description if we can't extract content
        if not content:
            content = f"Title: {document.title}\nDescription: {document.description}"
            if document.tags:
                content += f"\nTags: {', '.join(document.tags)}"
        return content
    except Exception as e:
        print(f"Error extracting content from document {document.id}: {e}")
        return f"Title: {document.title}\nDescription: {document.description}"

def get_chatbot_response(query, documents=None, conversation_history=None):
    """
    Get a response from the chatbot based on the query and relevant documents
    using LangChain RAG.
    
    Args:
        query (str): The user's question
        documents (list): List of Document objects relevant to the query
        conversation_history (list): Previous messages in the conversation
    
    Returns:
        str: The chatbot's response
    """
    try:
        # Convert conversation history to the format expected by get_rag_response
        formatted_history = []
        if conversation_history:
            for msg in conversation_history:
                formatted_history.append({
                    "message": msg.message,
                    "is_bot": msg.is_bot
                })
        
        # Get document IDs if documents are provided
        document_ids = []
        if documents:
            document_ids = [doc.id for doc in documents]
        
        # Get response from RAG system
        response_data = get_rag_response(
            question=query,
            document_ids=document_ids,
            conversation_history=formatted_history
        )
        
        # Extract answer and sources
        answer = response_data.get("answer", "I'm sorry, I couldn't generate a response.")
        sources = response_data.get("sources", [])
        
        # If sources were found, append them to the response
        if sources:
            source_list = "\n\nSources:"
            for i, source in enumerate(sources, 1):
                source_list += f"\n{i}. {source.get('title', 'Unknown')} (Document #{source.get('id', 'N/A')})"
            
            answer += source_list
        
        return answer
    
    except Exception as e:
        print(f"Error getting chatbot response: {e}")
        
        # Fallback to standard method without RAG
        try:
            system_content = (
                "You are a helpful assistant for a cleaning services platform. "
                "Your goal is to help users understand cleaning procedures, safety guidelines, "
                "and other documentation related to cleaning services."
            )
            
            # Add document context if available
            if documents:
                context = "Here are some relevant documents:\n\n"
                for i, doc in enumerate(documents, 1):
                    context += f"Document {i}: {doc.title} (Type: {doc.get_document_type_display()})\n"
                system_content += "\n\n" + context
            
            # Prepare messages including conversation history
            messages = [{"role": "system", "content": system_content}]
            
            # Add conversation history if provided
            if conversation_history:
                for msg in conversation_history:
                    role = "assistant" if msg.is_bot else "user"
                    messages.append({"role": role, "content": msg.message})
            
            # Add the current query
            messages.append({"role": "user", "content": query})
            
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=1000,
                temperature=0.7,
            )
            
            return response.choices[0].message.content
        except Exception as fallback_error:
            print(f"Fallback error: {fallback_error}")
            return "I'm sorry, I encountered an error while processing your request. Please try again later."

def search_documents_for_query(query, document_queryset):
    """
    Search for documents relevant to the user query using vector similarity search.
    
    Args:
        query (str): The user's question
        document_queryset: The base queryset of documents the user has access to
    
    Returns:
        list: List of relevant Document objects
    """
    try:
        # First try to get related documents using our RAG-based search
        all_document_ids = list(document_queryset.values_list('id', flat=True))
        
        # If we have no documents, return empty list
        if not all_document_ids:
            return []
        
        # Create a vector store with all accessible documents
        vector_store = create_or_load_vector_store(all_document_ids)
        
        if vector_store:
            # Use vector similarity search
            retriever = vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 3}  # Get top 3 results
            )
            retrieval_results = retriever.invoke(query)
            
            # Extract document IDs from metadata
            result_ids = []
            for doc in retrieval_results:
                if doc.metadata and "source" in doc.metadata:
                    source_id = doc.metadata["source"]
                    if source_id.startswith("document_"):
                        doc_id = int(source_id.replace("document_", ""))
                        result_ids.append(doc_id)
            
            # Get Document objects for these IDs
            if result_ids:
                return document_queryset.filter(id__in=result_ids)
    
    except Exception as e:
        print(f"Vector search error: {e}")
    
    # Fallback to traditional search if vector search fails
    from django.db.models import Q
    
    # Extract key terms from the query (this is a simple approach)
    terms = [term.strip().lower() for term in query.split() if len(term.strip()) > 3]
    
    # Build Q objects for searching
    q_objects = Q()
    for term in terms:
        q_objects |= Q(title__icontains=term)
        q_objects |= Q(description__icontains=term)
        q_objects |= Q(tags__contains=[term])
    
    # Return filtered queryset, limited to top 3 most relevant
    return document_queryset.filter(q_objects).distinct()[:3]