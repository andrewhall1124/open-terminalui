from textual.app import ComposeResult
from textual.widgets import (
    Label,
    ListItem,
)


class ChatListItem(ListItem):
    """A custom list item for displaying chat titles"""

    def __init__(self, chat_id: int, title: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chat_id = chat_id
        self.chat_title = title

    def compose(self) -> ComposeResult:
        yield Label(self.chat_title)
