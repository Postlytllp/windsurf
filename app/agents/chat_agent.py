"""
Chat agent module for the Clinical Trials & FDA Data Search App.
Uses LangGraph to build an agent that can answer questions about clinical trials and FDA data.
"""
import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
import re
import numpy as np

# Add parent directory to path to import key loading module
sys.path.append(str(Path(__file__).parent.parent.parent))

# Load API keys directly from file
api_keys_path = os.path.join(Path(__file__).parent.parent.parent, "API_KEYS.txt")
if os.path.exists(api_keys_path):
    with open(api_keys_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('OPENAI_API_KEY'):
                parts = line.split('=', 1)
                if len(parts) == 2:
                    api_key = parts[1].strip().strip('"\'')
                    os.environ['OPENAI_API_KEY'] = api_key
                    print(f"Set OPENAI_API_KEY from file: {api_key[:10]}...")
                    break

# Get OpenAI API key from environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
if not OPENAI_API_KEY:
    print("WARNING: OPENAI_API_KEY environment variable is not set!")
else:
    print(f"Using OPENAI_API_KEY: {OPENAI_API_KEY[:10]}...")
llm = ChatOpenAI(model="gpt-4.1") 

class AgentState(BaseModel):
    """State for the chat agent graph."""
    query: str
    clinical_trials_df: Optional[List[Dict[str, Any]]] = None
    fda_df: Optional[List[Dict[str, Any]]] = None
    chat_history: List[Dict[str, str]] = []
    context: str = ""
    answer: Optional[str] = None
    sources: List[Dict[str, Any]] = []
    error: Optional[str] = None
    # New fields for data filtering and code generation
    selected_dataframes: List[str] = []
    generated_code: str = ""
    execution_result: Dict[str, Any] = {}
    filtered_data: Optional[List[Dict[str, Any]]] = None
    retry_count: int = 0

def create_code_generation_agent(state: AgentState) -> AgentState:
    """
    Generate Python code to filter and analyze the data based on the query.
    """
    try:
        print(f"[Code Generation Agent] Generating code for query: {state.query}")
        # Create context about available data
        data_context = "# Data Context for Analysis\n"
        
        # Read column information from CSV files
        clinical_trials_columns = []
        fda_columns = []
        
        try:
            # Read clinical trials column information
            with open("d:/CT_FDA/windsurf/clinical_trials_column.csv", "r") as f:
                import csv
                reader = csv.DictReader(f)
                clinical_trials_columns = list(reader)
            
            # Read FDA column information
            with open("d:/CT_FDA/windsurf/fda_column.csv", "r") as f:
                import csv
                reader = csv.DictReader(f)
                fda_columns = list(reader)
        except Exception as e:
            print(f"Error reading column CSV files: {str(e)}")
         
        # Add information about clinical trials data if selected
        if "clinical_trials_df" in state.selected_dataframes and state.clinical_trials_df:
            data_context += "\n## Clinical Trials Data Structure:\n"
            if state.clinical_trials_df:
                # Get column names from the first item
                sample_item = state.clinical_trials_df[0]
                data_context += f"Available fields: {', '.join(sample_item.keys())}\n"
                data_context += f"Total records: {len(state.clinical_trials_df)}\n"
                
                # Add column descriptions from CSV
                if clinical_trials_columns:
                    data_context += "\nKey columns with descriptions:\n"
                    for col in clinical_trials_columns:
                        if col["column_name"] in sample_item:
                            data_context += f"- {col['column_name']} ({col['data_type']}): {col['description']}\n"
                
                # Add a few sample records
                data_context += f"Sample data (first 3 records):\n{json.dumps(state.clinical_trials_df[:3], indent=2)[:1000]}...\n"
        
        # Add information about FDA data if selected
        if "fda_df" in state.selected_dataframes and state.fda_df:
            data_context += "\n## FDA Data Structure:\n"
            if state.fda_df:
                # Get column names from the first item
                sample_item = state.fda_df[0]
                data_context += f"Available fields: {', '.join(sample_item.keys())}\n"
                data_context += f"Total records: {len(state.fda_df)}\n"
                
                # Add column descriptions from CSV
                if fda_columns:
                    data_context += "\nKey columns with descriptions:\n"
                    for col in fda_columns:
                        if col["column_name"] in sample_item:
                            data_context += f"- {col['column_name']} ({col['data_type']}): {col['description']}\n"
                
                # Add a few sample records
                data_context += f"Sample data (first 3 records):\n{json.dumps(state.fda_df[:3], indent=2)[:1000]}...\n"
        
        # Create the code generation prompt
        code_prompt = f"""You are a smart and intellegent clinical trial and Food Drug Authority (FDA) Analyst. Your job is to Generate Python code that:
        - Uses only provided variables
        - Give the final dataframe from which answer to the query can be answered, and all the dataframes in the code should have a suffix '_df
        - Includes any necessary imports
        - If fixing an error, correct the previous code while maintaining logic
        - While matching any name lower the case for the term to search and in data where to search
        - Also, try to use contains rather than exact match like ==
        - You have available dataframe are {state.selected_dataframes}  
        -The data context is as below:
        {data_context}
        """
        
        # Create messages for the LLM
        messages = [
            {"role": "system", "content": code_prompt},
            {"role": "user", "content": state.query}
        ]
        
        # Get response from LLM
        llm = ChatOpenAI(model="gpt-4.1")
        response = llm.invoke(messages)
        code = response.content
        
        # Extract code from markdown if present
        code_match = re.search(r'```python\n(.*?)```', code, flags=re.DOTALL)
        if code_match:
            code = code_match.group(1).strip()
        else:
            # If no code block, use the entire response but remove any markdown
            code = re.sub(r'```.*?```', '', code, flags=re.DOTALL).strip()
        
        print(f"[Code Generation Agent] Generated code: {code}")
        state.generated_code = code
        return state
    except Exception as e:  
        print(f"[Code Generation Agent] Error: {str(e)}")   
        state.error = f"Error generating code: {str(e)}"
        return state

def execute_code(state: AgentState) -> AgentState:
    """
    Execute the generated code to filter and analyze the data.
    """
    try:
        print(f"[Code Execution Agent] Executing code for query: {state.query}")
        # Prepare data for execution
        local_vars = {
            'pd': pd,
            # 'np': __import__('numpy'),
            # 're': __import__('re'),
            '__builtins__': __builtins__,
        }
        
        # Add selected data to local variables
        if "clinical_trials_df" in state.selected_dataframes:
            # Convert list of dictionaries to DataFrame if it's not already a DataFrame
            if isinstance(state.clinical_trials_df, list) and state.clinical_trials_df:
                local_vars["clinical_trials_df"] = pd.DataFrame(state.clinical_trials_df)
            else:
                local_vars["clinical_trials_df"] = state.clinical_trials_df or []
        if "fda_df" in state.selected_dataframes:
            # Convert list of dictionaries to DataFrame if it's not already a DataFrame
            if isinstance(state.fda_df, list) and state.fda_df:
                local_vars["fda_df"] = pd.DataFrame(state.fda_df)
            else:
                local_vars["fda_df"] = state.fda_df or []
        
        # Execute the code
        output = ""
        error = None
        last_df_name = None
        
        # Set pandas display options to avoid truncation
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        
        try:
            # Redirect stdout to capture output
            import io
            import sys
            mystdout = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = mystdout
            # Store initial variables
            initial_vars = set(local_vars.keys())
            
            # Execute the code
            exec(state.generated_code, local_vars)
            
            # Find all new DataFrame variables
            new_vars = set(local_vars.keys()) - initial_vars
            df_vars = {var: local_vars[var] for var in new_vars 
                    if isinstance(local_vars[var], pd.DataFrame)}
            
            # Print information about all DataFrames created
            if df_vars:
                print(f"\n--- Created {len(df_vars)} DataFrames ---")
                for df_name, df in df_vars.items():
                    print(f"\nDataFrame: {df_name}")
                    print(f"Shape: {df.shape}")
                    print(f"Columns: {list(df.columns)}")
                    print(f"Sample data:")
                    print(df.head(5))
                    print("-" * 50)
            
            # Get the last DataFrame created (if any exist)
            result_df = None
            if df_vars:
                last_df_name = re.findall(r'\b\w+_df\b', state.generated_code)[-1]
                if last_df_name in local_vars:
                    result_df = local_vars[last_df_name]
                    # Print the DataFrame to capture it in the output
                    print(f"\n--- Final DataFrame ({last_df_name}) ---")
                    print(result_df)
            
            # Get output
            output = mystdout.getvalue()
            sys.stdout = old_stdout
            pd.reset_option('display.max_rows')
            pd.reset_option('display.max_columns')
            pd.reset_option('display.width')
            
        except Exception as e:
            error = str(e)
            sys.stdout = old_stdout
            pd.reset_option('display.max_rows')
            pd.reset_option('display.max_columns')
            pd.reset_option('display.width')
            
            # Create a simple error DataFrame
            error_df = pd.DataFrame({
                "error": [str(e)],
                "query": [state.query]
            })
            
            # Add summary data even on error
            summary_data = []
            if "clinical_trials_df" in state.selected_dataframes:
                summary_data.append({
                    "data_source": "Clinical Trials",
                    "total_records": len(state.clinical_trials_df or []),
                    "query": state.query
                })
            
            if "fda_df" in state.selected_dataframes:
                summary_data.append({
                    "data_source": "FDA Data",
                    "total_records": len(state.fda_df or []),
                    "query": state.query
                })
            
            state.filtered_data = summary_data
        

        # Store execution results
        state.execution_result = {
            "output": output,
            "error": error,
            "last_df_name": last_df_name,
            "dataframes": {name: df.to_dict('records') for name, df in df_vars.items()} if 'df_vars' in locals() and df_vars else {}
        }
        
        if error:
            print(f"[Code Execution Agent] Error executing code: {error}")
            state.error = f"Error executing code: {error}"
        else:
            print(f"[Code Execution Agent] Code executed successfully")
            if state.filtered_data:
                print(f"[Code Execution Agent] Found {len(state.filtered_data)} filtered records")
            else:
                print("[Code Execution Agent] No filtered data found")
        
        return state
    except Exception as e:
        print(f"[Code Execution Agent] Error: {str(e)}")
        state.error = f"Error executing code: {str(e)}"
        return state

def generate_answer(state: AgentState) -> AgentState:
    """
    Generate an answer to the query based on the context.
    """
    try:
        print(f"[Final Answer Generation] Generating answer for query: {state.query}    ")
        # Create the prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert healthcare analyst specializing in clinical trials and FDA data.
            Your task is to provide a clear, concise answer to the user's query based on the data analysis results.
            
            Guidelines:
            - Focus on directly answering the query with specific facts and numbers from the data
            - Use bullet points for lists or multiple findings
            - Include relevant statistics and trends
            - Be objective and factual
            - Cite specific data points when relevant
            - If the data is insufficient to answer the query, clearly state this
            
            FORMAT YOUR RESPONSE USING MARKDOWN:
            - Use **bold** for important numbers and key findings
            - Use bullet points (- item) for lists
            - Use headers (## or ###) for sections if needed
            - Use tables for structured data if appropriate
            - Include line breaks for readability
            
            The data analysis has been performed and the results are provided below.
            """),
            ("user", """Query: {query}
            
            Data Analysis Results:
            {output}
            
            DataFrame Results:
            {dataframe_results}
            
            Based on this analysis, provide a clear and concise answer to the query.
            """)
        ])
        
        # Prepare dataframe results text
        dataframe_results = ""
        if state.execution_result and "dataframes" in state.execution_result and state.execution_result["dataframes"]:
            dataframes = state.execution_result["dataframes"]
            for df_name, records in dataframes.items():
                if records:
                    dataframe_results += f"\n{df_name}:\n"
                    # Show first 5 records or fewer if less available
                    sample_records = records[:5]
                    for i, record in enumerate(sample_records):
                        dataframe_results += f"Record {i+1}: {record}\n"
                    if len(records) > 5:
                        dataframe_results += f"... and {len(records) - 5} more records\n"
        
        if not dataframe_results:
            dataframe_results = "No DataFrame results available."
        
        # Get the model - using the existing llm variable
        
        # Format the prompt with the data
        formatted_prompt = prompt.format(
            query=state.query,
            output=state.execution_result.get("output", "No output available.") if state.execution_result else "No execution results available.",
            dataframe_results=dataframe_results
        )
        
        # Get the response from the model
        response = llm.invoke(formatted_prompt)
        
        # Extract the answer
        answer = response.content
        
        # Store the answer in the state
        state.answer = answer
        
        # Extract sources from filtered data
        sources = []
        if state.filtered_data:
            for record in state.filtered_data[:5]:  # Limit to 5 sources
                source = {}
                
                # For clinical trials
                if "nctId" in record:
                    source["type"] = "clinical_trial"
                    source["id"] = record.get("nctId", "Unknown")
                    source["name"] = record.get("briefTitle", "Unknown Trial")
                    source["url"] = f"https://clinicaltrials.gov/study/{source['id']}" if source['id'] != "Unknown" else None
                
                # For FDA data
                elif "brand_name" in record:
                    source["type"] = "fda_df"
                    source["id"] = record.get("product_ndc", "Unknown")
                    source["name"] = record.get("brand_name", "Unknown Drug")
                
                if source:
                    sources.append(source)
        
        state.sources = sources
        print(f"[Final Answer Generation] Answer generated: {len(answer)} characters, {len(state.sources)} sources")
        
        return state
    except Exception as e:
        print(f"[Final Answer Generation] Error: {str(e)}")
        state.error = f"Error generating final answer: {str(e)}"
        state.answer = f"I encountered an error while analyzing the data: {str(e)}"
        return state

def create_chat_agent():
    """
    Create a LangGraph agent for answering questions about clinical trials and FDA data.
    
    Returns:
        A compiled LangGraph agent.
    """
    # Initialize LLM
    try:
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            api_key=OPENAI_API_KEY
        )
    except Exception as e:
        print(f"Error initializing ChatOpenAI: {str(e)}")
        raise

    # Create the graph
    workflow = StateGraph(AgentState)
    
    # 1. Dataframe Selection Agent: Determine which dataframes are relevant to the query
    def select_dataframes(state: AgentState) -> AgentState:
        """
        Determine which dataframes are relevant to the query.
        """
        try:
            print(f"[Dataframe Selection Agent] Analyzing query: {state.query}")
            # Define the selection prompt
            selection_prompt = f"""
            You are a specialized data source selection agent.
            
            Your task is to select which data sources are relevant to answer this query: "{state.query}"
            
            Available data sources:
            1. clinical_trials_df - Contains information about clinical trials including conditions, interventions, eligibility criteria, etc.
            2. fda_df - Contains FDA drug information including indications, warnings, adverse reactions, etc.
            
            Select one or both data sources based on the query. Return your selection as a list.
            If the query mentions drugs, medications, or FDA approvals, include "fda_df".
            If the query mentions clinical trials, studies, or research, include "clinical_trials_df".
            If the query could benefit from both sources, include both.
            """
            
            # Create messages for the LLM
            messages = [
                {"role": "system", "content": selection_prompt}
            ]
            
            # Get response from LLM
            response = llm.invoke(messages)
            content = response.content.lower()
            
            # Parse the response to get selected dataframes
            selected = []
            if "clinical_trials_df" in content or "clinical trials" in content:
                selected.append("clinical_trials_df")
            if "fda_df" in content or "fda" in content:
                selected.append("fda_df")
                
            # If nothing was selected, default to both
            if not selected:
                selected = ["clinical_trials_df", "fda_df"]
                
            print(f"[Dataframe Selection Agent] Selected dataframes: {selected}")
            state.selected_dataframes = selected
            return state
        except Exception as e:
            print(f"[Dataframe Selection Agent] Error: {str(e)}")
            state.error = f"Error selecting dataframes: {str(e)}"
            return state
    
    # 2. Code Generation Agent: Generate Python code to filter and analyze the data
    workflow.add_node("generate_code", create_code_generation_agent)
    
    # 3. Code Execution Agent: Execute the generated code to filter and analyze the data
    workflow.add_node("execute_code", execute_code)
    
    # 4. Final Answer Generation: Generate answer based on context
    workflow.add_node("generate_answer", generate_answer)
    
    # Add nodes to the workflow
    workflow.add_node("select_dataframes", select_dataframes)
    
    # Define the edges
    workflow.add_edge("select_dataframes", "generate_code")
    workflow.add_edge("generate_code", "execute_code")
    
    # Use a direct edge instead of conditional to avoid recursion issues
    workflow.add_edge("execute_code", "generate_answer")
    workflow.add_edge("generate_answer", END)
    
    # Set the entry point
    workflow.set_entry_point("select_dataframes")
    
    # Compile the workflow
    compiled_workflow = workflow.compile()
    print("[Workflow Manager] Workflow compiled successfully")
    
    # Return the compiled workflow
    return compiled_workflow

async def process_chat_query(
    query: str,
    clinical_trials_df: Optional[List[Dict[str, Any]]] = None,
    fda_df: Optional[List[Dict[str, Any]]] = None,
    chat_history: Optional[List[Dict[str, Any]]] = None
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Process a chat query using the LangGraph agent.
    
    Args:
        query: The user's query.
        clinical_trials_df: Clinical trials data for context.
        fda_df: FDA data for context.
        chat_history: Previous chat messages.
        
    Returns:
        Tuple[str, List[Dict[str, Any]]]: The answer and sources.
    """
    try:
        # Process chat history to handle sources
        processed_history = []
        if chat_history:
            for msg in chat_history:
                # Create a clean message without sources
                processed_msg = {"role": msg.get("role", ""), "content": msg.get("content", "")}
                
                # Parse sources if they exist and are in string format
                if "sources" in msg and isinstance(msg["sources"], str):
                    try:
                        # Try to parse JSON string sources
                        sources = json.loads(msg["sources"])
                        print(f"Parsed sources from history: {len(sources) if sources else 0} items")
                    except json.JSONDecodeError:
                        # If not valid JSON, keep as is
                        sources = msg["sources"]
                        print(f"Sources not in JSON format: {sources[:50]}...")
                else:
                    sources = None
                
                processed_history.append(processed_msg)
        
        # Create agent
        print("Creating chat agent workflow...")
        agent = create_chat_agent()
        
        # Initialize state
        print(f"Initializing agent state with query: {query}")
        print(f"Data provided: {len(clinical_trials_df or [])} clinical trials, {len(fda_df or [])} FDA records")
        
        initial_state = AgentState(
            query=query,
            clinical_trials_df=clinical_trials_df or [],
            fda_df=fda_df or [],
            chat_history=processed_history or []
        )
        
        # Run the agent
        print(f"Running multi-agent workflow for query: {query}")
        
        # Invoke the full LangGraph workflow
        try:
            # Use synchronous invocation - LangGraph's invoke is not awaitable
            final_state = agent.invoke(initial_state)
            print("Multi-agent workflow completed successfully")
            print(f"Final state type: {type(final_state)}")
            
            # Extract answer and sources from the AddableValuesDict
            # Access dictionary-style instead of attribute-style
            answer = final_state.get("answer", "")
            sources = final_state.get("sources", [])
            
            print(f"Extracted from final state - Answer: {answer[:50] if answer else ''}..., Sources: {len(sources) if sources else 0}")
            
            # Fallback if no answer
            if not answer:
                print("No answer found in final state, using fallback")
                answer = (
                    f"I analyzed the data related to your query about '{query}', but couldn't find a specific answer. "
                    f"There are {len(clinical_trials_df or [])} clinical trials and {len(fda_df or [])} FDA records available. "
                    "Please try asking a more specific question about this data."
                )
            
            return answer, sources
            
        except Exception as e:
            import traceback
            print(f"Error during agent invocation: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            # Fallback for invocation errors
            return (
                f"I'm sorry, but I encountered an error while processing your query: {str(e)}. "
                "Please try again with a more specific question.",
                []
            )
        
    except Exception as e:
        import traceback
        print(f"Chat agent error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        
        # Provide a helpful error message to the user
        return (
            f"I'm sorry, but I encountered an error while processing your query: {str(e)}. "
            "This might be due to the complexity of your question or the data format. "
            "Please try asking a simpler or more specific question.",
            []
        )
