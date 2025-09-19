
import asyncio
import os
import google.auth
from google.genai import types
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.bigquery import BigQueryCredentialsConfig, BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode
from google.adk.tools import google_search   # built-in Google Search tool


from app.bq_agent import usda_bigquery_agent
from app.allergen_agent import allergen_research_agent


_, project_id = google.auth.default()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")

MODEL = "gemini-2.5-flash"


MAIN_AGENT_INSTRUCTIONS="""
You are a friendly food and nutrician agent.
Answer questions related to food, nutrician, allergies, dietary health, and other inquiries related to thise things.
You have 2 helper agents.
- The usda_bigquery_agent has access to a large database from the USDA containing all sorts to food-related information.
- The allergen_research agent can search the Allergen Online web site for allergy-related information.
"""

root_agent = Agent(
    name="main_agent",
    model=MODEL,
    description="Provides Answers to Users Food and Allergy Questions.",
    instruction=MAIN_AGENT_INSTRUCTIONS,
    sub_agents=[usda_bigquery_agent, allergen_research_agent],
)