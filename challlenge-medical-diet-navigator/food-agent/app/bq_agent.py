# @title Build the BigQuery Agent. Uses the BigQuery tool to access the BQ Dataset created earlier

# @title ADK Imports
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

from .bq_schema import DB_SCHEMA
from .config import Config

PROJECT_ID = Config.GOOGLE_CLOUD_PROJECT
DATASET_NAME = Config.DATASET_NAME
MODEL = Config.MODEL

# Uses Application Default Credentials for BigQuery (gcloud or service account).
adc, _ = google.auth.default()
bq_credentials = BigQueryCredentialsConfig(credentials=adc)

# Read-only tool config (blocks DDL/DML). You can change to WriteMode.ALLOWED later if needed.
bq_tool_cfg = BigQueryToolConfig(write_mode=WriteMode.BLOCKED)

# Instantiate the BigQuery toolset
bq_tools = BigQueryToolset(
    credentials_config=bq_credentials,
    bigquery_tool_config=bq_tool_cfg
)

# Instruct the agent to **only** use your dataset
INSTR = f"""
You are a data analysis agent with access to BigQuery tools.
The dataset you have access to contains information from the USDA about foods and nutrician information.
Only query the dataset `{PROJECT_ID}.{DATASET_NAME}`.
Fully qualify every table as `{PROJECT_ID}.{DATASET_NAME}.<table>`.
Never perform DDL/DML; SELECT-only. Return the SQL you ran along with a concise answer.
Here is the database schema, please study it {DB_SCHEMA}
"""

agent_generation = types.GenerateContentConfig(
    temperature=0.6,
    top_p=0.9,
    max_output_tokens=32768,
)  


usda_bigquery_agent = Agent(
    model=MODEL,         # Works with ADK; requires a Gemini API key or Vertex AI setup
    name="usda_food_information_bigquery_agent",
    description="""Analyzes tables in a BigQuery dataset that contains food information from the USDA. Tables.""",
    instruction=INSTR,
    tools=[bq_tools],
    generate_content_config=agent_generation,
)