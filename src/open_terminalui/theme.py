from textual.theme import Theme

open_terminalui_theme = Theme(
    name="open_terminalui",
    primary="lime",
    secondary="white",
    accent="lime",
    foreground="#ffffff",
    background="#000000",
    success="green",
    warning="yellow",
    error="red",
    surface="#111111",
    panel="#444444",
    dark=True,
    variables={
        "footer-key-foreground": "lime",
    },
)
