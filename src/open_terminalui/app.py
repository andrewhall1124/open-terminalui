from ollama import chat
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Footer, Header, Input, Static


class ChatMessage(Static):
    """A single chat message widget"""

    def __init__(self, content: str, role: str, *args, **kwargs):
        super().__init__(content, *args, **kwargs)
        self.role = role
        self.add_class(f"message-{role}")


class OpenTerminalUI(App):
    CSS_PATH = "styles.css"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chat_history = []
        self.current_assistant_message = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="container"):
            with VerticalScroll(id="chat_container"):
                pass  # Messages will be added dynamically
            yield Static("", id="loading_indicator")
            yield Input(type="text", id="input", placeholder="Type a message...")
        yield Footer()

    @on(Input.Submitted, "#input")
    def handle_input_submission(self) -> None:
        input_widget = self.query_one("#input", Input)
        content = input_widget.value.strip()

        if not content:
            return

        # Add user message to history
        self.chat_history.append({"role": "user", "content": content})

        # Create and mount user message widget
        chat_container = self.query_one("#chat_container", VerticalScroll)
        user_msg = ChatMessage(content, "user")
        chat_container.mount(user_msg)
        chat_container.scroll_end(animate=False)

        input_widget.clear()
        self.stream_ollama_response(content)

    @work(exclusive=True, thread=True)
    def stream_ollama_response(self, content: str) -> None:
        # Select and update loading indicator
        loading_indicator = self.query_one("#loading_indicator", Static)
        self.call_from_thread(loading_indicator.update, "Thinking...")

        # Selecte chat history widget
        chat_container = self.query_one("#chat_container", VerticalScroll)

        # Stream ollama response
        stream = chat(model="llama3.2", messages=self.chat_history, stream=True)
        accumulated_text = ""
        for i, chunk in enumerate(stream):
            accumulated_text += chunk["message"]["content"]

            # Create assistant message widget on first chunk
            if i == 0:
                self.chat_history.append(
                    {"role": "assistant", "content": accumulated_text}
                )
                self.current_assistant_message = ChatMessage(
                    accumulated_text, "assistant"
                )
                self.call_from_thread(
                    chat_container.mount, self.current_assistant_message
                )
                self.call_from_thread(loading_indicator.update, "")
            # Update existing assistant message
            else:
                self.chat_history[-1]["content"] = accumulated_text
                self.call_from_thread(
                    self.current_assistant_message.update, accumulated_text
                )

            # Auto-scroll to bottom
            self.call_from_thread(chat_container.scroll_end, animate=False)

    def action_toggle_dark(self) -> None:
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )
