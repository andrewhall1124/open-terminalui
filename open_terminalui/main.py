import ollama
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Button, Footer, Header, Input, Select, Static


class ChatMessage(Static):
    """A single chat message widget."""

    def __init__(self, role: str, content: str, **kwargs) -> None:
        self.role = role
        self.message_content = content
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        """Compose the message widget."""
        role_prefix = "You: " if self.role == "user" else "Assistant: "
        yield Static(
            f"[bold {'cyan' if self.role == 'user' else 'green'}]{role_prefix}[/]"
        )
        yield Static(self.message_content)


class ChatHistory(Vertical):
    """Container for chat messages."""

    DEFAULT_CSS = """
    ChatHistory {
        height: 1fr;
        overflow-y: auto;
        border: solid $accent;
        padding: 1;
    }

    ChatMessage {
        margin-bottom: 1;
    }

    ChatMessage Static:first-child {
        margin-bottom: 0;
    }
    """


class OpenTerminalUI(App):
    """A Textual app for chatting with Ollama models."""

    CSS = """
    Screen {
        background: $surface;
    }

    #input-container {
        height: auto;
        dock: bottom;
        padding: 1;
        background: $panel;
    }

    #model-selector {
        width: 30;
        margin-right: 2;
    }

    #chat-input {
        width: 1fr;
    }

    #send-button {
        width: auto;
        margin-left: 1;
    }

    .status-bar {
        height: 1;
        background: $panel;
        color: $text-muted;
        padding: 0 1;
        dock: bottom;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", priority=True),
        Binding("ctrl+n", "new_chat", "New Chat"),
    ]

    current_model: reactive[str] = reactive("llama2")
    available_models: reactive[list] = reactive([])
    conversation_history: list = []

    def compose(self) -> ComposeResult:
        """Compose the app UI."""
        yield Header(show_clock=True)
        yield ChatHistory(id="chat-history")

        with Container(id="input-container"):
            with Horizontal():
                yield Select(
                    [(model, model) for model in ["llama2", "mistral", "codellama"]],
                    id="model-selector",
                    allow_blank=False,
                    value="llama2",
                )
                yield Input(placeholder="Type your message here...", id="chat-input")
                yield Button("Send", id="send-button", variant="primary")

        yield Static("Ready | Model: llama2", classes="status-bar", id="status")
        yield Footer()

    async def on_mount(self) -> None:
        """Set up the app when mounted."""
        self.title = "Open Terminal UI"
        self.sub_title = "Chat with Ollama"

        # Focus the input
        self.query_one("#chat-input", Input).focus()

        # Load available models
        await self.load_models()

    async def load_models(self) -> None:
        """Load available Ollama models."""
        try:
            models = ollama.list()
            model_list = [model["name"] for model in models.get("models", [])]

            if model_list:
                self.available_models = model_list
                select = self.query_one("#model-selector", Select)
                select.set_options([(model, model) for model in model_list])
                if model_list:
                    self.current_model = model_list[0]
                    select.value = model_list[0]
                self.update_status(f"Loaded {len(model_list)} models")
            else:
                self.update_status(
                    "No models found. Please pull a model with 'ollama pull'"
                )
        except Exception as e:
            self.update_status(f"Error loading models: {str(e)}")

    def update_status(self, message: str) -> None:
        """Update the status bar."""
        status = self.query_one("#status", Static)
        status.update(f"{message} | Model: {self.current_model}")

    async def on_select_changed(self, event: Select.Changed) -> None:
        """Handle model selection changes."""
        if event.select.id == "model-selector":
            self.current_model = str(event.value)
            self.update_status("Model changed")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "send-button":
            await self.send_message()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission (Enter key)."""
        if event.input.id == "chat-input":
            await self.send_message()

    async def send_message(self) -> None:
        """Send a message to the Ollama model."""
        input_widget = self.query_one("#chat-input", Input)
        message = input_widget.value.strip()

        if not message:
            return

        # Clear input
        input_widget.value = ""

        # Add user message to chat
        chat_history = self.query_one("#chat-history", ChatHistory)
        await chat_history.mount(ChatMessage("user", message))

        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": message})

        # Update status
        self.update_status("Generating response...")

        # Create a placeholder for assistant response
        assistant_message = ChatMessage("assistant", "")
        await chat_history.mount(assistant_message)

        # Scroll to bottom
        chat_history.scroll_end(animate=False)

        try:
            # Stream response from Ollama
            response_text = ""
            stream = ollama.chat(
                model=self.current_model,
                messages=self.conversation_history,
                stream=True,
            )

            for chunk in stream:
                if "message" in chunk:
                    content = chunk["message"].get("content", "")
                    response_text += content
                    # Update the assistant message
                    assistant_message.query_one("Static:last-child").update(
                        response_text
                    )
                    chat_history.scroll_end(animate=False)

            # Add to conversation history
            self.conversation_history.append(
                {"role": "assistant", "content": response_text}
            )
            self.update_status("Ready")

        except Exception as e:
            assistant_message.query_one("Static:last-child").update(
                f"[red]Error: {str(e)}[/]"
            )
            self.update_status(f"Error: {str(e)}")

    def action_new_chat(self) -> None:
        """Start a new chat conversation."""
        self.conversation_history = []
        chat_history = self.query_one("#chat-history", ChatHistory)
        chat_history.remove_children()
        self.update_status("New chat started")


def main() -> None:
    """Run the application."""
    app = OpenTerminalUI()
    app.run()


if __name__ == "__main__":
    main()
