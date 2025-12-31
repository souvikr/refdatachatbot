import os
import asyncio
import gradio as gr
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from pydantic import create_model, Field

# Load environment variables
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import create_react_agent
from langgraph.graph import MessagesState

# MCP Imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Constants
SERVER_SCRIPT = "server.py"

def get_mcp_server_params() -> StdioServerParameters:
    """Returns the parameters to start the MCP server."""
    return StdioServerParameters(
        command="uv",
        args=["run", "fastmcp", "run", SERVER_SCRIPT],
        env=os.environ.copy() # Inherit environment variables
    )

async def convert_mcp_tools(session: ClientSession) -> List[StructuredTool]:
    """
    Query the MCP server for tools and convert them to LangChain StructuredTools.
    """
    mcp_tools_list = await session.list_tools()
    langchain_tools = []

    for tool in mcp_tools_list.tools:
        # We need to capture the specific tool name in the closure
        tool_name = tool.name
        
        # Capture tool_name by value using a default argument or a factory
        # Using a factory method to be cleaner and safer
        def create_wrapper(t_name: str):
            async def _wrapper(**kwargs) -> str:
                print(f"[DEBUG] Calling tool: {t_name} with args: {kwargs}")
                try:
                    result = await session.call_tool(t_name, arguments=kwargs)
                    text_output = []
                    if hasattr(result, 'content'):
                        for item in result.content:
                            if hasattr(item, 'text'):
                                text_output.append(item.text)
                            else:
                                print(f"[DEBUG] Unknown content item: {item}")
                    output = "\n".join(text_output)
                    print(f"[DEBUG] Tool {t_name} output: {output[:200]}...") 
                    return output
                except Exception as e:
                    print(f"[ERROR] Tool {t_name} failed: {e}")
                    raise e
            return _wrapper
            
        tool_wrapper = create_wrapper(tool_name)



        # Dynamic Schema Generation for Pydantic
        # This bridges the gap so the LLM knows what arguments to expect.
        input_schema = tool.inputSchema
        fields = {}
        
        if 'properties' in input_schema:
            for prop_name, prop_def in input_schema['properties'].items():
                prop_type = str  # Default to string for simplicity as most args are strings here
                # We could map 'integer' -> int, 'number' -> float, 'boolean' -> bool etc if needed
                
                description = prop_def.get('description', '')
                
                # Check if required
                if 'required' in input_schema and prop_name in input_schema['required']:
                    fields[prop_name] = (prop_type, Field(description=description))
                else:
                    fields[prop_name] = (Optional[prop_type], Field(default=None, description=description))
        
        # Create the Pydantic model
        ArgsModel = create_model(f"{tool.name}Args", **fields)

        # Create the StructuredTool with the explicit args_schema
        lc_tool = StructuredTool.from_function(
            func=None,
            coroutine=tool_wrapper,
            name=tool.name,
            description=tool.description or f"Tool named {tool.name}",
            args_schema=ArgsModel
        )
        
        langchain_tools.append(lc_tool)

    return langchain_tools

from prompts import INTENT_VALIDATION_PROMPT

async def validate_intent(message: str) -> bool:
    """
    Validates if the user query is related to finance or reference data.
    Returns True if valid, False otherwise.
    """
    prompt = INTENT_VALIDATION_PROMPT.format(message=message)
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    response = await llm.ainvoke(prompt)
    content = response.content.strip().upper()
    return "YES" in content

async def run_agent_interaction(message: str, history: List[Any]):
    """
    Main handler for the chat interface.
    Connects to MCP, builds agent, and runs the query with streaming updates.
    """
    # 1. Check API Key
    if "OPENAI_API_KEY" not in os.environ:
        yield "⚠️ OPENAI_API_KEY is missing from environment variables! Please set it."
        return

    # 2. Intent Check
    yield "🔍 Analyzing intent..."
    is_valid = await validate_intent(message)
    
    if not is_valid:
        yield "❌ **Request Rejected**: Your query does not appear to be related to financial reference data. Please ask about bonds, issuers, or credit ratings."
        return

    yield "✅ Intent verified. Processing..."

    # 3. Connect to MCP Server 
    server_params = get_mcp_server_params()
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # 4. Get and bind Tools
                tools = await convert_mcp_tools(session)
                
                # 5. Initialize LLM & Agent
                llm = ChatOpenAI(model="gpt-4o", temperature=0)
                agent_executor = create_react_agent(llm, tools)
                
                # 6. Run Agent with Streaming
                # We retain the accumulated response to append to it
                accumulated_response = ""
                
                async for event in agent_executor.astream_events(
                    {"messages": [("user", message)]},
                    version="v1"
                ):
                    kind = event["event"]
                    
                    if kind == "on_tool_start":
                        tool_name = event['name']
                        tool_input = event['data'].get('input')
                        accumulated_response += f"\n\n🛠️ **Calling Tool**: `{tool_name}`\nArgs: `{tool_input}`\n"
                        yield accumulated_response
                        
                    elif kind == "on_tool_end":
                        tool_name = event['name']
                        accumulated_response += f"✅ **Tool `{tool_name}` Finished**\n"
                        yield accumulated_response

                    elif kind == "on_chat_model_stream":
                        content = event['data']['chunk'].content
                        if content:
                            accumulated_response += content
                            yield accumulated_response
                            
    except Exception as e:
        yield f"Error: {str(e)}"

# UI Layout
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("## 🏦 Agentic Financial RAG")
    
    with gr.Accordion("📖 How to use", open=True):
        gr.Markdown("""
        - Ask questions about bonds, issuers, and ratings.
        - The agent connects to a local **MCP Server** (`server.py`) powered by `finance.db`.
        - It can look up ISIN details, search for issuers, and find credit ratings.
        """)
        
    chat = gr.ChatInterface(
        fn=run_agent_interaction,
        # type="messages", # Removed as it caused unexpected keyword argument error
        examples=[
            "Who is the issuer for ISIN US912810TS08?", 
            "Find the rating for Apple's bond US037833AS99.",
            "Search for issuers with 'Treasury' in their name."
        ]
    )
    
    gr.Markdown("### Powered by LangGraph & MCP")

if __name__ == "__main__":
    demo.launch()
