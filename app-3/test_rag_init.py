#!/usr/bin/env python3
"""
Test RAG Initialization
Debug the RAG system initialization step by step
"""

import os
from dotenv import load_dotenv
import pandas as pd
from langchain.schema import Document
from langchain.text_splitter import CharacterTextSplitter

# Load environment variables
load_dotenv()

def test_environment_variables():
    """Test if all required environment variables are loaded"""
    print("🔍 Testing Environment Variables...")
    
    required_vars = [
        'AZURE_OPENAI_API_KEY_CHAT',
        'AZURE_OPENAI_ENDPOINT_CHAT', 
        'AZURE_OPENAI_DEPLOYMENT_CHAT',
        'AZURE_OPENAI_API_KEY_EMBED',
        'AZURE_OPENAI_ENDPOINT_EMBED',
        'AZURE_OPENAI_DEPLOYMENT_EMBED',
        'AZURE_SEARCH_ENDPOINT',
        'AZURE_SEARCH_ADMIN_KEY',
        'AZURE_SEARCH_INDEX_NAME'
    ]
    
    all_present = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value[:20]}...")
        else:
            print(f"❌ {var}: MISSING")
            all_present = False
    
    return all_present

def test_csv_loading():
    """Test if the RAG CSV file can be loaded"""
    print("\n🔍 Testing CSV Loading...")
    
    try:
        df = pd.read_csv("rag.csv")
        print(f"✅ CSV loaded successfully")
        print(f"   Columns: {df.columns.tolist()}")
        print(f"   Rows: {len(df)}")
        print(f"   Sample data:")
        print(df.head(2).to_string())
        return True
    except Exception as e:
        print(f"❌ CSV loading failed: {e}")
        return False

def test_document_creation():
    """Test document creation from CSV"""
    print("\n🔍 Testing Document Creation...")
    
    try:
        df = pd.read_csv("rag.csv")
        documents = [
            Document(page_content=f"Topic: {row['ki_topic']}\n{row['ki_text']}")
            for _, row in df.iterrows()
        ]
        print(f"✅ Documents created: {len(documents)}")
        print(f"   Sample document content:")
        print(f"   {documents[0].page_content[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Document creation failed: {e}")
        return False

def test_text_splitting():
    """Test text splitting"""
    print("\n🔍 Testing Text Splitting...")
    
    try:
        df = pd.read_csv("rag.csv")
        documents = [
            Document(page_content=f"Topic: {row['ki_topic']}\n{row['ki_text']}")
            for _, row in df.iterrows()
        ]
        
        splitter = CharacterTextSplitter(chunk_size=800, chunk_overlap=100)
        chunks = splitter.split_documents(documents)
        
        print(f"✅ Text splitting successful")
        print(f"   Original documents: {len(documents)}")
        print(f"   Chunks created: {len(chunks)}")
        print(f"   Sample chunk:")
        print(f"   {chunks[0].page_content[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Text splitting failed: {e}")
        return False

def test_azure_credentials():
    """Test Azure credentials without initializing models"""
    print("\n🔍 Testing Azure Credentials...")
    
    try:
        # Test if we can import the required modules
        from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
        from langchain_community.vectorstores import AzureSearch
        
        print("✅ Azure modules imported successfully")
        
        # Test credential format
        chat_api_key = os.getenv("AZURE_OPENAI_API_KEY_CHAT")
        chat_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT_CHAT")
        chat_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_CHAT")
        
        embed_api_key = os.getenv("AZURE_OPENAI_API_KEY_EMBED")
        embed_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT_EMBED")
        embed_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBED")
        
        azure_search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        azure_search_key = os.getenv("AZURE_SEARCH_ADMIN_KEY")
        azure_index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")
        
        print(f"✅ Chat endpoint: {chat_endpoint}")
        print(f"✅ Embed endpoint: {embed_endpoint}")
        print(f"✅ Search endpoint: {azure_search_endpoint}")
        print(f"✅ Index name: {azure_index_name}")
        
        return True
    except Exception as e:
        print(f"❌ Azure credentials test failed: {e}")
        return False

def test_embedding_model():
    """Test embedding model initialization"""
    print("\n🔍 Testing Embedding Model...")
    
    try:
        from langchain_openai import AzureOpenAIEmbeddings
        
        embed_api_key = os.getenv("AZURE_OPENAI_API_KEY_EMBED")
        embed_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT_EMBED")
        embed_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBED")
        
        embedding_model = AzureOpenAIEmbeddings(
            azure_endpoint=embed_endpoint,
            api_key=embed_api_key,
            deployment=embed_deployment,
            api_version="2025-01-01-preview",
            chunk_size=1000
        )
        
        print("✅ Embedding model initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Embedding model initialization failed: {e}")
        return False

def test_chat_model():
    """Test chat model initialization"""
    print("\n🔍 Testing Chat Model...")
    
    try:
        from langchain_openai import AzureChatOpenAI
        
        chat_api_key = os.getenv("AZURE_OPENAI_API_KEY_CHAT")
        chat_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT_CHAT")
        chat_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_CHAT")
        
        llm = AzureChatOpenAI(
            azure_endpoint=chat_endpoint,
            api_key=chat_api_key,
            deployment_name=chat_deployment,
            api_version="2025-01-01-preview",
            temperature=0
        )
        
        print("✅ Chat model initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Chat model initialization failed: {e}")
        return False

def test_azure_search():
    """Test Azure Search connection"""
    print("\n🔍 Testing Azure Search...")
    
    try:
        from langchain_openai import AzureOpenAIEmbeddings
        from langchain_community.vectorstores import AzureSearch
        
        # Create a simple test document
        test_docs = [Document(page_content="This is a test document for Azure Search.")]
        
        embed_api_key = os.getenv("AZURE_OPENAI_API_KEY_EMBED")
        embed_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT_EMBED")
        embed_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBED")
        
        azure_search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        azure_search_key = os.getenv("AZURE_SEARCH_ADMIN_KEY")
        azure_index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")
        
        embedding_model = AzureOpenAIEmbeddings(
            azure_endpoint=embed_endpoint,
            api_key=embed_api_key,
            deployment=embed_deployment,
            api_version="2025-01-01-preview",
            chunk_size=1000
        )
        
        # Try to create vectorstore
        vectorstore = AzureSearch.from_documents(
            documents=test_docs,
            embedding=embedding_model,
            azure_search_endpoint=azure_search_endpoint,
            azure_search_key=azure_search_key,
            index_name=azure_index_name
        )
        
        print("✅ Azure Search connection successful")
        return True
    except Exception as e:
        print(f"❌ Azure Search connection failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 RAG Initialization Debug Test")
    print("=" * 50)
    
    tests = [
        test_environment_variables,
        test_csv_loading,
        test_document_creation,
        test_text_splitting,
        test_azure_credentials,
        test_embedding_model,
        test_chat_model,
        test_azure_search
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! RAG should work.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main() 