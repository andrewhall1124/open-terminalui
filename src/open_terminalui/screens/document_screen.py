from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    DataTable,
    Input,
    Label,
    Static,
)

from open_terminalui.document_manager import DocumentManager


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
