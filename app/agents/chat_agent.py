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

class AgentState(BaseModel):
    """State for the chat agent graph."""
    query: str
    clinical_trials_data: Optional[List[Dict[str, Any]]] = None
    fda_data: Optional[List[Dict[str, Any]]] = None
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
    
    # 1. Select relevant dataframes based on the query
    def select_dataframes(state: AgentState) -> AgentState:
        """
        Determine which dataframes are relevant to the query.
        """
        try:
            print(f"Selecting dataframes for query: {state.query}")
            # Define the selection prompt
            selection_prompt = f"""
            Your task is to select which data sources are relevant to answer this query: "{state.query}"
            
            Available data sources:
            1. clinical_trials_data - Contains information about clinical trials including conditions, interventions, eligibility criteria, etc.
            2. fda_data - Contains FDA drug information including indications, warnings, adverse reactions, etc.
            
            Select one or both data sources based on the query. Return your selection as a list.
            If the query mentions drugs, medications, or FDA approvals, include "fda_data".
            If the query mentions clinical trials, studies, or research, include "clinical_trials_data".
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
            if "clinical_trials_data" in content or "clinical trials" in content:
                selected.append("clinical_trials_data")
            if "fda_data" in content or "fda" in content:
                selected.append("fda_data")
                
            # If nothing was selected, default to both
            if not selected:
                selected = ["clinical_trials_data", "fda_data"]
                
            print(f"Selected dataframes: {selected}")
            state.selected_dataframes = selected
            return state
        except Exception as e:
            print(f"Error in select_dataframes: {str(e)}")
            state.error = f"Error selecting dataframes: {str(e)}"
            return state
    
    # 2. Generate code to filter and analyze the data
    def generate_code(state: AgentState) -> AgentState:
        """
        Generate Python code to filter and analyze the data based on the query.
        """
        try:
            print(f"Generating code for query: {state.query}")
            # Create context about available data
            data_context = ""
            
            # Add information about clinical trials data if selected
            if "clinical_trials_data" in state.selected_dataframes and state.clinical_trials_data:
                data_context += "\n## Clinical Trials Data Structure:\n"
                if state.clinical_trials_data:
                    # Get column names from the first item
                    if len(state.clinical_trials_data) > 0:
                        columns = list(state.clinical_trials_data[0].keys())
                        data_context += f"Available columns: {columns}\n"
                        # Add a few sample records
                        data_context += f"Sample data (first 3 records):\n{json.dumps(state.clinical_trials_data[:3], indent=2)[:1000]}...\n"
            
            # Add information about FDA data if selected
            if "fda_data" in state.selected_dataframes and state.fda_data:
                data_context += "\n## FDA Data Structure:\n"
                if state.fda_data:
                    # Get column names from the first item
                    if len(state.fda_data) > 0:
                        columns = list(state.fda_data[0].keys())
                        data_context += f"Available columns: {columns}\n"
                        # Add a few sample records
                        data_context += f"Sample data (first 3 records):\n{json.dumps(state.fda_data[:3], indent=2)[:1000]}...\n"
            
            # Create the code generation prompt
            code_prompt = f"""You are an expert data analyst specializing in healthcare data. 
            Your task is to generate Python code that filters and analyzes data to answer this query: "{state.query}"
            
            {data_context}
            
            Generate Python code that:
            1. Converts the input data to pandas DataFrames
            2. Filters the data based on the query using case-insensitive matching
            3. Performs any necessary analysis to answer the query
            4. Returns the relevant filtered data as a DataFrame with suffix '_df'
            
            Important guidelines:
            - Use pandas for data manipulation
            - Make string comparisons case-insensitive (use .lower() or .str.contains() with case=False)
            - Prefer partial matches (contains) over exact matches
            - Include all necessary imports
            - Handle potential missing values or empty fields
            - Return only the code, no explanations
            """
            
            # Create messages for the LLM
            messages = [
                {"role": "system", "content": code_prompt}
            ]
            
            # Get response from LLM
            response = llm.invoke(messages)
            
            # Extract code from the response
            code = response.content
            
            # Clean up the code (remove markdown code blocks if present)
            import re
            code_match = re.search(r'```python\n(.*?)```', code, flags=re.DOTALL)
            if code_match:
                code = code_match.group(1).strip()
            else:
                # If no code block, use the entire response but remove any markdown
                code = re.sub(r'```.*?```', '', code, flags=re.DOTALL).strip()
            
            print(f"Generated code:\n{code[:200]}...")
            state.generated_code = code
            return state
        except Exception as e:
            print(f"Error in generate_code: {str(e)}")
            state.error = f"Error generating code: {str(e)}"
            return state
    
    # 3. Execute the generated code
    def execute_code(state: AgentState) -> AgentState:
        """
        Execute the generated code to filter and analyze the data.
        """
        try:
            print(f"Executing code for query: {state.query}")
            # Prepare data for execution
            local_vars = {
                'pd': pd,
                '__builtins__': __builtins__,
            }
            
            # Add selected data to local variables
            if "clinical_trials_data" in state.selected_dataframes:
                local_vars["clinical_trials_data"] = state.clinical_trials_data or []
            if "fda_data" in state.selected_dataframes:
                local_vars["fda_data"] = state.fda_data or []
            
            # Capture stdout
            from io import StringIO
            import sys
            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()
            
            # Set pandas display options
            pd.set_option('display.max_rows', None)
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', None)
            
            result_df = None
            last_df_name = None
            error = None
            
            try:
                # Execute the code
                exec(state.generated_code, local_vars)
                
                # Find all DataFrame variables created by the code
                df_vars = {name: var for name, var in local_vars.items() 
                          if isinstance(var, pd.DataFrame) and name not in ['pd']}
                
                # Get the last DataFrame created (if any)
                if df_vars:
                    # Find the last DataFrame with _df suffix
                    df_names = [name for name in df_vars.keys() if name.endswith('_df')]
                    if df_names:
                        last_df_name = df_names[-1]
                        result_df = df_vars[last_df_name]
                        
                        # Convert to list of dicts for easier handling
                        if result_df is not None:
                            # Convert DataFrame to list of dicts
                            filtered_data = result_df.to_dict(orient="records")
                            state.filtered_data = filtered_data
                            print(f"Filtered data: {len(filtered_data)} records")
            except Exception as e:
                import traceback
                error = traceback.format_exc()
                print(f"Code execution error: {error}")
                
                # If there's an error and we have retries left, try again
                if state.retry_count < 3:
                    state.retry_count += 1
                    state.error = f"Code execution failed: {str(e)}"
                    # We'll handle this in the main workflow to go back to code generation
                    return state
            finally:
                # Restore stdout and pandas options
                output = mystdout.getvalue()
                sys.stdout = old_stdout
                pd.reset_option('display.max_rows')
                pd.reset_option('display.max_columns')
                pd.reset_option('display.width')
            
            # Store execution results
            state.execution_result = {
                "output": output,
                "error": error,
                "last_df_name": last_df_name
            }
            
            return state
        except Exception as e:
            print(f"Error in execute_code: {str(e)}")
            state.error = f"Error executing code: {str(e)}"
            return state
    
    # 4. Prepare context from filtered data
    def prepare_context(state: AgentState) -> AgentState:
        """
        Prepare context from the filtered data for the LLM to generate an answer.
        """
        try:
            print(f"Preparing context for query: {state.query}")
            context_parts = []
            
            # Add query to context
            context_parts.append(f"Query: {state.query}")
            
            # Add execution output if available
            if state.execution_result.get("output"):
                context_parts.append(f"Analysis output:\n{state.execution_result['output']}")
            
            # Add filtered data to context
            if state.filtered_data:
                context_parts.append(f"Filtered data ({len(state.filtered_data)} records):")
                
                # Limit to 10 records to avoid context length issues
                max_records = min(10, len(state.filtered_data))
                for i, record in enumerate(state.filtered_data[:max_records]):
                    context_parts.append(f"Record {i+1}:")
                    for key, value in record.items():
                        if value is not None:
                            context_parts.append(f"  {key}: {value}")
                
                if len(state.filtered_data) > max_records:
                    context_parts.append(f"... and {len(state.filtered_data) - max_records} more records")
            else:
                # If no filtered data, add some of the original data
                if "clinical_trials_data" in state.selected_dataframes and state.clinical_trials_data:
                    context_parts.append(f"Clinical trials data ({len(state.clinical_trials_data)} records):")
                    for i, trial in enumerate(state.clinical_trials_data[:5]):
                        context_parts.append(f"Trial {i+1}:")
                        for key in ['nctId', 'briefTitle', 'conditions', 'overallStatus', 'organization']:
                            if key in trial and trial[key]:
                                context_parts.append(f"  {key}: {trial[key]}")
                
                if "fda_data" in state.selected_dataframes and state.fda_data:
                    context_parts.append(f"FDA data ({len(state.fda_data)} records):")
                    for i, drug in enumerate(state.fda_data[:5]):
                        context_parts.append(f"Drug {i+1}:")
                        for key in ['brand_name', 'generic_name', 'manufacturer_name']:
                            if key in drug and drug[key]:
                                context_parts.append(f"  {key}: {drug[key]}")
            
            # Create context string
            context = "\n".join(context_parts)
            state.context = context
            print(f"Context prepared: {len(context)} characters")
            return state
        except Exception as e:
            print(f"Error in prepare_context: {str(e)}")
            state.error = f"Error preparing context: {str(e)}"
            return state
    
    # 5. Generate answer based on context
    def generate_answer(state: AgentState) -> AgentState:
        """
        Generate an answer to the query based on the context.
        """
        try:
            print(f"Generating answer for query: {state.query}")
            # Create the prompt template
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert healthcare analyst specializing in clinical trials and FDA data.
                Your task is to provide clear, accurate answers based on the data provided.
                
                Guidelines:
                - Answer the query based only on the provided data and analysis
                - Be specific and cite your sources
                - If the data doesn't contain enough information to answer, say so
                - Format your response in a clear, professional manner
                - Include relevant statistics or findings from the data
                """),
                ("human", "{context}\n\nQuery: {query}")
            ])
            
            # Format the prompt with the context and query
            formatted_prompt = prompt.format_messages(context=state.context, query=state.query)
            
            # Generate the answer
            response = llm.invoke(formatted_prompt)
            answer = response.content
            
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
                        source["type"] = "fda_data"
                        source["id"] = record.get("product_ndc", "Unknown")
                        source["name"] = record.get("brand_name", "Unknown Drug")
                    
                    if source:
                        sources.append(source)
            
            # Update state
            state.answer = answer
            state.sources = sources
            print(f"Answer generated: {len(answer)} characters, {len(sources)}")
            return state
        except Exception as e:
            print(f"Error in generate_answer: {str(e)}")
            state.error = f"Error generating answer: {str(e)}"
            # Provide a fallback answer
            state.answer = f"I'm sorry, I encountered an error while generating an answer: {str(e)}. Please try rephrasing your question."
            return state
    
    # Add nodes to the workflow
    workflow.add_node("select_dataframes", select_dataframes)
    workflow.add_node("generate_code", generate_code)
    workflow.add_node("execute_code", execute_code)
    workflow.add_node("prepare_context", prepare_context)
    workflow.add_node("generate_answer", generate_answer)
    
    # Define the edges
    workflow.add_edge("select_dataframes", "generate_code")
    workflow.add_edge("generate_code", "execute_code")
    workflow.add_edge("execute_code", "prepare_context")
    workflow.add_edge("prepare_context", "generate_answer")
    workflow.add_edge("generate_answer", END)
    
    # Set the entry point
    workflow.set_entry_point("select_dataframes")
    
    # Compile the workflow
    compiled_workflow = workflow.compile()
    print("Workflow compiled successfully")
    
    # Return the compiled workflow
    return compiled_workflow

