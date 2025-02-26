import streamlit as st
import asyncio
import uuid
from Controller import LLMController

class DataQueryChatbot:
    def __init__(self):
        self.controller = LLMController(timeout=300.0)

    async def chat(self, input_data):
        return await self.controller.run(data=input_data)

# Initialize chatbot in session state
if "chatbot" not in st.session_state:
    st.session_state.chatbot = DataQueryChatbot()

# Custom CSS to hide elements
st.markdown(
    """
    <style>
    header {visibility: hidden;}
    .css-1rs6os.edgvbvh3 {visibility: hidden;}
    .chat-message__avatar { display: none !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar Information
st.sidebar.title('Troubleshooting Assistant')
st.sidebar.markdown("**Hi, Welcome to the Troubleshooting Assistant.**")
st.sidebar.markdown("This assistant helps diagnose and resolve issues by providing relevant information.")

# Initialize session variables
if 'messages' not in st.session_state:
    st.session_state['messages'] = []
if 'report_generated' not in st.session_state:
    st.session_state['report_generated'] = False
if 'report_content' not in st.session_state:
    st.session_state['report_content'] = ""

# Display previous messages
for message in st.session_state['messages']:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

# Chat interface
if user_input := st.chat_input("Enter your query"):
    st.session_state['messages'].append({"role": "user", "content": user_input})
    with st.chat_message('user'):
        st.markdown(user_input)

    # Get response from model
    with st.chat_message('assistant'):
        with st.spinner("Generating response..."):
            bot_response = asyncio.run(st.session_state.chatbot.chat(user_input))
        if not isinstance(bot_response, list):
            st.markdown(bot_response)
            st.session_state['messages'].append({"role": "assistant", "content": bot_response})
        else:
            st.markdown(bot_response[0])
            st.session_state['messages'].append({"role": "assistant", "content": bot_response[0]})
            with open(bot_response[1], "rb") as pdf_file:
                st.download_button(label="Download Customer Service Report",
                                data=pdf_file,
                                file_name="customer_service_report.pdf",
                                mime="application/pdf")


    # Generate troubleshooting report if applicable
    # with st.spinner("Analyzing conversation..."):
    #     report_data = asyncio.run(st.session_state.chatbot.generate_report())

    # if report_data.get("status") == "Resolved":
    #     pdf_path = st.session_state.chatbot.controller.create_pdf(report_data)
    #     st.session_state['report_generated'] = True
    #     st.session_state['report_content'] = pdf_path
    # else:
    #     st.session_state['report_generated'] = False

# Show download button if report is generated
if st.session_state['report_generated']:
    with open(st.session_state['report_content'], "rb") as pdf_file:
        st.download_button(label="Download Customer Service Report",
                           data=pdf_file,
                           file_name="customer_service_report.pdf",
                           mime="application/pdf")
