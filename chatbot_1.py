# import streamlit as st
# import os
# import json
# from cryptography.fernet import Fernet
# from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
# from llama_index.core.memory import ChatMemoryBuffer



# # Load encryption key
# with open('secret.key', 'rb') as key_file:
#     key = key_file.read()

# cipher_suite = Fernet(key)

# # Load and decrypt configuration data
# with open('config.json', 'r') as config_file:
#     encrypted_data = json.load(config_file)

# data = {key: cipher_suite.decrypt(value.encode()).decode() for key, value in encrypted_data.items()}

# # Set API key
# os.environ['OPENAI_API_KEY'] = data["API_KEY"]
# memory = ChatMemoryBuffer.from_defaults(token_limit=10000)  # Adjust token limit as needed
# st.set_page_config(page_title="Troubleshooting Assistant")

# st.markdown(
#     """
#     <style>
#     /* Hide the Streamlit header */
#     header {visibility: hidden;}
    
#     /* Hide bot icon in chat history */
#     .css-1rs6os.edgvbvh3 {visibility: hidden;} /* Additional styling for certain versions */
    
#     .chat-message__avatar {
#         display: none !important;  /* Ensures the bot icon is hidden */
#     }
#     </style>
#     """,
#     unsafe_allow_html=True
# )

# # Load stored embeddings
# storage_context = StorageContext.from_defaults(persist_dir="llama_embeddings_new_2_carrier")
# index = load_index_from_storage(storage_context)

# # Setup chat engine
# chat_engine = index.as_chat_engine(
#     similarity_top_k=10,
#     chat_mode="context",
#     memory=memory,
#     system_prompt=(
#         "You are a helpful Assistant. While answering queries, be precise and realistic. "
#         "Do not assume any information or facts on your own. You are supposed to generate answers strictly based on the documents provided as input. "
#         "While publishing any numerical data, crosscheck the data is available in the input documents and publish the correct data only. "
#         "You should answer like a senior technician."
#         """ Please include the source(s) of your information at the end of the response. If there are multiple sources, list them clearly.mention the file_name for the response only if applicable."
#         Instruction: Always respond with the following structured format:
#         <Your response>
#         Source: <If applicable, list the source(s) of your information. If from personal or general knowledge, omit this line from response strictly.> If the source is from personal or general knowledge, omit the source line from response strictly."
#         """
#     )
# )

# # Initialize Streamlit app

# st.sidebar.title('Troubleshooting Assistant')
# st.sidebar.markdown("**Hi, Welcome to the Troubleshooting Assistant.**")
# st.sidebar.markdown("This assistant helps diagnose and resolve issues by providing relevant information.")
# st.sidebar.markdown("It can assist with troubleshooting technical problems and offer guidance based on available documentation.")

# # Initialize session variables
# if 'messages' not in st.session_state:
#     st.session_state['messages'] = []

# # Display previous messages
# for message in st.session_state['messages']:
#     with st.chat_message(message['role']):
#         st.markdown(message['content'])

# # Chat interface
# if user_input := st.chat_input("Enter your query"):
#     st.session_state['messages'].append({"role": "user", "content": user_input})
#     with st.chat_message('user'):
#         st.markdown(user_input)
    
#     # Get response from the model
#     with st.chat_message('assistant'):
#         with st.spinner("Thinking..."):
#             bot_response = chat_engine.chat(user_input).response
        
#         st.markdown(bot_response)
#         st.session_state['messages'].append({"role": "assistant", "content": bot_response})






import streamlit as st
import os
import json
from cryptography.fernet import Fernet
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.core.memory import ChatMemoryBuffer
from fpdf import FPDF
from openai import OpenAI
# import unicodedata

st.set_page_config(page_title="Troubleshooting Assistant")

