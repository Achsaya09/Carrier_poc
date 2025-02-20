import chainlit as cl
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
import os
import streamlit as st
from cryptography.fernet import Fernet
import json
with open('secret.key', 'rb') as key_file:
        key = key_file.read()
 
        cipher_suite = Fernet(key)
 
        # Load the encrypted configuration data
        with open('config.json', 'r') as config_file:
            encrypted_data = json.load(config_file)
 
        # Decrypt the sensitive information
        data = {key: cipher_suite.decrypt(value.encode()).decode() for key, value in encrypted_data.items()}
        


# Set API key
os.environ['OPENAI_API_KEY'] = data["API_KEY"]
# Load stored embeddings
storage_context = StorageContext.from_defaults(persist_dir="llama_embeddings_new_2_carrier")
index = load_index_from_storage(storage_context)

# Setup chat engine with custom configuration
chat_engine = index.as_chat_engine(
    similarity_top_k=10,
    chat_mode="context",
    system_prompt=(
        "You are a helpful Assistant. While answering queries, be precise and realistic. "
        "Do not assume any information or facts on your own. You are supposed to generate answers strictly based on the documents provided as input. "
        "While publishing any numerical data, crosscheck the data is available in the input documents and publish the correct data only. "
        "You should answer like a senior technician."
    )
)
@cl.on_chat_start
async def main():
    await cl.Message(content="Hi, I am a troubleshooting assistant. How can I help you today?").send()

    # ChatInput = ui.ChatInput(placeholder="")  # To remove the placeholder
    # # OR
    # ChatInput = ui.ChatInput(placeholder="Enter your message here...") # Custom placeholder

    # # Set the chat input in the UI
    # await ui.Chat(inputs=[ChatInput]).update()  # Update the UI with the ChatInput


@cl.on_message
async def main(message: cl.Message):
    
    # Retrieve chat history
    history = cl.user_session.get("history", [])
    

    # Append the new message to history
    history.append({"role": "user", "content": message.content})

    #with cl.spinner("Thinking..."):  # Start spinner
        # Generate response using history
    response = chat_engine.chat(message.content)

        # Append assistant's response to history
    history.append({"role": "assistant", "content": response.response})

        # Save updated history
    cl.user_session.set("history", history)

    # Send response back
    await cl.Message(content=response.response).send()
