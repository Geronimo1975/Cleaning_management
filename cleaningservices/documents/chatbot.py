"""
Chatbot service for document support.
"""
import os
import json
from openai import OpenAI
from django.conf import settings

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def extract_document_content(document):
    """
    Extract content from a document based on its file type.
    Currently supports very basic text extraction.
    
    In a production system, this would be expanded to handle various
    file types like PDFs, Word docs, etc. using libraries like PyPDF2,
    python-docx, etc.
    """
    try:
        content = ""
        if document.file.name.endswith('.txt'):
            with open(document.file.path, 'r', encoding='utf-8') as f:
                content = f.read()
        # For demo purposes, return document description if we can't extract content
        if not content:
            content = f"Title: {document.title}\nDescription: {document.description}"
            if document.tags:
                content += f"\nTags: {', '.join(document.tags)}"
        return content
    except Exception as e:
        print(f"Error extracting content from document {document.id}: {e}")
        return f"Title: {document.title}\nDescription: {document.description}"

def generate_document_context(documents):
    """
    Generate context from multiple documents to provide to the chatbot.
    """
    context = "Here are some relevant documents that might help answer your question:\n\n"
    
    for i, doc in enumerate(documents, 1):
        content = extract_document_content(doc)
        context += f"Document {i}: {doc.title}\n"
        context += f"Category: {doc.category.name}\n"
        context += f"Type: {doc.get_document_type_display()}\n"
        context += f"Content: {content[:1000]}...\n\n"  # Limit content length
    
    return context

def get_chatbot_response(query, documents=None, conversation_history=None):
    """
    Get a response from the chatbot based on the query and relevant documents.
    
    Args:
        query (str): The user's question
        documents (list): List of Document objects relevant to the query
        conversation_history (list): Previous messages in the conversation
    
    Returns:
        str: The chatbot's response
    """
    try:
        # Prepare system message with document context if provided
        system_content = (
            "You are a helpful assistant for a cleaning services platform. "
            "Your goal is to help users understand cleaning procedures, safety guidelines, "
            "and other documentation related to cleaning services."
        )
        
        # Add document context if available
        if documents:
            system_content += "\n\n" + generate_document_context(documents)
        
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
    
    except Exception as e:
        print(f"Error getting chatbot response: {e}")
        return "I'm sorry, I encountered an error while processing your request. Please try again later."

def search_documents_for_query(query, document_queryset):
    """
    Search for documents relevant to the user query.
    This is a simple implementation that could be enhanced with vector search or other techniques.
    
    Args:
        query (str): The user's question
        document_queryset: The base queryset of documents the user has access to
    
    Returns:
        list: List of relevant Document objects
    """
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