st.markdown(
    """
    <style>
    header {visibility: hidden;}
    .css-1rs6os.edgvbvh3 {visibility: hidden;}
    .chat-message__avatar {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# # Load encryption key
with open('secret.key', 'rb') as key_file:
    key = key_file.read()

cipher_suite = Fernet(key)

# Load and decrypt configuration data
with open('config.json', 'r') as config_file:
    encrypted_data = json.load(config_file)

data = {key: cipher_suite.decrypt(value.encode()).decode() for key, value in encrypted_data.items()}
client = OpenAI(api_key=data["API_KEY"])
# Set API key
os.environ['OPENAI_API_KEY'] = data["API_KEY"]
memory = ChatMemoryBuffer.from_defaults(token_limit=10000)
# Load stored embeddings
client = OpenAI()
storage_context = StorageContext.from_defaults(persist_dir="llama_embeddings_new_2_ca")
index = load_index_from_storage(storage_context)

# Setup chat engine
chat_engine = index.as_chat_engine(
    similarity_top_k=10,
    chat_mode="context",
    memory=memory,
    system_prompt=(
        "You are a helpful Assistant. While answering queries, be precise and realistic. "
        "Do not assume any information or facts on your own. You are supposed to generate answers in step by step strictly based on the documents provided as input. "
        "While publishing any numerical data, crosscheck the data is  available in the input documents and publish the correct data only. "
        "You should answer like a senior technician."
  
    )
)

st.sidebar.title('Troubleshooting Assistant')
st.sidebar.markdown("**Hi, Welcome to the Troubleshooting Assistant.**")
st.sidebar.markdown("This assistant helps diagnose and resolve issues by providing relevant information.")
st.sidebar.markdown("It can assist with troubleshooting technical problems and offer guidance based on available documentation.")

# Initialize session variables
if 'messages' not in st.session_state:
    st.session_state['messages'] = []
if 'report_generated' not in st.session_state:
    st.session_state['report_generated'] = False
if 'report_content' not in st.session_state:
    st.session_state['report_content'] = ""

# Function to detect if query is related to report generation using LLM
def is_report_request(query):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # You can use a smaller, faster model for this classification task
        messages=[
            {"role": "system", "content": "Your task is to determine if a user query is requesting a troubleshooting report to be generated. Respond with only 'YES' if the query is asking to generate, create, produce, get, download, or see a report. Otherwise, respond with 'NO'."},
            {"role": "user", "content": query}
        ],
        temperature=0,  # Keep temperature low for consistent results
        max_tokens=5    # We only need a short answer
    )
    
    classification = response.choices[0].message.content.strip().upper()
    return classification == "YES"

# Function to generate troubleshooting report using OpenAI
# def generate_ai_report():
#     conversation_history = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in st.session_state['messages']])

#     prompt = f"""
# Analyze the following troubleshooting conversation. Generate a structured troubleshooting report 

# - **Breakdown Details**  
# - **Diagnosis**  
# - **Resolution Method**  
# - **Recommended Actions**  

# **Don't include sources.**

# Conversation:
# {conversation_history}
# """

#     response = client.chat.completions.create(
#         model="gpt-4",
#         messages=[{"role": "system", "content": "You are an expert technician generating structured troubleshooting reports."},
#                   {"role": "user", "content": prompt}]
#     )

#     return response.choices[0].message.content

def generate_ai_report():
    conversation_history = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in st.session_state['messages']])
 
    prompt = f"""
Analyze the following troubleshooting conversation. Generate a structured troubleshooting report 
 
else, return a JSON-formatted structured dictionary with the following keys:
 
{{
    "status": "Resolved",
    "Breakdown Details": "Short summary of the issue.",
    "Diagnosis": "Analysis of the problem and possible root causes.",
    "Resolution Method": "Steps taken to fix the issue.",
    "Recommended Actions": "Future recommendations to prevent the issue."
}}
 
**Ensure the output is valid JSON.**
 
Conversation:
{conversation_history}
"""
 
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an expert technician generating structured troubleshooting reports."},
            {"role": "user", "content": prompt}
        ]
    )
 
    try:
        report_data = json.loads(response.choices[0].message.content)
        return report_data
    except json.JSONDecodeError:
        return {"status": "Not Resolved"}

# Function to create PDF from AI-generated report

# def create_pdf(report_text):
#     pdf = FPDF()
#     pdf.set_auto_page_break(auto=True, margin=15)
#     pdf.add_page()
#     pdf.set_font("Arial", style="B", size=16)
#     pdf.cell(200, 10, "Troubleshooting Report", ln=True, align='C')
    
#     pdf.set_font("Arial", size=12)
#     pdf.ln(10)

#     # Normalize Unicode and replace unsupported characters
#     report_text = unicodedata.normalize('NFKD', report_text).encode('latin-1', 'ignore').decode('latin-1')

#     for line in report_text.split("\n"):
#         pdf.multi_cell(0, 8, line)
#         pdf.ln(2)
    
#     pdf_path = "troubleshooting_report.pdf"
#     pdf.output(pdf_path)
#     return pdf_path

