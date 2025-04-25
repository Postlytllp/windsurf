
import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Tuple, Optional
from io import StringIO
import pandas as pd
import re
from dataclasses import dataclass
from typing import TypedDict, Annotated
from langchain_core.messages import AnyMessage
from langchain_core.commands import Command
from typing import Literal

#This a code snippet example for streamlit chatbot to query WHOLE the clinical trials and FDA data

# Chat input
if prompt := st.chat_input("Ask your clinical trial analysis question:"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    llm = ChatOpenAI(model="gpt-4.1")

    # Prepare the graph state   
    @dataclass(frozen=True)
    class MessageState(TypedDict):
        messages:Annotated[list[AnyMessage], add_messages]
        code: str
        result: str
        retry_count: int
        next: str
        dfs: list[str]
        out_df: dict
        summary: str
        last_df_name: str
        last_q: str
        # last_a: str
        pass

    class df_selection(TypedDict):
        """Dataframe selection: Choose one or more dataframes to query from."""
        df: list[Literal["clinical_trials_df", "FDA_drugs_df"]]  # Now df is a LIST

    

    def select_dataframe(state: MessageState) -> Command[Literal["generate_code"]]:
        """Dataframe selection node: Choose the dataframe(s) to query from."""

        dataframes = ["clinical_trials_df", "FDA_drugs_df"]

        df_selection_prompt = f"""Your task is to select relevant dataframes from {dataframes} based on the user query: 
                                {state['messages'][-1]}. 
                                - Choose either one or both dataframes as needed.
                                - If the query requires information from both, return both in a list.
        """

        messages = [
            {"role": "system", "content": df_selection_prompt},
        ] + state["messages"]

        response = llm.with_structured_output(df_selection).invoke(messages)

        dfs = response["df"]

        # Ensure dfs is always a list (even if the model returns a single string)
        if isinstance(dfs, str):
            dfs = [dfs]

        return Command(goto="generate_code", update={"dfs": dfs})

    # Define the workflow functions
    def generate_code(state: MessageState) -> Command[Literal["agent"]]:
        # client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        
        # Mapping of dataframe names to actual dataframes
        df_mapping = {
            "clinical_trials_df": st.session_state.df_ct,
            "FDA_drugs_df": st.session_state.df_fda
        }

        # Ensure we get the actual dataframes from the selected names
        data = [df_mapping[name] for name in state['dfs'] if name in df_mapping]
        # print(f'The lenth of data is: {len(data)}')
        
        # clinical_trial_context = clinical_trial_context.format(data_head=st.session_state.df_ct.head(3))
        # print(clinical_trial_context)
        # fda_context = fda_context.format(info=st.session_state.df_fda.info())

        if len(data)==1:
            # Determine the available variables
            available_variables = (
                list(data.columns) if isinstance(data, pd.DataFrame) else
                (list(data.keys()) if isinstance(data, dict) else 'N/A')
            )
            if state['dfs'][0] =='clinical_trials_df':
                data_context = str(clinical_trial_context + "\n" + st.session_state.df_ct.head(3).to_string())
            elif state['dfs'][0] == 'FDA_drugs_df':
                data_context = fda_context
        else:
            data_context = fda_context + clinical_trial_context
            # Extract column names from each dataframe
            available_variables = {
                name: list(df.columns) for name, df in zip(state['dfs'], data) if isinstance(df, pd.DataFrame)
            }

        # available_variables = list(st.session_state.df.columns)

        user_message =  f"""Task: {state['messages'][-1]}
            Available variables: {available_variables}
            Dataframes available: {state['dfs']}
            My last question: {state.get('last_q', None)}
            Your last answer: {state.get('summary',None)}
            """
        print(f"Last question was:  {state.get('last_q', None)}")
        print(f"*********************************Last Answer was was:  {state.get('summary', None)}")

        # Error-based rectification request
        user_message_rectify = f"""The previous code:
            {state['code'] if isinstance(state.get('code'), str) else 'N/A'}

            gave the following error:
            {state['result']['error'] if isinstance(state.get('result', {}).get('error'), str) else 'N/A'}


            Based on the task: {state['messages'][-1]} and available variables: {available_variables},
            please fix the error while maintaining the original logic."""

        # Choose the correct prompt based on whether there's an error
        selected_message = user_message if not state.get('error') else user_message_rectify

        # chat_completion = client.chat.completions.create(
        #     messages=[
        #         {"role": "system", "content": system_prompt},
        #         {"role": "user", "content": selected_message}
        #     ],
        #     model="deepseek-r1-distill-llama-70b",
        #     temperature=0.1,
        # )

        system_prompt = f"""You are a smart and intellegent clinical trial and Food Drug Authority (FDA) Analyst. Your job is to Generate Python code that:
        - Uses only provided variables
        - Give the final dataframe from which answer to the query can be answered, and all the datafrmes in the code should have a suffix '_df
        - Includes any necessary imports
        - If fixing an error, correct the previous code while maintaining logic
        - While matching any name lower the case for the term to search and in data where to search
        - Also, try to use contains rather than exact match like ==
        -The data context is as below:
        {data_context}
        """

        messages = [
                    {
                        "role": "system",
                        "content":  system_prompt,
                    },
                    {
                        "role": "user",
                        "content": selected_message,
                    }
                ]
        summary = llm.invoke(messages)
        response = summary.content

        def clean_code_response(response):
            response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
            code_match = re.search(r'```python\n(.*?)```', response, flags=re.DOTALL)
            return code_match.group(1).strip() if code_match else response.strip()

        # response = chat_completion.choices[0].message.content
        return Command(
            update={'code': clean_code_response(response)},
            goto= "agent"
        )

    def agent(state: MessageState) -> Command[Literal["summarize_result", "__end__"]]:
        # Access global variables safely
        data = state['dfs']

        # Check for the correct string values
        if data[0] == "clinical_trials_df":
            data_df = st.session_state.df_ct
        elif data[0] == "FDA_drugs_df":
            data_df = st.session_state.df_fda
        else:
            # Use a dictionary to store both DataFrames
            data_df = {
                "clinical_trials_df": st.session_state.df_ct,
                "FDA_drugs_df": st.session_state.df_fda
            }


        def execute_python(code, data=None):
            """Executes Python code with given context and prevents pandas truncation"""

            # Set pandas display options
            pd.set_option('display.max_rows', None)
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', None)
            pd.set_option('display.max_colwidth', None)

            old_stdout = sys.stdout
            sys.stdout = StringIO()

            # Ensure df is correctly assigned in the local scope
            local_vars = {"df": data_df} if isinstance(data_df, pd.DataFrame) else data_df

            local_vars = {'pd': pd,
                            '__builtins__': __builtins__
                        }
            
            if "clinical_trials_df" in data:
                local_vars["clinical_trials_df"] = st.session_state.df_ct
            if "FDA_drugs_df" in data:
                local_vars["FDA_drugs_df"] = st.session_state.df_fda


            try:
                # Store initial variables
                initial_vars = set(local_vars.keys())

                exec(code, local_vars)

                # Find all new DataFrame variables
                new_vars = set(local_vars.keys()) - initial_vars
                df_vars = {var: local_vars[var] for var in new_vars 
                        if isinstance(local_vars[var], pd.DataFrame)}
                
                # Get the last DataFrame created (if any exist)
                result_df = None
                if df_vars:
                    # Get the last DataFrame from the execution
                    # last_df_name = list(df_vars.keys())[-1]
                    # last_df_name= max(df_vars, key=lambda var: list(local_vars.keys()).index(var)) # Get the last created DF
                    last_df_name = re.findall(r'\b\w+_df\b', code)[-1]
                    result_df = df_vars[last_df_name].to_dict(orient="records")
                    print(f"\nCapturing DataFrame: '{last_df_name}'")


                output = sys.stdout.getvalue()
                return {
                        "output": output,
                        "error": None,
                        "result_df": result_df,
                        # "all_dataframes": df_vars,  # Optional: return all DataFrames if needed
                        "last_df_name": last_df_name
                    }
            except Exception as e:
                error_trace = traceback.format_exc()
                return {
                    "output": None,
                    "error": str(error_trace),
                    "result_df": None,
                    # "all_dataframes": {},
                    "last_df_name":None
                }
            finally:
                # Reset stdout and pandas options
                sys.stdout = old_stdout
                pd.reset_option('display.max_rows')
                pd.reset_option('display.max_columns')
                pd.reset_option('display.width')
                pd.reset_option('display.max_colwidth')

        result = execute_python(state['code'], data)
        # return {"result": result}
        # Initialize retry count if not present
        retry_count = state.get("retry_count", 0)
        # st.write(f"This type of result: {type(result['output'])}")
        
        error = result.get("error", None)
        if error:
            # retry_count=1
            st.write(f"Got erorr in the code, Number of retries : {retry_count + 1}.")
            if retry_count < 3:
                retry_count += 1
                goto_agent = "generate_code"  # Retry code generation
            else:
                goto_agent = END
                st.write("Max retries reached. Stopping.")
        else:
            goto_agent = "summarize_result"

    
        return Command(
                update={"result": result,
                        "out_df": result['result_df'],
                        # "out_df": result['result_df'].to_dict(orient="records") if result.get('result_df') is not None else None,
                        "last_df_name":result['last_df_name'],
                        "retry_count": retry_count,
                        },          
                goto= goto_agent
            )

    def summarize_result(state: MessageState) -> Command[Literal[ "__end__"]]:
        """Summarize the result of the code execution to human understable language"""
        summarize_prompt = f"""Write the answer to the query from the output and ONLY IF REQUIRED to anser take help of DATA
                            - The audience is experts in lifesciences and healthcare sector
                            - The answer must provide clarity
                            - Query: {state['messages'][-1]}
                            - Output: {state['result']['output']}
                            - Data: {state['out_df']}
                            """

        llm = ChatOpenAI(model="gpt-4.1",  max_tokens=None)

        messages = [
            (
                "system",
                "You are a good at answering and summarizing results. Summarize results of data based on the user's query.",
            ),
            ("human", summarize_prompt),
        ]

        # summary = llm.invoke(messages)
        # summary_text = summary.content
        try:
            summary = llm.invoke(messages)
            summary_text = summary.content

        except openai.OpenAIError as e:  # Catch OpenAI errors
            error_message = str(e)
            if "Request too large" in error_message or "rate_limit_exceeded" in error_message:
                summary_text= "⚠️ **Data too long to summarize. Please refer to the data above for the answer.**"
            else:
                summary_text= "⚠️ **An error occurred while generating the summary. Please try again.**"

        except LangChainException as e:
            if getattr(e, "error_code", None) == ErrorCode.MODEL_RATE_LIMIT:
                summary_text="⚠️ **Data too long to summarize. Please refer to the data above for the answer.**"
            else:
                summary_text="⚠️ **An unexpected error occurred. Please ask question differently.**"
            return None  # Ensure graceful handling
        
        
        return Command(
            update={"messages": AIMessage(content=summary_text)
                    # "messages": summary_text    
            },
            goto= END,
        )

    # Build and run the graph
    builder = StateGraph(MessageState)
    builder.add_edge(START, "select_dataframe")
    builder.add_node("select_dataframe", select_dataframe)
    builder.add_node("generate_code", generate_code)
    builder.add_node("agent", agent)
    builder.add_node("summarize_result", summarize_result)
    graph = builder.compile(checkpointer=memory)

    if 'session_key' not in st.session_state:
        st.session_state['session_key'] = str(uuid.uuid4())

    # Use the session key as the thread ID
    thread_id = st.session_state['session_key']

    # Specify a consistent thread for each session
    config = {"configurable": {"thread_id": thread_id}}

    # Invoke the graph
    answer = graph.invoke({
                "messages": [HumanMessage(content=prompt)],
                "code": "",
                "result": {},
                "retry_count": 0,  # Initialize retry count
                "next": "",  # Define the next step (empty for now)
                "dfs": [],  # Initialize as an empty list
                "out_df": None, # Initialize out_df to None or an empty DataFrame
                "last_df_name":"",  
            },
            config,
            stream_mode="values",
            )