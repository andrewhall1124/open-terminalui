from ddgs import DDGS


def web_search(query: str, max_results: int = 5) -> str:
    """Perform web search and return formatted results"""
    try:
        results = list(DDGS().text(query, max_results=max_results))
        if not results:
            return "No search results found."

        # Format results for LLM context
        formatted_results = ""
        for result in results:
            formatted_results += f"Title: {result['title']}\n"
            formatted_results += f"Content: {result['body']}\n"
            formatted_results += f"Source: {result['href']}\n\n"

        return formatted_results
    except Exception as e:
        return f"Search error: {str(e)}"
