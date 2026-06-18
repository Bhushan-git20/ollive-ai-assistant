from duckduckgo_search import DDGS

def search_web(query: str, max_results: int = 3) -> str:
    """Perform a web search and return a formatted string of the top results."""
    try:
        results = DDGS().text(query, max_results=max_results)
        if not results:
            return "No web search results found."
        
        formatted_results = []
        for i, res in enumerate(results):
            title = res.get("title", "")
            body = res.get("body", "")
            href = res.get("href", "")
            formatted_results.append(f"[{i+1}] {title}\n{body}\nURL: {href}")
            
        return "\n\n".join(formatted_results)
    except Exception as e:
        return f"Web search failed: {str(e)}"

TOOL_DEFINITION = {
    "name": "web_search",
    "description": "Search the web for up-to-date information.",
    "trigger_keywords": ["search", "lookup", "who is", "what is", "tell me about"],
}
