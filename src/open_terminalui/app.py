from ollama import chat
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Footer, Header, Input, Markdown


class OpenTerminalUI(App):
    CSS_PATH = "styles.css"

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="container"):
            yield Markdown(id="output")
            yield Markdown(id="loading_indicator")
            yield Input(type="text", id="input")
        yield Footer()

    @on(Input.Submitted, "#input")
    def handle_input_submission(self) -> None:
        # Select input widget
        input_widget = self.query_one("#input", Input)

        # Parse input content
        content = input_widget.value.strip()

        # Clear input
        input_widget.clear()

        # Stream ollama response
        self.stream_ollama_response(content)

    @work(exclusive=True, thread=True)
    def stream_ollama_response(self, content: str) -> None:
        messages = [{"role": "user", "content": content}]
        output_widget = self.query_one("#output", Markdown)
        loading_indicator_widget = self.query_one("#loading_indicator", Markdown)

        self.call_from_thread(output_widget.update, "")
        self.call_from_thread(loading_indicator_widget.update, "Thinking...")

        accumulated_text = ""
        stream = chat(model="llama3.2", messages=messages, stream=True)

        for i, chunk in enumerate(stream):
            accumulated_text += chunk["message"]["content"]
            self.call_from_thread(output_widget.update, accumulated_text)
            if i == 0:
                self.call_from_thread(loading_indicator_widget.update, "")

    def action_toggle_dark(self) -> None:
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )
