from open_terminalui.memory_manager import MemoryManager


def memory_search(
    memory_manager: MemoryManager, query: str, max_results: int = 5
) -> str:
    """Perform document search and return formatted results"""
    try:
        # Search vector database
        results = memory_manager.search_chat_summaries(query=query, top_k=max_results)

        # Format results for LLM context
        formatted_results = ""
        for result in results:
            formatted_results += f"Content: {result[0]}\n"
            formatted_results += f"Similarity Score: {result[1]}\n\n"

        return formatted_results
    except Exception as e:
        return f"Vector search error: {str(e)}"
