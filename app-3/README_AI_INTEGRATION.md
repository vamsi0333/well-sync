# AI Integration Setup Guide

This application now includes two AI-powered features:

## 1. ATS (Applicant Tracking System) 🤖
- **Route**: `/ai/ats`
- **Function**: Resume processing and matching against job descriptions
- **Features**:
  - Upload multiple PDF resumes
  - Provide job description
  - Get similarity scores using TF-IDF and SBERT
  - Automatic resume filtering and ranking

## 2. RAG (Retrieval-Augmented Generation) 💬
- **Route**: `/ai/rag`
- **Function**: AI assistant trained on Enplify.ai knowledge base
- **Features**:
  - Ask questions about Enplify.ai
  - Get AI-powered responses
  - Context-aware conversations

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Variables (for RAG functionality)
Create a `.env` file in the root directory with the following variables:

```env
# Azure OpenAI Credentials for RAG
AZURE_OPENAI_API_KEY_CHAT=your_chat_api_key_here
AZURE_OPENAI_ENDPOINT_CHAT=your_chat_endpoint_here
AZURE_OPENAI_DEPLOYMENT_CHAT=your_chat_deployment_name_here

AZURE_OPENAI_API_KEY_EMBED=your_embed_api_key_here
AZURE_OPENAI_ENDPOINT_EMBED=your_embed_endpoint_here
AZURE_OPENAI_DEPLOYMENT_EMBED=your_embed_deployment_name_here

# Azure Search Credentials
AZURE_SEARCH_ENDPOINT=your_search_endpoint_here
AZURE_SEARCH_ADMIN_KEY=your_search_admin_key_here
AZURE_SEARCH_INDEX_NAME=your_index_name_here
```

### 3. Required Files
- `rag.csv` - Knowledge base data (already included)
- Azure OpenAI service setup
- Azure Search service setup

### 4. Running the Application
```bash
python app.py
```

The application will run on `http://localhost:5001`

## Features

### ATS System
- **Access**: Navigate to `/ai/ats` or click "🤖 ATS" in the navigation
- **Usage**:
  1. Upload at least 3 PDF resume files
  2. Enter a detailed job description
  3. Set a threshold score (default: 75%)
  4. Get similarity scores and recommendations

### RAG Assistant
- **Access**: Navigate to `/ai/rag` or click "💬 AI Assistant" in the navigation
- **Usage**:
  1. Ask questions about Enplify.ai
  2. Get AI-powered responses
  3. Supports conversation history

## Notes
- The RAG system requires Azure credentials to function
- If Azure credentials are not provided, the RAG system will show an error message
- The ATS system works independently and doesn't require external services
- Both systems are integrated with the existing authentication system

## Troubleshooting
- If you see "RAG system not initialized" errors, check your Azure credentials
- For ATS issues, ensure uploaded files are valid PDFs
- Make sure all dependencies are installed correctly 