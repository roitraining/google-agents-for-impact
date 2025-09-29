
import os
import google.auth
from google.genai import types
from google.adk.agents import Agent
from google.adk.tools import agent_tool

from app.bq_agent import usda_bigquery_agent
from app.allergen_agent import allergen_research_agent
from app.image_agent import image_agent


_, project_id = google.auth.default()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")

MODEL = "gemini-2.5-flash"

agent_generation = types.GenerateContentConfig(
    temperature=0.6,
    top_p=0.9,
    max_output_tokens=32768,
)  


MAIN_AGENT_INSTRUCTIONS="""
You are a friendly food and nutrician agent.
Answer questions related to food, nutrician, allergies, dietary health, and other inquiries related to thise things.
You have 2 helper agents.
- The usda_bigquery_agent has access to a large database from the USDA containing all sorts to food-related information.
- The image_agent generate images if requested
You can use your tool to search for information about allergies and related health concerns online.
When you use the Google Search tool, always cite the source of the information you find.
"""

root_agent = Agent(
    name="main_agent",
    model=MODEL,
    description="Provides Answers to Users Food and Allergy Questions.",
    instruction=MAIN_AGENT_INSTRUCTIONS,
    tools=[agent_tool.AgentTool(agent=allergen_research_agent)],
    sub_agents=[usda_bigquery_agent, image_agent],
    generate_content_config=agent_generation,
)