from textual.app import ComposeResult
from textual.widgets import (
    Label,
    Static,
)


class ChatMessage(Static):
    """A single chat message widget with label"""

    def __init__(self, content: str, role: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.role: str = role
        self.content: str = content
        self.add_class(f"message-{role}")

    def compose(self) -> ComposeResult:
        if self.role == "user":
            label_text = "User:"
        elif self.role == "web_search":
            label_text = "Web Search Results:"
        elif self.role == "document_search":
            label_text = "Vector Search Results:"
        elif self.role == "memory_search":
            label_text = "Memory Search Results:"
        else:
            label_text = "Assistant:"
        yield Label(label_text, classes=f"message-label-{self.role}")
        yield Static(self.content, classes="message-content")

    def update_content(self, new_content: str) -> None:
        """Update the message content"""
        self.content = new_content
        content_widget = self.query_one(".message-content", Static)
        content_widget.update(new_content)
