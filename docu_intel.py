import os  
import streamlit as st  
from openai import AzureOpenAI  
import fitz  # PyMuPDF  
from msal import ConfidentialClientApplication  
  
# Azure App Registration credentials  
client_id = "2849f8da-cd31-4b5c-b605-ad3ad64162aa"  
authority = "https://login.microsoftonline.com/4d4343c6-067a-4794-91f3-5cb10073e5b4"  
redirect_uri = "https://gale-bot-1-wrtxjvw6bhddtufmzvsrgj.streamlit.app/"  
client_secret = "0829698c-4afc-4b8c-89fd-3ea38765608f"  # Updated client secret  
  
# MSAL configuration  
msal_app = ConfidentialClientApplication(  
    client_id,  
    client_credential=client_secret,  
    authority=authority  
)  
  
# Initialize auth_code_flow  
auth_code_flow = None  
  
# Function to get token  
def get_token():  
    result = msal_app.acquire_token_by_auth_code_flow(  
        st.session_state.auth_code_flow, st.experimental_get_query_params()  
    )  
    if "error" in result:  
        st.error(f"Authentication failed: {result['error_description']}")  
        return None  
    return result  
  
# Check if the user is authenticated  
def is_authenticated():  
    token = st.session_state.get("token")  
    return token is not None  
  
# Set up Azure OpenAI credentials for the general chatbot model  
endpoint = "https://gpt-4omniwithimages.openai.azure.com/"  
deployment = "GPT-40-mini"  
search_endpoint = "https://pptapp8.search.windows.net"  
search_key = "NbobDVlqcVQMj9Ls9L7Ck23KDB7is5RwHQcL2msZ8jAzSeA6HFAN"  
search_index = "new-index-4"  
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
  
# Authentication flow  
if "token" not in st.session_state:  
    st.session_state.token = None  
  
if not is_authenticated():  
    if st.button("Login"):  
        st.session_state.auth_code_flow = msal_app.initiate_auth_code_flow(  
            scopes=["User.Read"],  
            redirect_uri=redirect_uri  
        )  
        auth_url = st.session_state.auth_code_flow["auth_uri"]  
        st.write(f"Please authenticate by visiting [this link]({auth_url}).")  
else:  
    if st.button("Logout"):  
        st.session_state.token = None  
        st.write("You have been logged out.")  
        st.experimental_rerun()  # This will refresh the page and clear the session state  
  
# Create a session state variable to store the chat messages. This ensures that the messages persist across reruns.  
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
  
if is_authenticated():  
    # Create a file uploader for document uploads  
    uploaded_file = st.file_uploader("Upload a document", type=["pdf", "txt"])  
  
    # Create a chat input field to allow the user to enter a message. This will display automatically at the bottom of the page.  
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
  
        # Stream the response to the chat using `st.write_stream`, then store it in session state.  
        with st.chat_message("assistant"):  
            st.markdown(response)  
        st.session_state.messages.append({"role": "assistant", "content": response})  
else:  
    st.write("Please login to interact with the chatbot.")  
