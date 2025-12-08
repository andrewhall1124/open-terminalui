from ddgs import DDGS
from ollama import chat
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Static,
    Switch,
)

from .document_manager import DocumentManager
from .models import Chat, Message
from .storage import ChatStorage
from .theme import open_terminalui_theme


class DocumentManagerScreen(ModalScreen):
    """Modal screen for managing documents"""

    def __init__(self, doc_manager: DocumentManager, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.doc_manager = doc_manager

    def compose(self) -> ComposeResult:
        with Vertical(id="document_dialog"):
            yield Label("Manage Documents", id="document_title")
            yield Static(id="status_indicator")
            with Horizontal(id="document_input_container"):
                yield Input(
                    placeholder="Enter PDF file path...",
                    id="document_path_input",
                )
                yield Button("Add", id="add_document_btn", variant="primary")
            yield DataTable(id="document_table")
            with Horizontal(id="document_button_container"):
                yield Button(
                    "Remove Selected", id="remove_document_btn", variant="error"
                )
                yield Button("Close", id="close_dialog_btn", variant="default")

    def on_mount(self) -> None:
        # Configure data table
        table = self.query_one("#document_table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Name", "Path", "Chunks")

        # Load table rows
        self._refresh_table()

    def _refresh_table(self) -> None:
        # Select table widget
        table = self.query_one("#document_table", DataTable)

        # Clear existing rows
        table.clear()

        # Get documents
        documents = self.doc_manager.list_documents()

        # Populate table
        for document in documents:
            table.add_row(document[1], document[0], document[2], key=str(document[0]))

    @on(Button.Pressed, "#add_document_btn")
    def handle_add_document(self) -> None:
        # Select input widget
        input_widget = self.query_one("#document_path_input", Input)

        # Get file_path
        file_path: str = input_widget.value.strip()

        # Clear input widget
        input_widget.clear()

        # Process document
        self.process_document(file_path)

    @work(exclusive=True, thread=True)
    def process_document(self, file_path: str) -> None:
        # Select widgets
        status_widget = self.query_one("#status_indicator", Static)
        input_widget = self.query_one("#document_path_input", Input)
        button_widget = self.query_one("#add_document_btn", Button)

        # Disable button and show processing status
        self.app.call_from_thread(setattr, button_widget, "disabled", True)
        self.app.call_from_thread(status_widget.update, "Processing...")

        # Process document
        success, message = self.doc_manager.add_document(file_path)

        # Update status and re-enable button
        self.app.call_from_thread(status_widget.update, message)
        self.app.call_from_thread(setattr, button_widget, "disabled", False)

        # If successful, clear input widget and update table
        if success:
            self.app.call_from_thread(input_widget.clear)
            self.app.call_from_thread(self._refresh_table)

    @on(Button.Pressed, "#remove_document_btn")
    def handle_remove_document(self) -> None:
        # Select widgets
        table = self.query_one("#document_table", DataTable)
        status_widget = self.query_one("#status_indicator", Static)

        # Get the selected row's file path
        if table.cursor_row is not None:
            row = table.get_row_at(table.cursor_row)
            file_path = row[1]

            # Remove the document
            success, message = self.doc_manager.remove_document(file_path)
            status_widget.update(message)

            # Refresh table if successful
            if success:
                self._refresh_table()

    @on(Button.Pressed, "#close_dialog_btn")
    def handle_close_dialog(self) -> None:
        self.app.pop_screen()


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
        elif self.role == "vector_search":
            label_text = "Vector Search Results:"
        else:
            label_text = "Assistant:"
        yield Label(label_text, classes=f"message-label-{self.role}")
        yield Static(self.content, classes="message-content")

    def update_content(self, new_content: str) -> None:
        """Update the message content"""
        self.content = new_content
        content_widget = self.query_one(".message-content", Static)
        content_widget.update(new_content)


class ChatListItem(ListItem):
    """A custom list item for displaying chat titles"""

    def __init__(self, chat_id: int, title: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chat_id = chat_id
        self.chat_title = title

    def compose(self) -> ComposeResult:
        yield Label(self.chat_title)


class OpenTerminalUI(App):
    CSS_PATH = "styles.tcss"
    BINDINGS = [
        ("ctrl+n", "new_chat", "New Chat"),
        ("ctrl+b", "toggle_sidebar", "Toggle Sidebar"),
        ("ctrl+d", "delete_chat", "Delete Chat"),
        ("ctrl+k", "manage_documents", "Manage Documents"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chat_history = []
        self.current_assistant_message: ChatMessage
        self.storage = ChatStorage()
        self.doc_manager = DocumentManager()
        self.current_chat: Chat
        self.sidebar_visible = True

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main_container"):
            with Vertical(id="sidebar"):
                yield Label("Chat History", id="sidebar_title")
                yield ListView(id="chat_list")
            with Vertical(id="container"):
                with VerticalScroll(id="chat_container"):
                    pass  # Messages will be added dynamically
                yield Static(" ", id="loading_indicator")
                with Vertical(id="input_bar"):
                    yield Input(
                        type="text", id="input", placeholder="Type a message..."
                    )
                    with Horizontal(id="buttons_container"):
                        with Horizontal(id="search_container"):
                            yield Label("Search:", id="search_label")
                            yield Switch(value=False, id="search_switch")
                        with Horizontal(id="documents_container"):
                            yield Label("Documents:", id="documents_label")
                            yield Switch(value=False, id="documents_switch")
                        with Horizontal(id="logs_container"):
                            yield Label("Logs:", id="logs_label")
                            yield Switch(value=False, id="logs_switch")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize a new chat on startup"""
        self.register_theme(open_terminalui_theme)
        self.theme = "open_terminalui"
        self.refresh_chat_list()
        self.new_chat()

    def refresh_chat_list(self) -> None:
        """Refresh the sidebar chat list"""
        chat_list = self.query_one("#chat_list", ListView)
        chat_list.clear()

        chats = self.storage.list_chats()
        for chat_id, title, updated_at in chats:
            chat_list.append(ChatListItem(chat_id, title))

    def new_chat(self) -> None:
        """Create a new chat and clear the UI (not saved to DB until it has messages)"""
        self.current_chat = Chat.create_unsaved()
        self.chat_history = []

        # Clear chat container
        chat_container = self.query_one("#chat_container", VerticalScroll)
        chat_container.remove_children()

    def load_chat(self, chat_id: int) -> None:
        """Load an existing chat"""
        chat = self.storage.load_chat(chat_id)
        if chat is None:
            return

        self.current_chat = chat
        self.chat_history = chat.to_ollama_messages()

        # Clear and reload chat messages in UI
        chat_container = self.query_one("#chat_container", VerticalScroll)
        chat_container.remove_children()

        # Check if logs should be displayed
        logs_switch = self.query_one("#logs_switch", Switch)
        show_logs = logs_switch.value

        for message in chat.messages:
            # Skip log messages if logs switch is off
            if message.role in ("web_search", "vector_search") and not show_logs:
                continue

            msg_widget = ChatMessage(message.content, message.role)
            chat_container.mount(msg_widget)

        chat_container.scroll_end(animate=False)

    def perform_web_search(self, query: str, max_results: int = 5) -> str:
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

    def perform_vector_search(self, query: str, max_results: int = 5) -> str:
        """Perform vector search and return formatted results"""
        try:
            # Search vector database
            results = self.doc_manager.search_documents(query=query, top_k=max_results)

            # Format results for LLM context
            formatted_results = ""
            for result in results:
                formatted_results += f"File Path: {result[1]}\n"
                formatted_results += f"Content: {result[0]}\n"
                formatted_results += f"Similarity Score: {result[2]}\n\n"

            return formatted_results
        except Exception as e:
            return f"Vector search error: {str(e)}"

    @on(Input.Submitted, "#input")
    def handle_input_submission(self) -> None:
        input_widget = self.query_one("#input", Input)
        content: str = input_widget.value.strip()

        if not content:
            return

        # Check if search, logs, and documents are enabled
        search_switch = self.query_one("#search_switch", Switch)
        logs_switch = self.query_one("#logs_switch", Switch)
        documents_switch = self.query_one("#documents_switch", Switch)
        use_search = search_switch.value
        use_logs = logs_switch.value
        use_documents = documents_switch.value

        # Add user message to chat
        user_message = Message(role="user", content=content)
        self.current_chat.messages.append(user_message)
        self.chat_history.append({"role": "user", "content": content})

        # Create and mount user message widget
        chat_container = self.query_one("#chat_container", VerticalScroll)
        user_msg = ChatMessage(content, "user")
        chat_container.mount(user_msg)
        chat_container.scroll_end(animate=False)

        input_widget.clear()
        self.stream_ollama_response(content, use_search, use_logs, use_documents)

    @work(exclusive=True, thread=True)
    def stream_ollama_response(
        self,
        content: str,
        use_search: bool = False,
        use_logs: bool = False,
        use_documents: bool = False,
    ) -> None:
        # Select and update loading indicator
        loading_indicator = self.query_one("#loading_indicator", Static)

        # If search is enabled, perform web search first
        messages_to_send = self.chat_history.copy()
        web_search_results = None
        if use_search:
            self.call_from_thread(loading_indicator.update, "Searching the web...")
            web_search_results = self.perform_web_search(content)

            # Add search results as system context
            messages_to_send = [
                {
                    "role": "system",
                    "content": f"Use the following web search results to help answer the user's question:\n\n{web_search_results}",
                }
            ] + messages_to_send

            # Always save logs to database
            log_message_data = Message(role="web_search", content=web_search_results)
            self.current_chat.messages.append(log_message_data)

            # Only display in UI if logs switch is enabled
            if use_logs:
                chat_container = self.query_one("#chat_container", VerticalScroll)
                log_message = ChatMessage(web_search_results, "web_search")
                self.call_from_thread(chat_container.mount, log_message)
                self.call_from_thread(chat_container.scroll_end, animate=False)

        # If documents is enabled, perform vector search
        vector_search_results = None
        if use_documents:
            self.call_from_thread(
                loading_indicator.update, "Searching vector database..."
            )
            vector_search_results = self.perform_vector_search(content)

            # Add search results as system context
            messages_to_send = [
                {
                    "role": "system",
                    "content": f"Use the following vector search results to help answer the user's question:\n\n{vector_search_results}",
                }
            ] + messages_to_send

            # Always save logs to database
            log_message_data = Message(
                role="vector_search", content=vector_search_results
            )
            self.current_chat.messages.append(log_message_data)

            # Only display in UI if logs switch is enabled
            if use_logs:
                chat_container = self.query_one("#chat_container", VerticalScroll)
                log_message = ChatMessage(vector_search_results, "vector_search")
                self.call_from_thread(chat_container.mount, log_message)
                self.call_from_thread(chat_container.scroll_end, animate=False)

        self.call_from_thread(loading_indicator.update, "Thinking...")

        # Select chat history widget
        chat_container = self.query_one("#chat_container", VerticalScroll)

        # Stream ollama response
        stream = chat(model="llama3.2", messages=messages_to_send, stream=True)
        accumulated_text = ""

        for i, chunk in enumerate(stream):
            accumulated_text += chunk["message"]["content"]

            # Create assistant message widget on first chunk
            if i == 0:
                self.chat_history.append(
                    {"role": "assistant", "content": accumulated_text}
                )
                assistant_message = Message(role="assistant", content=accumulated_text)
                self.current_chat.messages.append(assistant_message)

                self.current_assistant_message = ChatMessage(
                    accumulated_text, "assistant"
                )
                self.call_from_thread(
                    chat_container.mount, self.current_assistant_message
                )
                self.call_from_thread(loading_indicator.update, " ")
            # Update existing assistant message
            else:
                self.chat_history[-1]["content"] = accumulated_text
                self.current_chat.messages[-1].content = accumulated_text
                self.call_from_thread(
                    self.current_assistant_message.update_content, accumulated_text
                )

            # Auto-scroll to bottom
            self.call_from_thread(chat_container.scroll_end, animate=False)

        # Save chat to database after streaming completes
        self.storage.save_chat(self.current_chat)

        # Refresh sidebar to update chat title/timestamp
        self.call_from_thread(self.refresh_chat_list)

    @on(ListView.Selected, "#chat_list")
    def handle_chat_selection(self, event: ListView.Selected) -> None:
        """Handle chat selection from sidebar"""
        if isinstance(event.item, ChatListItem):
            self.load_chat(event.item.chat_id)

    @on(Switch.Changed, "#logs_switch")
    def handle_logs_toggle(self, event: Switch.Changed) -> None:
        """Handle logs switch toggle - reload current chat to show/hide logs"""
        if self.current_chat and self.current_chat.id is not None:
            self.load_chat(self.current_chat.id)

    def action_new_chat(self) -> None:
        """Action to create a new chat"""
        self.new_chat()

    def action_delete_chat(self) -> None:
        """Delete the currently selected chat from the sidebar"""
        chat_list = self.query_one("#chat_list", ListView)

        # Get the currently highlighted item
        if chat_list.index is None:
            return

        selected_item = chat_list.highlighted_child
        if not isinstance(selected_item, ChatListItem):
            return

        chat_id_to_delete = selected_item.chat_id

        # Delete from database
        self.storage.delete_chat(chat_id_to_delete)

        # If we're deleting the current chat, create a new one
        if (
            self.current_chat
            and self.current_chat.id is not None
            and self.current_chat.id == chat_id_to_delete
        ):
            self.new_chat()

        # Refresh the sidebar
        self.refresh_chat_list()

    def action_toggle_sidebar(self) -> None:
        """Toggle sidebar visibility"""
        sidebar = self.query_one("#sidebar")
        sidebar.display = not sidebar.display
        self.sidebar_visible = sidebar.display

    def action_manage_documents(self) -> None:
        """Open the document management screen"""
        self.push_screen(DocumentManagerScreen(self.doc_manager))
