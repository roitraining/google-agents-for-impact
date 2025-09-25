from bs4 import BeautifulSoup
from google.adk.agents import Agent
from google.adk.tools import VertexAiSearchTool
from google.genai import types
from google.adk.tools import google_search 


# ---- Agent that uses Allergy Online webite Data Store ----
INSTR = f"""
You are an allergen researcher. 
Also, use your own knowledge about allergies and health.
You can also use the Google Search tool to find relevant information on the web.
When you use the Google Search tool, always cite the source of the information you find.
"""

MODEL = "gemini-2.5-flash"

agent_generation = types.GenerateContentConfig(
    temperature=0.6,
    top_p=0.9,
    max_output_tokens=32768,
)  

allergen_research_agent = Agent(
    model=MODEL,   # or your preferred Gemini model
    name="allergy_research_agent",
    description=f"Answer questions about allergies and related health concerns.",
    instruction=INSTR,
    tools=[
        google_search
    ],  
    generate_content_config=agent_generation,
)
