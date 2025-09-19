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

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
DATASET_NAME = "fda_dataset"

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

DB_SCHEMA = """

[{
  "table_name": "lab_method_nutrient",
  "fields": [{
    "column_name": "lab_method_id",
    "data_type": "INT64"
  }, {
    "column_name": "nutrient_id",
    "data_type": "INT64"
  }]
}, {
  "table_name": "food_update_log_entry",
  "fields": [{
    "column_name": "id",
    "data_type": "INT64"
  }, {
    "column_name": "description",
    "data_type": "STRING"
  }, {
    "column_name": "last_updated",
    "data_type": "DATE"
  }]
}, {
  "table_name": "input_food",
  "fields": [{
    "column_name": "id",
    "data_type": "INT64"
  }, {
    "column_name": "fdc_id",
    "data_type": "INT64"
  }, {
    "column_name": "fdc_of_input_food",
    "data_type": "INT64"
  }, {
    "column_name": "seq_num",
    "data_type": "STRING"
  }, {
    "column_name": "amount",
    "data_type": "STRING"
  }, {
    "column_name": "ingredient_code",
    "data_type": "STRING"
  }, {
    "column_name": "ingredient_description",
    "data_type": "STRING"
  }, {
    "column_name": "unit",
    "data_type": "STRING"
  }, {
    "column_name": "portion_code",
    "data_type": "STRING"
  }, {
    "column_name": "portion_description",
    "data_type": "STRING"
  }, {
    "column_name": "gram_weight",
    "data_type": "STRING"
  }, {
    "column_name": "retention_code",
    "data_type": "STRING"
  }]
}, {
  "table_name": "sub_sample_food",
  "fields": [{
    "column_name": "fdc_id",
    "data_type": "INT64"
  }, {
    "column_name": "fdc_id_of_sample_food",
    "data_type": "INT64"
  }]
}, {
  "table_name": "food",
  "fields": [{
    "column_name": "fdc_id",
    "data_type": "INT64"
  }, {
    "column_name": "data_type",
    "data_type": "STRING"
  }, {
    "column_name": "description",
    "data_type": "STRING"
  }, {
    "column_name": "food_category_id",
    "data_type": "INT64"
  }, {
    "column_name": "publication_date",
    "data_type": "DATE"
  }]
}, {
  "table_name": "foundation_food",
  "fields": [{
    "column_name": "fdc_id",
    "data_type": "INT64"
  }, {
    "column_name": "NDB_number",
    "data_type": "INT64"
  }, {
    "column_name": "footnote",
    "data_type": "STRING"
  }]
}, {
  "table_name": "market_acquisition",
  "fields": [{
    "column_name": "fdc_id",
    "data_type": "INT64"
  }, {
    "column_name": "brand_description",
    "data_type": "STRING"
  }, {
    "column_name": "expiration_date",
    "data_type": "DATE"
  }, {
    "column_name": "label_weight",
    "data_type": "STRING"
  }, {
    "column_name": "location",
    "data_type": "STRING"
  }, {
    "column_name": "acquisition_date",
    "data_type": "DATE"
  }, {
    "column_name": "sales_type",
    "data_type": "STRING"
  }, {
    "column_name": "sample_lot_nbr",
    "data_type": "STRING"
  }, {
    "column_name": "sell_by_date",
    "data_type": "DATE"
  }, {
    "column_name": "store_city",
    "data_type": "STRING"
  }, {
    "column_name": "store_name",
    "data_type": "STRING"
  }, {
    "column_name": "store_state",
    "data_type": "STRING"
  }, {
    "column_name": "upc_code",
    "data_type": "STRING"
  }]
}, {
  "table_name": "food_protein_conversion_factor",
  "fields": [{
    "column_name": "food_nutrient_conversion_factor_id",
    "data_type": "INT64"
  }, {
    "column_name": "value",
    "data_type": "FLOAT64"
  }]
}, {
  "table_name": "lab_method_code",
  "fields": [{
    "column_name": "lab_method_id",
    "data_type": "INT64"
  }, {
    "column_name": "code",
    "data_type": "STRING"
  }]
}, {
  "table_name": "food_nutrient_conversion_factor",
  "fields": [{
    "column_name": "id",
    "data_type": "INT64"
  }, {
    "column_name": "fdc_id",
    "data_type": "INT64"
  }]
}, {
  "table_name": "food_calorie_conversion_factor",
  "fields": [{
    "column_name": "food_nutrient_conversion_factor_id",
    "data_type": "INT64"
  }, {
    "column_name": "protein_value",
    "data_type": "FLOAT64"
  }, {
    "column_name": "fat_value",
    "data_type": "FLOAT64"
  }, {
    "column_name": "carbohydrate_value",
    "data_type": "FLOAT64"
  }]
}, {
  "table_name": "food_portion",
  "fields": [{
    "column_name": "id",
    "data_type": "INT64"
  }, {
    "column_name": "fdc_id",
    "data_type": "INT64"
  }, {
    "column_name": "seq_num",
    "data_type": "INT64"
  }, {
    "column_name": "amount",
    "data_type": "FLOAT64"
  }, {
    "column_name": "measure_unit_id",
    "data_type": "INT64"
  }, {
    "column_name": "portion_description",
    "data_type": "STRING"
  }, {
    "column_name": "modifier",
    "data_type": "STRING"
  }, {
    "column_name": "gram_weight",
    "data_type": "FLOAT64"
  }, {
    "column_name": "data_points",
    "data_type": "INT64"
  }, {
    "column_name": "footnote",
    "data_type": "STRING"
  }, {
    "column_name": "min_year_acquired",
    "data_type": "INT64"
  }]
}, {
  "table_name": "sample_food",
  "fields": [{
    "column_name": "fdc_id",
    "data_type": "INT64"
  }]
}, {
  "table_name": "lab_method",
  "fields": [{
    "column_name": "id",
    "data_type": "INT64"
  }, {
    "column_name": "description",
    "data_type": "STRING"
  }, {
    "column_name": "technique",
    "data_type": "STRING"
  }]
}, {
  "table_name": "nutrient",
  "fields": [{
    "column_name": "id",
    "data_type": "INT64"
  }, {
    "column_name": "name",
    "data_type": "STRING"
  }, {
    "column_name": "unit_name",
    "data_type": "STRING"
  }, {
    "column_name": "nutrient_nbr",
    "data_type": "FLOAT64"
  }, {
    "column_name": "rank",
    "data_type": "FLOAT64"
  }]
}, {
  "table_name": "food_nutrient",
  "fields": [{
    "column_name": "id",
    "data_type": "INT64"
  }, {
    "column_name": "fdc_id",
    "data_type": "INT64"
  }, {
    "column_name": "nutrient_id",
    "data_type": "INT64"
  }, {
    "column_name": "amount",
    "data_type": "FLOAT64"
  }, {
    "column_name": "data_points",
    "data_type": "INT64"
  }, {
    "column_name": "derivation_id",
    "data_type": "INT64"
  }, {
    "column_name": "min",
    "data_type": "FLOAT64"
  }, {
    "column_name": "max",
    "data_type": "FLOAT64"
  }, {
    "column_name": "median",
    "data_type": "FLOAT64"
  }, {
    "column_name": "footnote",
    "data_type": "STRING"
  }, {
    "column_name": "min_year_acquired",
    "data_type": "INT64"
  }]
}, {
  "table_name": "measure_unit",
  "fields": [{
    "column_name": "id",
    "data_type": "INT64"
  }, {
    "column_name": "name",
    "data_type": "STRING"
  }]
}, {
  "table_name": "acquisition_samples",
  "fields": [{
    "column_name": "fdc_id_of_sample_food",
    "data_type": "INT64"
  }, {
    "column_name": "fdc_id_of_acquisition_food",
    "data_type": "INT64"
  }]
}, {
  "table_name": "agricultural_samples",
  "fields": [{
    "column_name": "fdc_id",
    "data_type": "INT64"
  }, {
    "column_name": "acquisition_date",
    "data_type": "DATE"
  }, {
    "column_name": "market_class",
    "data_type": "STRING"
  }, {
    "column_name": "treatment",
    "data_type": "STRING"
  }, {
    "column_name": "state",
    "data_type": "STRING"
  }]
}, {
  "table_name": "sub_sample_result",
  "fields": [{
    "column_name": "food_nutrient_id",
    "data_type": "INT64"
  }, {
    "column_name": "adjusted_amount",
    "data_type": "FLOAT64"
  }, {
    "column_name": "lab_method_id",
    "data_type": "INT64"
  }, {
    "column_name": "nutrient_name",
    "data_type": "STRING"
  }]
}, {
  "table_name": "food_attribute_type",
  "fields": [{
    "column_name": "id",
    "data_type": "INT64"
  }, {
    "column_name": "name",
    "data_type": "STRING"
  }, {
    "column_name": "description",
    "data_type": "STRING"
  }]
}, {
  "table_name": "food_category",
  "fields": [{
    "column_name": "id",
    "data_type": "INT64"
  }, {
    "column_name": "code",
    "data_type": "INT64"
  }, {
    "column_name": "description",
    "data_type": "STRING"
  }]
}, {
  "table_name": "food_attribute",
  "fields": [{
    "column_name": "id",
    "data_type": "INT64"
  }, {
    "column_name": "fdc_id",
    "data_type": "INT64"
  }, {
    "column_name": "seq_num",
    "data_type": "INT64"
  }, {
    "column_name": "food_attribute_type_id",
    "data_type": "INT64"
  }, {
    "column_name": "name",
    "data_type": "STRING"
  }, {
    "column_name": "value",
    "data_type": "STRING"
  }]
}, {
  "table_name": "food_component",
  "fields": [{
    "column_name": "id",
    "data_type": "INT64"
  }, {
    "column_name": "fdc_id",
    "data_type": "STRING"
  }, {
    "column_name": "name",
    "data_type": "STRING"
  }, {
    "column_name": "pct_weight",
    "data_type": "FLOAT64"
  }, {
    "column_name": "is_refuse",
    "data_type": "BOOL"
  }, {
    "column_name": "gram_weight",
    "data_type": "FLOAT64"
  }, {
    "column_name": "data_points",
    "data_type": "INT64"
  }, {
    "column_name": "min_year_acqured",
    "data_type": "INT64"
  }]
}]
"""

# Instruct the agent to **only** use your dataset
INSTR = f"""
You are a data analysis agent with access to BigQuery tools.
The dataset you have access to contains information from the USDA about foods and nutrician information.
Only query the dataset `{PROJECT_ID}.{DATASET_NAME}`.
Fully qualify every table as `{PROJECT_ID}.{DATASET_NAME}.<table>`.
Never perform DDL/DML; SELECT-only. Return the SQL you ran along with a concise answer.
Here is the database schema, please study it {DB_SCHEMA}
"""

MODEL = "gemini-2.5-flash"

usda_bigquery_agent = Agent(
    model=MODEL,         # Works with ADK; requires a Gemini API key or Vertex AI setup
    name="usda_food_information_bigquery_agent",
    description="""Analyzes tables in a BigQuery dataset that contains food information from the USDA. Tables.""",
    instruction=INSTR,
    tools=[bq_tools],
)