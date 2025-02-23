import streamlit as st
import os
import json
from cryptography.fernet import Fernet
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.core.memory import ChatMemoryBuffer

# Load encryption key
with open('secret.key', 'rb') as key_file:
    key = key_file.read()

cipher_suite = Fernet(key)

# Load and decrypt configuration data
with open('config.json', 'r') as config_file:
    encrypted_data = json.load(config_file)

data = {key: cipher_suite.decrypt(value.encode()).decode() for key, value in encrypted_data.items()}

# Set API key
os.environ['OPENAI_API_KEY'] = data["API_KEY"]
memory = ChatMemoryBuffer.from_defaults(token_limit=10000)  # Adjust token limit as needed

# Load stored embeddings
storage_context = StorageContext.from_defaults(persist_dir="llama_embeddings_new_2_carrier")
index = load_index_from_storage(storage_context)

# Setup chat engine
chat_engine = index.as_chat_engine(
    similarity_top_k=10,
    chat_mode="context",
    memory=memory,
    system_prompt=(
        "You are a helpful Assistant. While answering queries, be precise and realistic. "
        "Do not assume any information or facts on your own. You are supposed to generate answers strictly based on the documents provided as input. "
        "While publishing any numerical data, crosscheck the data is available in the input documents and publish the correct data only. "
        "You should answer like a senior technician."
        """ Please include the source(s) of your information at the end of the response. If there are multiple sources, list them clearly.mention the file_name for the response only if applicable."
        Instruction: Always respond with the following structured format:
        <Your response>
        Source: <If applicable, list the source(s) of your information. If from personal or general knowledge, omit this line from response strictly.> If the source is from personal or general knowledge, omit the source line from response strictly."
        """
    )
)

# Initialize Streamlit app
st.set_page_config(page_title="Troubleshooting Assistant")
st.sidebar.title('Troubleshooting Assistant')
st.sidebar.markdown("**Hi, Welcome to the Troubleshooting Assistant.**")
st.sidebar.markdown("This assistant helps diagnose and resolve issues by providing relevant information.")
st.sidebar.markdown("It can assist with troubleshooting technical problems and offer guidance based on available documentation.")

# Initialize session variables
if 'messages' not in st.session_state:
    st.session_state['messages'] = []

# Display previous messages
for message in st.session_state['messages']:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

# Chat interface
if user_input := st.chat_input("Enter your query"):
    st.session_state['messages'].append({"role": "user", "content": user_input})
    with st.chat_message('user'):
        st.markdown(user_input)
    
    # Get response from the model
    with st.chat_message('assistant'):
        with st.spinner("Thinking..."):
            bot_response = chat_engine.chat(user_input).response
        
        st.markdown(bot_response)
        st.session_state['messages'].append({"role": "assistant", "content": bot_response})
