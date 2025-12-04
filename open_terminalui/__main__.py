from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Markdown, TextArea


class OpenTerminalUI(App):
    # CSS = """
    # #content {
    #     height: 1fr;
    # }

    # #input_container {
    #     height: auto;
    #     dock: bottom;
    # }

    # #user_input {
    #     width: 1fr;
    # }

    # #submit_button {
    #     width: auto;
    #     min-width: 5;
    # }
    # """

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="content"):
            yield Markdown(id="output")
        with Horizontal(id="input_container"):
            yield TextArea(id="user_input")
            yield Button("↑", flat=True, id="submit_button")
        yield Footer()

    @on(Button.Pressed, "#submit_button")
    def handle_submit_button(self) -> None:
        text_area = self.query_one("#user_input", TextArea)
        content = text_area.text
        if content.strip():
            self.query_one("#output", Markdown).update(content)
            text_area.clear()

    def action_toggle_dark(self) -> None:
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )


if __name__ == "__main__":
    app = OpenTerminalUI()
    app.run()
