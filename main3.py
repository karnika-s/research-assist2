# works completely fine 

from datetime import datetime
import streamlit as st
import os
from langchain_groq import ChatGroq
# from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFDirectoryLoader
import time

# import openai

from dotenv import load_dotenv
load_dotenv()     #load all env variables
#load the GROQ API Key

# os.environ['OPENAI_API_KEY']=os.getenv("OPENAI_API_KEY")
os.environ['GROQ_API_KEY']=os.getenv("GROQ_API_KEY")
groq_api_key=os.getenv("GROQ_API_KEY")


## If you do not have open AI key use the below Huggingface embedding
os.environ['HF_TOKEN']=os.getenv("HF_TOKEN")
from langchain_huggingface import HuggingFaceEmbeddings
embeddings=HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


# creating llm model 
llm=ChatGroq(groq_api_key=groq_api_key,model_name="Llama3-8b-8192")

prompt=ChatPromptTemplate.from_template(
    """
    Answer the questions based on the provided context only.
    Please provide the most accurate respone based on the question from the research_papers
    <context>
    {context}
    <context>
    Question:{input}

    """

)

# main aim is to be able to read the docs and then answert from there 
# session state helps to remeber vector store db 
def create_vector_embedding():
    if "vectors" not in st.session_state:
        st.session_state.embeddings=HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        st.session_state.loader=PyPDFDirectoryLoader("research_papers") ## Data Ingestion step
        st.session_state.docs=st.session_state.loader.load() ## Document Loading
        st.session_state.text_splitter=RecursiveCharacterTextSplitter(chunk_size=1000,chunk_overlap=200)
        st.session_state.final_documents=st.session_state.text_splitter.split_documents(st.session_state.docs[:50])
        st.session_state.vectors=FAISS.from_documents(st.session_state.final_documents,st.session_state.embeddings)


# Initialize chat history in session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


st.title("RAG Document Q&A With Groq And Lama3")


user_prompt=st.text_input("Enter your query from the research paper")

if st.button("Document Embedding"):
    create_vector_embedding()
    st.write("Vector Database is ready")

# what happens after the user give a promt 
if user_prompt:
    timestamp1 = datetime.now().strftime("%d-%m-%Y")
    timestamp2= datetime.now().strftime("%H:%M:%S")   # Get the current timestamp
    document_chain=create_stuff_documents_chain(llm,prompt)   #passing the list
    retriever=st.session_state.vectors.as_retriever()    #acta as an interface to pas the queries

    retrieval_chain=create_retrieval_chain(retriever,document_chain)

    start_time=time.process_time()
    response=retrieval_chain.invoke({'input':user_prompt})
    # print(f"Response time :{time.process_time()-start_time}")
    response_time = time.process_time() - start_time


    # Save the interaction to the chat history
    st.session_state.chat_history.append({"user": user_prompt, "bot": response['answer'],  "timestamp2": timestamp2, "timestamp1": timestamp1})


    # Display the bot's response
    st.write(f"Response time: {response_time:.2f} seconds")

    st.write(response['answer'])



       # Display the chat history
    st.write("### Chat History")
    for chat in st.session_state.chat_history:
        st.write(f"**Asked at**: {chat['timestamp2']}, {chat['timestamp1']}")
        st.write(f"**User**: {chat['user']}")
        st.write(f"**Bot**: {chat['bot']}")
        st.write("---")



    # With a streamlit expander
    with st.expander("Document similarity Search"):
        for i,doc in enumerate(response['context']):   #will give all relevant infor from doc to us
            st.write(doc.page_content)
            st.write('------------------------')