async def process_chat_query(
    query: str,
    clinical_trials_data: Optional[List[Dict[str, Any]]] = None,
    fda_data: Optional[List[Dict[str, Any]]] = None,
    chat_history: Optional[List[Dict[str, Any]]] = None
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Process a chat query using the LangGraph agent.
    
    Args:
        query: The user's query.
        clinical_trials_data: Clinical trials data for context.
        fda_data: FDA data for context.
        chat_history: Previous chat messages.
        
    Returns:
        Tuple[str, List[Dict[str, Any]]]: The answer and sources.
        
    Raises:
        Exception: If processing fails.
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
        print("Creating chat agent...")
        agent = create_chat_agent()
        
        # Initialize state
        print(f"Initializing agent state with query: {query}")
        print(f"Data provided: {len(clinical_trials_data or [])} clinical trials, {len(fda_data or [])} FDA records")
        
        initial_state = AgentState(
            query=query,
            clinical_trials_data=clinical_trials_data or [],
            fda_data=fda_data or [],
            chat_history=processed_history or []
        )
        
        # Run the agent
        print(f"Running agent for query: {query}")
        
        # Invoke the full LangGraph workflow
        try:
            final_state = agent.invoke(initial_state)
            print("Agent execution completed successfully")
            print(f"Final state: {type(final_state)}")
            
            # Extract answer and sources from the AddableValuesDict
            # Access dictionary-style instead of attribute-style
            answer = final_state.get("answer", "")
            sources = final_state.get("sources", [])
            
            print(f"Extracted from final state - Answer: {answer[:50] if answer else ''}..., Sources: {len(sources) if sources else 0}")
            
            # Fallback if no answer
            if not answer:
                print("No answer found in final state, using fallback")
                answer = (
                    f"I analyzed the data related to your query about '{query}'. "
                    f"There are {len(clinical_trials_data or [])} clinical trials and {len(fda_data or [])} FDA records available. "
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
