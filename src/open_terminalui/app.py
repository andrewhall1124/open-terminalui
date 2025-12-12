import ollama
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Footer,
    Header,
    Input,
    Label,
    ListView,
    Static,
    Switch,
)

from open_terminalui._models import Chat, Message
from open_terminalui._themes import open_terminalui_theme
from open_terminalui.chat_manager import ChatManager
from open_terminalui.components import ChatListItem, ChatMessage
from open_terminalui.document_manager import DocumentManager
from open_terminalui.memory_manager import MemoryManager
from open_terminalui.screens.document_screen import DocumentManagerScreen
from open_terminalui.tools import document_search, memory_search, web_search


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
        self.chat_manager = ChatManager()
        self.doc_manager = DocumentManager()
        self.memory_manager = MemoryManager()
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
                        with Horizontal(classes="toggle_container"):
                            yield Label("Search:", classes="toggle_label")
                            yield Switch(value=False, id="search_switch")
                        with Horizontal(classes="toggle_container"):
                            yield Label("Documents:", classes="toggle_label")
                            yield Switch(value=False, id="documents_switch")
                        with Horizontal(classes="toggle_container"):
                            yield Label("Memory:", classes="toggle_label")
                            yield Switch(value=False, id="memory_switch")
                        with Horizontal(classes="toggle_container"):
                            yield Label("Logs:", classes="toggle_label")
                            yield Switch(value=False, id="logs_switch")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize a new chat on startup"""
        self.register_theme(open_terminalui_theme)
        self.theme = "open_terminalui"
        self._refresh_chat_list()
        self._new_chat()

    @work(exclusive=True, thread=True)
    def stream_ollama_response(
        self,
        content: str,
        use_search: bool = False,
        use_logs: bool = False,
        use_documents: bool = False,
        use_memory: bool = False,
    ) -> None:
        # Select and update loading indicator
        loading_indicator = self.query_one("#loading_indicator", Static)

        # If search is enabled, perform web search first
        messages_to_send = self.chat_history.copy()
        web_search_results = None
        if use_search:
            self.call_from_thread(loading_indicator.update, "Searching the web...")
            web_search_results = web_search(query=content)

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
        document_search_results = None
        if use_documents:
            self.call_from_thread(
                loading_indicator.update, "Searching vector database..."
            )
            document_search_results = document_search(
                doc_manager=self.doc_manager, query=content
            )

            # Add search results as system context
            messages_to_send = [
                {
                    "role": "system",
                    "content": f"Use the following vector search results to help answer the user's question:\n\n{document_search_results}",
                }
            ] + messages_to_send

            # Always save logs to database
            log_message_data = Message(
                role="document_search", content=document_search_results
            )
            self.current_chat.messages.append(log_message_data)

            # Only display in UI if logs switch is enabled
            if use_logs:
                chat_container = self.query_one("#chat_container", VerticalScroll)
                log_message = ChatMessage(document_search_results, "document_search")
                self.call_from_thread(chat_container.mount, log_message)
                self.call_from_thread(chat_container.scroll_end, animate=False)

        # If memory is enabled, perform memory search
        memory_search_results = None
        if use_memory:
            self.call_from_thread(loading_indicator.update, "Searching chat memory...")
            memory_search_results = memory_search(
                memory_manager=self.memory_manager, query=content
            )

            # Add search results as system context
            messages_to_send = [
                {
                    "role": "system",
                    "content": f"Use the following chat summaries from other messages to help answer the user's question:\n\n{memory_search_results}",
                }
            ] + messages_to_send

            # Always save logs to database
            log_message_data = Message(
                role="memory_search", content=memory_search_results
            )
            self.current_chat.messages.append(log_message_data)

            # Only display in UI if logs switch is enabled
            if use_logs:
                chat_container = self.query_one("#chat_container", VerticalScroll)
                log_message = ChatMessage(memory_search_results, "memory_search")
                self.call_from_thread(chat_container.mount, log_message)
                self.call_from_thread(chat_container.scroll_end, animate=False)

        self.call_from_thread(loading_indicator.update, "Thinking...")

        # Select chat history widget
        chat_container = self.query_one("#chat_container", VerticalScroll)

        # Stream ollama response
        stream = ollama.chat(model="llama3.2", messages=messages_to_send, stream=True)
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
        self.chat_manager.save_chat(self.current_chat)

        # Save chat to vector database too
        self.memory_manager.save_chat(self.current_chat)

        # Refresh sidebar to update chat title/timestamp
        self.call_from_thread(self._refresh_chat_list)

    # ---------- Private Methods ----------
    def _refresh_chat_list(self) -> None:
        """Refresh the sidebar chat list"""
        chat_list = self.query_one("#chat_list", ListView)
        chat_list.clear()

        chats = self.chat_manager.list_chats()
        for chat in chats:
            if chat.id is not None:
                chat_list.append(ChatListItem(chat.id, chat.title))

    def _new_chat(self) -> None:
        """Create a new chat and clear the UI (not saved to DB until it has messages)"""
        self.current_chat = Chat.create_unsaved()
        self.chat_history = []

        # Clear chat container
        chat_container = self.query_one("#chat_container", VerticalScroll)
        chat_container.remove_children()

    def _load_chat(self, chat_id: int) -> None:
        """Load an existing chat"""
        chat = self.chat_manager.load_chat(chat_id)
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
            if (
                message.role in ("web_search", "document_search", "memory_search")
                and not show_logs
            ):
                continue

            msg_widget = ChatMessage(message.content, message.role)
            chat_container.mount(msg_widget)

        chat_container.scroll_end(animate=False)

    # ---------- Handlers ----------

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
        memory_switch = self.query_one("#memory_switch", Switch)
        use_search = search_switch.value
        use_logs = logs_switch.value
        use_documents = documents_switch.value
        use_memory = memory_switch.value

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
        self.stream_ollama_response(
            content, use_search, use_logs, use_documents, use_memory
        )

    @on(ListView.Selected, "#chat_list")
    def handle_chat_selection(self, event: ListView.Selected) -> None:
        """Handle chat selection from sidebar"""
        if isinstance(event.item, ChatListItem):
            self._load_chat(event.item.chat_id)

    @on(Switch.Changed, "#logs_switch")
    def handle_logs_toggle(self, event: Switch.Changed) -> None:
        """Handle logs switch toggle - reload current chat to show/hide logs"""
        if self.current_chat and self.current_chat.id is not None:
            self._load_chat(self.current_chat.id)

    # ---------- Actions ----------

    def action_new_chat(self) -> None:
        """Action to create a new chat"""
        self._new_chat()

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
        self.chat_manager.delete_chat(chat_id_to_delete)
        self.memory_manager.delete_chat(chat_id_to_delete)

        # If we're deleting the current chat, create a new one
        if (
            self.current_chat
            and self.current_chat.id is not None
            and self.current_chat.id == chat_id_to_delete
        ):
            self._new_chat()

        # Refresh the sidebar
        self._refresh_chat_list()

    def action_toggle_sidebar(self) -> None:
        """Toggle sidebar visibility"""
        sidebar = self.query_one("#sidebar")
        sidebar.display = not sidebar.display
        self.sidebar_visible = sidebar.display

    def action_manage_documents(self) -> None:
        """Open the document management screen"""
        self.push_screen(DocumentManagerScreen(self.doc_manager))
