import sys, subprocess, importlib, asyncio, re
from urllib.parse import urlparse, urljoin
import httpx
from bs4 import BeautifulSoup


from google.genai import types
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.bigquery import BigQueryCredentialsConfig, BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode
from google.adk.tools import google_search   # built-in Google Search tool


# ---- Configure the site you want to use as the sole information source ----
SITE_URL = "http://www.allergenonline.org/"     # <-- change me
_ALLOWED = urlparse(SITE_URL).netloc.lower()

def fetch_url(url: str) -> dict:
    """
    Fetch and return cleaned text content from a URL within the allowed domain.

    Args:
        url (str): HTTP/HTTPS URL to fetch.

    Returns:
        dict: {
          "url": <final-url>,
          "title": <page title or None>,
          "text": <cleaned text (truncated)>,
          "chars": <len(text)>
        }

    Notes:
      - Only allows URLs on the configured site/domain.
      - Strips scripts/styles and collapses whitespace.
      - Truncates very large pages to keep context small.
    """
    try:
        u = url.strip()
        # Normalize relative links against base, just in case
        if u.startswith("/"):
            u = urljoin(SITE_URL, u)

        parsed = urlparse(u)
        if parsed.scheme not in {"http", "https"}:
            return {"status": "error", "error_message": "Only http/https URLs are allowed."}
        if not parsed.netloc.lower().endswith(_ALLOWED):
            return {"status": "error", "error_message": f"URL not in allowed domain: {_ALLOWED}"}

        # Fetch with sane limits
        with httpx.Client(follow_redirects=True, timeout=20) as client:
            resp = client.get(u, headers={"User-Agent": "adk-site-agent/1.0"})
            resp.raise_for_status()
            ctype = resp.headers.get("content-type", "").lower()
            if "text/html" not in ctype and "application/xhtml" not in ctype:
                return {"status": "error", "error_message": f"Unsupported content-type: {ctype}"}

            soup = BeautifulSoup(resp.text, "html.parser")
            # Remove noise
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            title = (soup.title.string.strip() if soup.title and soup.title.string else None)
            text = re.sub(r"\s+", " ", soup.get_text(separator=" ", strip=True))
            MAX_CHARS = 20000
            if len(text) > MAX_CHARS:
                text = text[:MAX_CHARS] + " ... [truncated]"
            return {"status": "success", "url": str(resp.url), "title": title, "text": text, "chars": len(text)}

    except Exception as e:
        return {"status": "error", "error_message": str(e)}

# ---- Agent that uses Google Search (site-restricted) + fetch_url ----
INSTR = f"""
You are a site-scoped research agent.
Only use Google Search constrained to the domain {_ALLOWED} by prefixing queries with 'site:{_ALLOWED}'.
You research information about food alergens and food health information.
When you identify promising results, call fetch_url(url) to open and read the page content.
Cite the specific URLs you used in your final answer. Do not use sources outside {_ALLOWED}.
"""

MODEL = "gemini-2.5-flash"

allergen_research_agent = Agent(
    model=MODEL,   # or your preferred Gemini model
    name="site_research_agent",
    description=f"Answers questions using only content from {_ALLOWED}.",
    instruction=INSTR,
    tools=[google_search, fetch_url],  # built-in search + custom fetcher
)
