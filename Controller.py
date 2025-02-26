from llama_index.core.workflow import StartEvent, StopEvent, Workflow, step, Event
from knowledge_agent import knowledgeagent
from llama_index.core.memory import ChatMemoryBuffer
import time
from typing import Optional
import json
from cryptography.fernet import Fernet
from llama_index.llms.openai import OpenAI
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define custom events
class OperationEvent(Event):
    operation: str
    query: str
 
class ResultEvent(Event):
    result: any
 
 
# Define the workflow
class LLMController(Workflow):
    def __init__(self, timeout: Optional[float] = 300.0):
        try:
            super().__init__(timeout=timeout)
            self._disable_validation = False
            self.memory_knowledge = ChatMemoryBuffer.from_defaults(token_limit=10000)
            
            try:
                with open('secret.key', 'rb') as key_file:
                    key = key_file.read()

                cipher_suite = Fernet(key)

                # Load the encrypted configuration data
                with open('config.json', 'r') as config_file:
                    encrypted_data = json.load(config_file)

                # Decrypt the sensitive information
                self.data = {key: cipher_suite.decrypt(value.encode()).decode() for key, value in encrypted_data.items()}
                
                
            except FileNotFoundError as e:
                logger.error(f"Configuration file not found: {e}")
                raise
            except json.JSONDecodeError as e:
                logger.error(f"JSON decoding error: {e}")
                raise
            except Exception as e:
                logger.error(f"Initialization error: {e}")
                raise
        except Exception as e:
            logger.critical(f"Failed to initialize LLMController: {e}")
            raise
       
    @step
    async def start(self, ev: StartEvent) -> OperationEvent:
        try:
            input_data = ev.data
            # LLM prompt engineering to decide the operation
            try:
                with open('secret.key', 'rb') as key_file:
                    key = key_file.read()
                cipher_suite = Fernet(key)
                with open('config.json', 'r') as config_file:
                    encrypted_data = json.load(config_file)

                data1 = {key: cipher_suite.decrypt(value.encode()).decode() for key, value in encrypted_data.items()}
            except FileNotFoundError as e:
                logger.error(f"Configuration file not found: {e}")
                return OperationEvent(operation="error", query=f"Error: Configuration file not found - {str(e)}")
            except Exception as e:
                logger.error(f"Error decrypting configuration: {e}")
                return OperationEvent(operation="error", query=f"Error processing configuration - {str(e)}")

            prompt = f"""
 
I can classify your input and route it to the appropriate agent. Here are the categories I use:
 
1. **knowledge_agent**: This agent act when your input involves general queries, requests for information, questions related to custom data or documents, or anything else that needs context-based responses. This agent is also responsible input involves Azure cloud related queries, requests for Azure cloud related information, questions related to Azure cloud related custom data or documents and question involves general queries.Additionally, this agent provides support for elevator-related queries, including troubleshooting, maintenance issues, technical specifications, safety guidelines, error code diagnostics, and operational concerns.
                 
2. **Greetings**: For simple welcome messages (e.g., 'hi', 'hello').
 
3. **Ending the conversation** : For end the conversation(e.g 'bye' , 'goodbye' ,'thanks for help')
 
Your input: '{input_data}'
 
I will classify your input into one of the following categories:
    - 'qanda' for the knowledge_agent (general queries, contextual questions,elevator question),
    - 'greetings' for welcome greetings (e.g., 'hi', 'hiiiii', 'hello')
    - 'end' for ending the conversation (e.g., 'thanks', 'goodbye').
Please wait for my classification: 'qanda'  or 'greetings' , 'end' - don't include any extra words.
 
"""
            try:
                llm = OpenAI(model="gpt-3.5-turbo", api_key=self.data["API_KEY"])
                # Get the completion and extract just the text
                completion_response = llm.complete(prompt)
                classification = str(completion_response.text).strip()
            except Exception as e:
                logger.error(f"LLM processing error: {e}")
                return OperationEvent(operation="error", query=f"Error processing your request - {str(e)}")
           
            return OperationEvent(operation=classification, query=input_data)
        except Exception as e:
            logger.error(f"Error in start step: {e}")
            return OperationEvent(operation="error", query=f"An error occurred: {str(e)}")
 
    @step
    async def perform_operation(self, ev: OperationEvent) -> ResultEvent:
        try:
            operation = ev.operation
            query = ev.query
     
            # Check for error operation
            if operation == "error":
                return ResultEvent(result=f"Error processing your request: {query}")
            
            # Initialize agents
            try:
                
                knowledge_agent = knowledgeagent(self.memory_knowledge,timeout=300.0)

            except Exception as e:
                logger.error(f"Error initializing agents: {e}")
                return ResultEvent(result=f"Failed to initialize required components: {str(e)}")
            
            start_time = time.time()
            print(operation)
            
            try:
                if "qanda" in operation:
                    result = await knowledge_agent.run(topic=query)
                   
         
                elif "greetings" in operation:
                    return ResultEvent(result="Hi! How can I help you today?")
                elif "end" in operation:
                    return ResultEvent(result="Happy to help, This is Elevatrix Ops Connect your AI Agent signing off. Good day!")
                else:
                    return ResultEvent(result="Please provide more information regarding your query")
            except Exception as e:
                logger.error(f"Error during agent operation {operation}: {e}")
                return ResultEvent(result=f"An error occurred while processing your '{operation}' request: {str(e)}")
     
            end_time = time.time()
            print(f"Operation took {end_time - start_time} seconds.")
            result_str = result
           
            return ResultEvent(result=result_str)
        except Exception as e:
            logger.error(f"Unhandled error in perform_operation: {e}")
            return ResultEvent(result=f"An unexpected error occurred: {str(e)}")
 
    @step
    async def finish(self, ev: ResultEvent) -> StopEvent:
        try:
            return StopEvent(result=ev.result)
        except Exception as e:
            logger.error(f"Error in finish step: {e}")
            return StopEvent(result=f"Error finalizing your request: {str(e)}")
 


 


 


 

