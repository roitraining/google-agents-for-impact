# Agents for Impact — Project Chronicle: Medical Diet Navigator (Sample Implementation)

A **demo-ready, end-to-end example** showing how to build a medically-aware “food as medicine” assistant using **Google’s Agent Development Kit (ADK)**, **Agent Engine**, **BigQuery**, and a lightweight **Flask** front end.

> ⚠️ This repository is NOT intended as *the* canonical solution. It’s a clear, opinionated **reference implementation** that facilitators and hackers can run and adapt during the *Agents for Impact* hackathon.

---

## Challenge Context

Millions of Americans with chronic conditions (e.g., **diabetes**, **Celiac**, **severe allergies**) must treat **food as medicine**—constantly inspecting labels, menus, and recipes. One slip can have serious consequences.

**Mission:** Build an AI-powered *guardian* that reduces cognitive load and risk by providing **precise, personalized dietary guidance**.

**Suggested data sources:**

- **USDA FoodData Central (FDC):** comprehensive nutrient data by the U.S. Department of Agriculture.  
- **FARRP AllergenOnline:** peer-reviewed allergen information curated by UNL’s FARRP program.

> In this sample, FDC is loaded into **BigQuery**; the agent can query it and combine results with additional tools (e.g., web lookups, allergen reference checks) to produce actionable advice.

---

## Repository Structure

```
/
├─ colab-notebooks/         # Colab Enterprise notebooks for data import and agent smoke tests
├─ food-agent/              # ADK Starter Pack–based agent (tools, prompts, orchestration)
└─ nutritian-flask-app/     # Flask web app that calls the deployed Agent Engine endpoint
```

> Note: Folder names above reflect this sample’s structure. If you fork/rename, update paths accordingly.

---

## High-Level Architecture

```
[Colab Notebooks] ──► [BigQuery: FDC dataset] ──┐
                                                │
                              [ADK Agent + Tools] ──► [Agent Engine Deployment]
                                                │
                             [Flask Web App (UI)] ◄──┘  (invokes deployed agent)
```

- **Data layer:** BigQuery hosts the **FoodData Central** tables for fast SQL queries.
- **Reasoning layer (Agent):** An ADK agent with tools (e.g., BigQuery, search) plans multi-step answers.
- **Serving layer:** The agent is deployed to **Agent Engine**; the Flask app invokes it via API.
- **UI layer:** A simple web front end that demonstrates user interaction and result rendering.

---

## Quick Start (End-to-End)

### 0) Prerequisites

- **Google Cloud** project with billing enabled.
- **BigQuery** and permissions to create datasets/tables.
- **Vertex AI & Agent Engine** enabled (plus ADK access).
- **Colab Enterprise** access (recommended) OR local notebooks runtime.
- Local dev:
  - **Python 3.10+**
  - `gcloud` CLI (authenticated to your project)
  - Optional: `uv`/`pip`/`venv` or `poetry` for dependency management

> Make sure your default `gcloud` project is set:  
> `gcloud config set project YOUR_PROJECT_ID`

---

### 1) Load FoodData Central into BigQuery (via Colab)

1. Open `colab-notebooks/` and run the **data import** notebook(s).
2. Configure:
   - **PROJECT_ID**
   - **BQ_DATASET** (e.g., `fdc_dataset`)
   - Optional **GCS_BUCKET** if staging files
3. Run all cells to:
   - Download/unzip the USDA FDC CSV bundle
   - Create the BigQuery dataset and tables
   - Load CSVs into BigQuery
   - (Optional) Run validation queries

> Result: You’ll have a populated **BigQuery dataset** with nutrient information the agent can query.

---

### 2) Configure & Deploy the Agent (ADK)

From `food-agent/`:

1. **Install deps** (choose your toolchain):
   ```bash
   # using venv + pip
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt

   # or using uv (alternative fast installer)
   uv venv && source .venv/bin/activate
   uv pip install -r requirements.txt

   # or using poetry
   poetry install
   ```
2. **Set environment/config** values (example):
   - `PROJECT_ID`, `LOCATION` (e.g., `us-central1`)
   - `BQ_DATASET` (e.g., `fdc_dataset`)
   - Any tool credentials (if using external APIs)
3. **Run locally** (optional) to smoke test:
   ```bash
   python -m app.main   # or the equivalent entrypoint for this starter
   ```
4. **Deploy to Agent Engine** (exact command depends on the Starter Pack wiring in this folder):
   - Either a provided script (e.g., `scripts/deploy.sh`)
   - Or an ADK/Agent Engine CLI invocation
   - Capture/record the **Agent ID** or **endpoint** after deploy

