import os, re

from crewai.tools import tool
from firecrawl import FirecrawlApp
from firecrawl.v2.types import ScrapeOptions


def _get_result_fields(result):
    if getattr(result, "markdown", None):
        metadata = result.metadata
        title = (metadata.title if metadata else None) or ""
        url = (metadata.url if metadata else None) or ""
        markdown = result.markdown
    else:
        title = getattr(result, "title", None) or ""
        url = getattr(result, "url", None) or ""
        markdown = getattr(result, "description", None) or getattr(result, "snippet", None) or ""

    return title, url, markdown


@tool
def web_search_tool(query: str):
    """
    Web Search Tool.
    Args:
        query: str
            The query to search the web for.
    Returns
        A list of search results with the website content in Markdown format.
    """
    app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

    response = app.search(
        query=query,
        limit=5,
        scrape_options=ScrapeOptions(
            formats=["markdown"],
        ),
    )

    cleaned_chunks = []

    for result in response.web or []:

        title, url, markdown = _get_result_fields(result)

        cleaned = re.sub(r"\\+|\n+", "", markdown).strip()
        cleaned = re.sub(r"\[[^\]]+\]\([^\)]+\)|https?://[^\s]+", "", cleaned)

        cleaned_result = {
            "title": title,
            "url": url,
            "markdown": cleaned,
        }

        cleaned_chunks.append(cleaned_result)

    return cleaned_chunks