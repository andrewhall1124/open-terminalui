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
            yield Input(type="text", id="input")
        yield Footer()

    @on(Input.Submitted, "#input")
    def handle_input_submission(self) -> None:
        input_widget = self.query_one("#input", Input)
        content = input_widget.value
        if content.strip():
            input_widget.clear()
            self.stream_ollama_response(content)

    @work(exclusive=True)
    async def stream_ollama_response(self, content: str) -> None:
        messages = [{"role": "user", "content": content}]

        markdown_widget = self.query_one("#output", Markdown)
        markdown_widget.update("")
        accumulated_text = ""
        stream = chat(model="llama3.2", messages=messages, stream=True)

        for chunk in stream:
            accumulated_text += chunk["message"]["content"]
            markdown_widget.update(accumulated_text)

    def action_toggle_dark(self) -> None:
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )
