"""
Utilidades para integración con Google Gemini, Embeddings y ChromaDB
"""

import os
import tempfile
import json
from datetime import datetime
from langchain_community.document_loaders import PyPDFLoader, TextLoader, CSVLoader, UnstructuredWordDocumentLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import JinaEmbeddings
import google.generativeai as genai
import streamlit as st

def initialize_gemini(api_key: str):
    """
    Inicializa la configuración de Google Gemini con la API Key proporcionada
    """
    if not api_key:
        raise ValueError("API Key no proporcionada")
    
    genai.configure(api_key=api_key)
    return True

def inicializar_embeddings():
    api_key = os.getenv("JINA_API_KEY")
    if not api_key:
        raise ValueError("❌ No se encontró la variable de entorno JINA_API_KEY")
    
    return JinaEmbeddings(
        jina_api_key=api_key,
        model_name="jina-embeddings-v2-base-es"
    )

def inicializar_gemini_model(model_name: str = "gemini-2.0-flash"):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("❌ No se encontró la variable de entorno GOOGLE_API_KEY")

    genai.configure(api_key=api_key)

    try:
        model = genai.GenerativeModel(model_name)
        print(f"✅ Modelo {model_name} inicializado correctamente.")
        return model
    except Exception as e:
        raise RuntimeError(f"⚠️ Error al inicializar el modelo {model_name}: {e}")


def inicializar_chroma():
    persist_directory = "D:/DESCARGAS/AI/tarea2/vectorial"

    vector_store = Chroma(
        collection_name="opt-desperdicios",
        embedding_function=inicializar_embeddings(),
        persist_directory=persist_directory
    )
    return vector_store

def procesar_y_guardar_archivos(uploaded_files):
    """
    Procesa archivos cargados en Streamlit, los convierte en embeddings y los almacena en Chroma.
    """
    if not uploaded_files:
        return "⚠️ No se cargaron archivos."

    vector_store = inicializar_chroma()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    for file in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(file.read())
            tmp_path = tmp_file.name

        # Seleccionar loader según el tipo de archivo
        if file.name.endswith(".pdf"):
            loader = PyPDFLoader(tmp_path)
        elif file.name.endswith(".txt"):
            loader = TextLoader(tmp_path)
        elif file.name.endswith(".csv"):
            loader = CSVLoader(tmp_path)
        elif file.name.endswith(".docx"):
            loader = UnstructuredWordDocumentLoader(tmp_path)
        elif file.name.endswith(".xlsx"):
            from langchain_community.document_loaders import UnstructuredExcelLoader
            loader = UnstructuredExcelLoader(tmp_path)
        else:
            os.remove(tmp_path)
            continue

        docs = loader.load()
        chunks = text_splitter.split_documents(docs)

        # Almacenar en la base vectorial
        vector_store.add_documents(chunks)

        os.remove(tmp_path)

    # Guardar los cambios
        vector_store.persist()
    return "✅ Archivos procesados y almacenados correctamente en ChromaDB."


def recuperar_contexto(query: str, k: int = 3) -> str:
    """
    Recupera los fragmentos más relevantes desde la base vectorial
    según una consulta o descripción del problema.
    
    Args:
        query: Texto de la pregunta o tema a consultar.
        k: Número de fragmentos a recuperar (por defecto 3).
    """
    vector_store = inicializar_chroma()
    resultados = vector_store.similarity_search(query, k=k)

    contexto = "\n\n".join([doc.page_content for doc in resultados])
    return contexto
