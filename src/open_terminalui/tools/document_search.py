from open_terminalui.document_manager import DocumentManager


def document_search(
    doc_manager: DocumentManager, query: str, max_results: int = 5
) -> str:
    """Perform document search and return formatted results"""
    try:
        # Search vector database
        results = doc_manager.search_documents(query=query, top_k=max_results)

        # Format results for LLM context
        formatted_results = ""
        for result in results:
            formatted_results += f"File Path: {result[1]}\n"
            formatted_results += f"Content: {result[0]}\n"
            formatted_results += f"Similarity Score: {result[2]}\n\n"

        return formatted_results
    except Exception as e:
        return f"Vector search error: {str(e)}"
