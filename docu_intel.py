import os  
import streamlit as st  
from openai import AzureOpenAI  
import fitz  # PyMuPDF  
  
# Set up Azure OpenAI credentials for the general chatbot model  
endpoint = "https://gpt-4omniwithimages.openai.azure.com/"  
deployment = "GPT-40-mini"  
search_endpoint = "https://pptapp8.search.windows.net"  
search_key = "NbobDVlqcVQMj9Ls9L7Ck23KDB7is5RwHQcL2msZ8jAzSeA6HFAN"  
search_index = "new-index-2"  
api_key = "6e98566acaf24997baa39039b6e6d183"  
  
# Set up Azure OpenAI credentials for the Summarizer and Q&A model  
summarizer_endpoint = "https://theswedes.openai.azure.com/openai/deployments/GPT-4-Omni/chat/completions?api-version=2024-02-15-preview"  
summarizer_api_key = "783973291a7c4a74a1120133309860c0"  
  
# Initialize Azure OpenAI client for the general chatbot model  
client = AzureOpenAI(  
    azure_endpoint=endpoint,  
    api_key=api_key,  
    api_version="2024-05-01-preview",  
)  
  
# Initialize Azure OpenAI client for the Summarizer and Q&A model  
summarizer_client = AzureOpenAI(  
    azure_endpoint=summarizer_endpoint,  
    api_key=summarizer_api_key,  
    api_version="2024-02-15-preview",  
)  
  
# Streamlit app interface  
st.title("⛽ GAIL Limited Chatbot")  
st.write(  
    "An advanced enterprise chatbot tailored for GAIL, Ministry of Petroleum and Natural Gas, utilizing Azure AI services. This chatbot streamlines internal processes, enhances communication, and provides instant, accurate responses on HR policies, IT support, company events, and more. "  
    "It is secure, scalable, and designed to boost productivity within the organization."   
)  
  
# Create a session state variable to store the chat messages. This ensures that the  
# messages persist across reruns.  
if "messages" not in st.session_state:  
    st.session_state.messages = []  
  
# Display the existing chat messages via `st.chat_message`.  
for message in st.session_state.messages:  
    with st.chat_message(message["role"]):  
        st.markdown(message["content"])  
  
# Function to handle document uploads and queries  
def handle_document_query(document, query):  
    # Determine the file type and read the content accordingly  
    if document.type == "application/pdf":  
        # Read PDF content  
        pdf_document = fitz.open(stream=document.read(), filetype="pdf")  
        document_content = ""  
        for page_num in range(pdf_document.page_count):  
            page = pdf_document.load_page(page_num)  
            document_content += page.get_text()  
    else:  
        # Try reading the document with different encodings  
        try:  
            document_content = document.read().decode("utf-8")  
        except UnicodeDecodeError:  
            try:  
                document_content = document.read().decode("latin1")  
            except UnicodeDecodeError:  
                st.error("Unable to read the document. Unsupported encoding.")  
                return "Error: Unsupported document encoding."  
  
    # Generate a response using the Summarizer and Q&A model  
    completion = summarizer_client.chat.completions.create(  
        model="GPT-4-Omni",  
        messages=[  
            {"role": "system", "content": "You are an AI assistant that helps summarize and answer questions based on the provided document."},  
            {"role": "user", "content": f"Document content: {document_content}"},  
            {"role": "user", "content": f"Question: {query}"}  
        ],  
        max_tokens=4096,  
        temperature=0,  
        top_p=1,  
        frequency_penalty=0,  
        presence_penalty=0,  
        stop=None,  
        stream=False  
    )  
  
    return completion.choices[0].message.content  
  
# Create a file uploader for document uploads  
uploaded_file = st.file_uploader("Upload a document", type=["pdf", "txt"])  
  
# Create a chat input field to allow the user to enter a message. This will display  
# automatically at the bottom of the page.  
if prompt := st.chat_input("What is up?"):  
    # Store and display the current prompt.  
    st.session_state.messages.append({"role": "user", "content": prompt})  
    with st.chat_message("user"):  
        st.markdown(prompt)  
  
    if uploaded_file:  
        # Handle document-based query  
        response = handle_document_query(uploaded_file, prompt)  
    else:  
        # Generate a response using the general chatbot model  
        completion = client.chat.completions.create(  
            model=deployment,  
            messages=[  
                {"role": m["role"], "content": m["content"]}  
                for m in st.session_state.messages  
            ],  
            max_tokens=800,  
            temperature=0,  
            top_p=1,  
            frequency_penalty=0,  
            presence_penalty=0,  
            stop=None,  
            stream=False,  
            extra_body={  
                "data_sources": [{  
                    "type": "azure_search",  
                    "parameters": {  
                        "endpoint": f"{search_endpoint}",  
                        "index_name": search_index,  
                        "semantic_configuration": "default",  
                        "query_type": "semantic",  
                        "fields_mapping": {},  
                        "in_scope": True,  
                        "role_information": "You are an AI assistant that helps people find information.",  
                        "filter": None,  
                        "strictness": 3,  
                        "top_n_documents": 5,  
                        "authentication": {  
                            "type": "api_key",  
                            "key": f"{search_key}"  
                        }  
                    }  
                }]  
            }  
        )  
        response = completion.choices[0].message.content  
  
    # Stream the response to the chat using `st.write_stream`, then store it in  
    # session state.  
    with st.chat_message("assistant"):  
        st.markdown(response)  
    st.session_state.messages.append({"role": "assistant", "content": response})  
