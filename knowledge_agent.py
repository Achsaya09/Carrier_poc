from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
import os
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core import PromptTemplate
from llama_index.core.workflow import StartEvent, StopEvent, Workflow, step, Event
import asyncio
from typing import Optional
from cryptography.fernet import Fernet
import json
from openai import OpenAI
from fpdf import FPDF
 
# memory_knowledge = ChatMemoryBuffer.from_defaults(token_limit=5000)
 
class knowledgeagent(Workflow):
    def __init__(self, memory, timeout: Optional[float] = 300.0):    
        super().__init__(timeout=timeout)
        self._disable_validation = False
 
        with open('secret.key', 'rb') as key_file:
            key = key_file.read()
 
        cipher_suite = Fernet(key)
 
            # Load the encrypted configuration data
        with open('config.json', 'r') as config_file:
            encrypted_data = json.load(config_file)
 
        # Decrypt the sensitive information
        data = {key: cipher_suite.decrypt(value.encode()).decode() for key, value in encrypted_data.items()}
       
        # Set environment variables for API keys
        os.environ['OPENAI_API_KEY'] = data["API_KEY"]
       
        # Assign the persist directory and load index
        self.storage_context = StorageContext.from_defaults(persist_dir="./llama_embeddings_new_2_ca")
        self.index = load_index_from_storage(storage_context=self.storage_context)
        self.memory = memory
       
        # Initialize OpenAI client
        self.client = OpenAI(api_key=data["API_KEY"])
       
        # Initialize chat engine
        self.chat_engine = self.index.as_chat_engine(
            similarity_top_k=10,
            chat_mode="context",  
            memory=self.memory,
            system_prompt=(
                '''You are a helpful Assistant. While answering queries, be precise and realistic. Do not assume any information or facts on your own. You must generate answers strictly step by step based on the documents provided as input.
 
                When publishing any numerical data, crosscheck that the data is available in the input documents and ensure accuracy before providing the response.
 
                If the user asks a question related to generating a report (e.g., 'generate the report,' 'make me the report,' or similar), respond only with 'Generate Report.
 
                'For all other queries, follow the original guidelines and respond like a senior technician.'''
            )
        )
 
    def generate_ai_report(self, conversation_history):
        """Generate an AI report based on conversation history"""
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
         
        response = self.client.chat.completions.create(
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
 
    def create_pdf(self, workorder, report_data):
        """Create a PDF report"""
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", style="B", size=16)
       
        # Draw a border
        pdf.rect(10, 10, 190, 277)
       
        # Title
        pdf.cell(190, 10, "Customer Service Report", ln=True, align='C', border=1)
        pdf.ln(4)
       
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
     
       
        pdf.ln(4)
       
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
        pdf.ln(4)
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
 
    @step
    async def chat_with_engine(self, ev: StartEvent) -> StopEvent:
        # Use the engine to chat with the passed message and memory
        try:
            message = ev.topic
            response = self.chat_engine.chat(message)
            if str(response) == "Generate Report":
                workorder = {
                    "WO_number": "WO_CF_A21_1028",
                    "Technician_name": "William Reynolds",
                    "Customer": "Pavillion Court Apartments",
                    "Location": "Los Angeles CA",
                    "Chiller_model": "Carrier AquaEdge 19DV",
                    "Serial_no": "RAAS-25/2/25",
                    "Service_details": "AC unit not cooling"
                }
                report_text = self.generate_ai_report(self.memory)
                pdf_path = self.create_pdf(workorder, report_text)
                return StopEvent(result=[str("Report is Generated"),pdf_path])
            else:
                return StopEvent(result=str(response))
                   
        except Exception as e:
            return StopEvent(result=str({e}))
       
 
# async def calling(user_input):
#     # Initialize the workflow with memory
#     w = knowledgeagent(memory_knowledge)
#     # Run the workflow with the user input
#     result = await w.run(topic=user_input)
#     print(result)
 
#     # Use asyncio to run the coroutine
# if __name__ == "__main__":
#     while True:
#         user_imput = input("Enter the Query :")
#         if user_imput == "Exit":
#             break
#         else:
#             asyncio.run(calling(user_imput))
 