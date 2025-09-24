from bs4 import BeautifulSoup
from google.adk.agents import Agent
from google.adk.tools import VertexAiSearchTool
from google.genai import types
from google.adk.tools import google_search 


# ---- Agent that uses Allergy Online webite Data Store ----
INSTR = f"""
You are an allergen researcher. 
Also, use your own knowledge about allergies and health.
"""

MODEL = "gemini-2.5-flash"
# DATASTORE_PATH = "projects/cool-benefit-472616-t9/locations/global/collections/default_collection/dataStores/allergen-online-ds_1758649979142"
# vertex_search_tool = VertexAiSearchTool(data_store_id=DATASTORE_PATH)

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
        #google_search
    ],  
    generate_content_config=agent_generation,
)