def create_pdf(workorder, report_data):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", style="B", size=16)
   
    # Draw a border
    pdf.rect(10, 10, 190, 277)
   
    # Title
    pdf.cell(190, 10, "Customer Service Report", ln=True, align='C', border=1)
    pdf.ln(5)
   
    # Compact Work Order Details (Two values in one cell)
    pdf.set_font("Arial", size=11)
    details = [
        ("WO Number:", workorder['WO_number'], "Technician:", workorder['Technician_name']),
        ("Customer:", workorder['Customer'], "Location:", workorder['Location']),
        ("Chiller Model:", workorder['Chiller_model'], "Serial No:", workorder['Serial_no'])]
   
    col_widths = [37, 58, 37, 58]  # Adjusted column widths for better alignment
   
    for label1, value1, label2, value2 in details:
        pdf.set_font("Arial", style="B", size=11)
        pdf.cell(col_widths[0], 10, label1, border=1)
        pdf.set_font("Arial", size=11)
        pdf.cell(col_widths[1], 10, value1, border=1)
        pdf.set_font("Arial", style="B", size=11)
        pdf.cell(col_widths[2], 10, label2, border=1)
        pdf.set_font("Arial", size=11)
        pdf.cell(col_widths[3], 10, value2, border=1, ln=True)
 
    pdf.set_font("Arial", style="B", size=11)
    pdf.cell(37, 10, "Service Details:", border=1)
    pdf.set_font("Arial", size=11)
    pdf.cell(153, 10, workorder['Service_details'], border=1, ln=True)  # Spanning across remaining width
 
   
    pdf.ln(5)
   
    # Insert report sections
    if report_data.get("status") == "Resolved":
        sections = ["Breakdown Details", "Diagnosis", "Resolution Method", "Recommended Actions"]
        for section in sections:
            pdf.set_font("Arial", style="B", size=12)
            pdf.cell(0, 10, section, ln=True, align='L')
            pdf.set_font("Arial", size=11)
            pdf.multi_cell(0, 8, report_data.get(section, "No information provided"))
            pdf.ln(5)  
   
    # Customer Feedback Section
    pdf.ln(5)
    pdf.set_font("Arial", style="B", size=12)
    pdf.cell(0, 10, "Customer Feedback", ln=True, align='L')
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 8, "Comments:")
    pdf.ln(10)
    pdf.cell(95, 10, "Signature:", border=1)
    pdf.cell(95, 10, "Date:", border=1, ln=True)
   
    pdf_path = "customer_service_report.pdf"
    pdf.output(pdf_path)
    return pdf_path

# Display previous messages
for message in st.session_state['messages']:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

# Chat interface
if user_input := st.chat_input("Enter your query"):
    st.session_state['messages'].append({"role": "user", "content": user_input})
    with st.chat_message('user'):
        st.markdown(user_input)
    
    # Check if it's a report request
    is_report_query = is_report_request(user_input)
    print(is_report_query)
    # Get response from the model
    with st.chat_message('assistant'):
        if is_report_query:
            # Get the RAG response but don't display it (we still need it for conversation context)
            with st.spinner("Processing your request..."):
                bot_response = chat_engine.chat(user_input).response
                # Add to session state but don't display
                st.session_state['messages'].append({"role": "assistant", "content": bot_response})
            
            # Call AI to generate a report
            with st.spinner("Analyzing conversation and generating report..."):
                report_text = generate_ai_report()
                # print(report_text)

            workorder = {
                "WO_number": "WO_CF_A21_1028",
                "Technician_name": "William Reynolds",
                "Customer": "Pavillion Court Apartments",
                "Location": "Los Angeles CA",
                "Chiller_model": "Carrier AquaEdge 19DV",
                "Serial_no": "RAAS-25/2/25",
                "Service_details": "AC unit not cooling"
            }

            if "Not Resolved":
                print("entering into the  right group")
                pdf_path = create_pdf(workorder , report_text)
                st.session_state['report_generated'] = True
                st.session_state['report_content'] = pdf_path
                
                # Display a friendly message instead of the RAG response
                report_message = "I've analyzed your conversation and generated a troubleshooting report. You can download it using the button below."
                st.markdown(report_message)
            else:
                # If no issue has been resolved yet
                no_report_message = "I couldn't generate a report as no issue has been marked as resolved yet. Please continue troubleshooting or explicitly mark an issue as resolved."
                st.markdown(no_report_message)
                # Add this message to the conversation history
                st.session_state['messages'].append({"role": "assistant", "content": no_report_message})
        else:
            # Regular query - show the RAG response
            with st.spinner("Thinking..."):
                print("generating the chat response")
                bot_response = chat_engine.chat(user_input).response
                st.markdown(bot_response)
                st.session_state['messages'].append({"role": "assistant", "content": bot_response})
            

# Show download button if report is generated
if st.session_state['report_generated']:
    with open(st.session_state['report_content'], "rb") as pdf_file:
        st.download_button(label="Download Troubleshooting Report",
                           data=pdf_file,
                           file_name="troubleshooting_report.pdf",
                           mime="application/pdf")