> Result: An **Agent Engine** endpoint (or agent resource) that the Flask app can invoke.

---

### 3) Run the Flask Web App

From `nutritian-flask-app/`:

1. **Install deps** and create your local env:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Configure environment variables** (example):
   ```bash
   export PROJECT_ID=YOUR_PROJECT_ID
   export LOCATION=us-central1
   export AGENT_ID=YOUR_DEPLOYED_AGENT_ID_OR_ENDPOINT
   export BQ_DATASET=fdc_dataset
   # add any required auth/config for your setup
   ```
3. **Run the app**:
   ```bash
   flask run  # or: python -m app, or: gunicorn app:app
   ```
4. Open the app in your browser, ask questions like:
   - “I’m allergic to peanuts—does this recipe trigger any concerns?”
   - “Show high-protein options under 400 calories per serving.”
   - “Help me choose a gluten-free lunch with 30g protein.”

---

## Demo Scenarios (Examples)

- **Allergen safety check:** Paste an ingredient list or menu item; the agent flags risks referencing allergen data and nutrient facts.
- **Macronutrient targeting:** Ask for meal suggestions by protein/carb/fat ranges; the agent queries BigQuery for nutrient-dense candidates.
- **Diet rules assistant:** “I’m managing Type 2 diabetes—suggest breakfast options under 45g carbs, high in fiber and protein.”

> Tip: Encourage users to **state constraints clearly** (allergens, macros, ingredients to avoid), and the agent will plan multi-step queries.

---

## Configuration Notes

- **BigQuery schema**: The notebooks load the **FDC CSVs** into standard tables (names may vary by notebook version). If you rename the dataset or tables, update:
  - Agent’s **BigQuery tool** queries
  - Any SQL in the Flask app (if present)
- **Agent Tools**: A common toolset includes:
  - **BigQueryTool** (for nutrient queries)
  - Optional **Web/Search Tool** (for label lookups or authoritative references)
  - Optional **Allergen reference tool** (if you mirror/ingest curated allergen info)
- **Safety & Guardrails**:
  - This app is **not medical advice**. Provide disclaimers.
  - Consider adding **prompt guardrails**, **retrieval citations**, and **PII policies** for production use.

---

## Local Development Tips

- Use a `.env` file or `env.yaml` to keep secrets/config organized.
- Create a dedicated **service account** for local dev with constrained roles:
  - `BigQuery Data Viewer`
  - `Vertex AI User`
  - `Agent Engine Invoker` (or equivalent)
- For Flask UX, plan for:
  - Clear error messages for missing config
  - Loading spinners and markdown rendering
  - Copy-to-clipboard for agent answers and SQL traces (if you expose them)

---

## Troubleshooting

- **Agent returns empty or generic answers**
  - Verify the **Agent Engine** endpoint/ID and region.
  - Check tool wiring (BigQuery dataset/table names).
  - Try a simpler question first to validate connectivity.
- **BigQuery queries fail**
  - Confirm dataset and table names.
  - Ensure your principal (user or service account) has **Viewer** or appropriate *Data* permissions.
- **Auth errors**
  - Make sure `gcloud auth application-default login` or service account creds are set and exported.
  - Verify the project/region match across notebooks, agent, and Flask app.

---

## Contributing

PRs welcome! Please keep contributions **small and focused**:
- One change per PR (e.g., new tool, notebook improvement, UI tweak)
- Add/update docstrings and comments
- Include minimal repro steps and screenshots/gifs where helpful

---

## License

Unless otherwise noted in subfolders, this sample is provided for educational/demonstration purposes. If a `LICENSE` file is present, that file governs usage; otherwise, please treat this as a permissive sample and credit the source in derivative works.

---

## Acknowledgments

- **USDA FoodData Central** — comprehensive nutrient data  
- **FARRP AllergenOnline** — allergen reference data  
- Google Cloud teams behind **BigQuery**, **Vertex AI**, **ADK**, and **Agent Engine**

---

## FAQ

**Is this production-ready?**  
No. It’s meant for **learning and rapid prototyping** at the hackathon. For production, add robust **testing, observability, privacy & safety controls**, and strict **data governance**.

**Can I swap the UI or tools?**  
Yes—this is a **modular** setup. Swap Flask for any web stack, add/remove tools, or point to different datasets.

**What if I don’t have Colab Enterprise?**  
Run the notebooks locally (VS Code/Python), or adapt them into simple Python scripts that load FDC into BigQuery via the Python SDK.
