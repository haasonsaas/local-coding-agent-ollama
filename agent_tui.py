#!/usr/bin/env python3
"""
Beautiful TUI interface for the local coding agent using Textual.
Inspired by modern terminal interfaces with dark theme and clean layout.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Button, DataTable, DirectoryTree, Footer, Header, Input, Log, Markdown,
    ProgressBar, RichLog, Static, TabbedContent, TabPane
)
from textual.reactive import reactive
from textual.message import Message
from textual import events
from rich.console import RenderableType
from rich.markdown import Markdown as RichMarkdown
from rich.syntax import Syntax
from rich.panel import Panel
from rich.text import Text

try:
    from agent_ollama import LocalCodingAgent
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from agent_ollama import LocalCodingAgent


class StatusBar(Static):
    """Custom status bar showing agent status and model info"""
    
    def __init__(self, agent: LocalCodingAgent):
        super().__init__()
        self.agent = agent
    
    def compose(self) -> ComposeResult:
        status_text = (
            f"[bold green]●[/bold green] Agent: [cyan]{self.agent.agent_model}[/cyan] | "
            f"[bold magenta]🔮[/bold magenta] Oracle: [cyan]{self.agent.oracle_model}[/cyan] | "
            f"[bold blue]📁[/bold blue] Workspace: [yellow]{self.agent.workspace.name}[/yellow]"
        )
        yield Static(status_text, id="status", markup=True)


class FileExplorer(Container):
    """File explorer panel showing workspace contents"""
    
    def __init__(self, workspace: Path):
        super().__init__()
        self.workspace = workspace
    
    def compose(self) -> ComposeResult:
        yield Static("📁 Files", classes="panel-title")
        yield DirectoryTree(str(self.workspace), id="file_tree")


class ChatPanel(Container):
    """Main chat interface with history and input"""
    
    def compose(self) -> ComposeResult:
        yield Static("💬 Chat", classes="panel-title")
        yield RichLog(id="chat_history", markup=True)
        yield Horizontal(
            Input(placeholder="Ask me anything about coding...", id="chat_input"),
            Button("Send", variant="primary", id="send_button"),
            id="input_container"
        )


class WorkspacePanel(Container):
    """Right panel showing workspace info and tool outputs"""
    
    def compose(self) -> ComposeResult:
        with TabbedContent(id="workspace_tabs"):
            with TabPane("📊 Status", id="status_tab"):
                yield Static("🎯 Agent Status", classes="section-title")
                yield RichLog(id="status_log", markup=True)
            
            with TabPane("🔧 Tools", id="tools_tab"):
                yield Static("🛠️ Tool Outputs", classes="section-title")
                yield RichLog(id="tool_log", markup=True)
            
            with TabPane("📈 Stats", id="stats_tab"):
                yield Static("📊 Session Stats", classes="section-title")
                yield DataTable(id="stats_table")


class AgentTUI(App):
    """Main TUI application for the coding agent"""
    
    CSS = """
    /* === GLOBAL STYLES === */
    Screen {
        background: #0f0f0f;
        color: #e6e6e6;
    }
    
    /* === HEADER AND STATUS === */
    Header {
        background: #1a1a1a;
        color: #e6e6e6;
        border-bottom: solid #333;
    }
    
    Footer {
        background: #1a1a1a;
        color: #888;
        border-top: solid #333;
    }
    
    #status {
        background: #1a1a1a;
        color: #4ade80;
        padding: 0 2;
        text-style: bold;
        border-bottom: solid #333;
    }
    
    /* === LAYOUT === */
    #main_container {
        layout: horizontal;
        height: 1fr;
        background: #0f0f0f;
    }
    
    #left_panel {
        width: 30%;
        background: #171717;
        padding: 1 2;
        border-right: solid #333;
    }
    
    #center_panel {
        width: 45%;
        height: 100%;
        background: #0f0f0f;
        padding: 1 2;
        layout: vertical;
    }
    
    #right_panel {
        width: 25%;
        background: #171717;
        padding: 1 2;
        border-left: solid #333;
    }
    
    /* === PANEL TITLES === */
    .panel-title {
        color: #4ade80;
        text-style: bold;
        background: #262626;
        padding: 1 2;
        margin-bottom: 1;

        border: solid #404040;
    }
    
    .section-title {
        color: #60a5fa;
        text-style: bold;
        margin: 1 0;
        padding: 0 1;
        border-left: solid #60a5fa;
    }
    
    /* === CHAT INTERFACE === */
    #chat_history {
        height: 1fr;
        overflow-y: auto;
        background: #0a0a0a;
        border: solid #333;
        margin-bottom: 1;
        scrollbar-color: #404040 #1a1a1a;
        scrollbar-color-hover: #525252 #1a1a1a;
    }
    
    #input_container {
        height: 4;
        background: #171717;
        padding: 1;
        border: solid #4ade80;
    }
    
    #chat_input {
        width: 1fr;
        margin-right: 2;
        background: #ffffff;
        color: #000000;
        border: solid #4ade80;
        padding: 1;
        text-style: bold;
    }
    
    #chat_input:focus {
        border: solid #22c55e;
        background: #ffffff;
        color: #000000;
    }
    
    #send_button {
        min-width: 8;
        background: #4ade80;
        color: #0a0a0a;
        border: none;

        text-style: bold;
    }
    
    #send_button:hover {
        background: #22c55e;
    }
    
    /* === FILE EXPLORER === */
    #file_tree {
        height: 1fr;
        background: #0a0a0a;
        border: solid #333;

        color: #d1d5db;
        scrollbar-color: #404040 #1a1a1a;
    }
    
    DirectoryTree {
        background: #0a0a0a;
        color: #d1d5db;
    }
    
    DirectoryTree > .directory-tree--file {
        color: #9ca3af;
    }
    
    DirectoryTree > .directory-tree--folder {
        color: #60a5fa;
        text-style: bold;
    }
    
    DirectoryTree:focus .directory-tree--cursor {
        background: #1e40af;
        color: #ffffff;
    }
    
    /* === TABS === */
    #workspace_tabs {
        height: 1fr;
        background: #171717;
    }
    
    TabbedContent {
        background: #171717;
        border: solid #333;

    }
    
    Tabs {
        background: #262626;
        color: #9ca3af;
    }
    
    Tab {
        background: #262626;
        color: #9ca3af;
        padding: 1 2;
        border-right: solid #404040;

        margin-right: 1;
    }
    
    Tab:hover {
        background: #404040;
        color: #e6e6e6;
    }
    
    Tab.-active {
        background: #4ade80;
        color: #0a0a0a;
        text-style: bold;
    }
    
    TabPane {
        background: #0a0a0a;
        padding: 2;

    }
    
    /* === STATUS LOGS === */
    #status_log, #tool_log {
        height: 1fr;
        background: #0a0a0a;
        border: solid #333;

        scrollbar-color: #404040 #1a1a1a;
        color: #d1d5db;
    }
    
    /* === STATS TABLE === */
    #stats_table {
        height: 1fr;
        background: #0a0a0a;
        border: solid #333;

        color: #d1d5db;
    }
    
    DataTable {
        background: #0a0a0a;
        color: #d1d5db;
    }
    
    DataTable > .datatable--header {
        background: #262626;
        color: #4ade80;
        text-style: bold;
        border-bottom: solid #404040;
    }
    
    DataTable > .datatable--row {
        background: #0a0a0a;
    }
    
    DataTable > .datatable--row:hover {
        background: #1a1a1a;
    }
    
    DataTable > .datatable--row-odd {
        background: #121212;
    }
    
    DataTable > .datatable--row-odd:hover {
        background: #1a1a1a;
    }
    
    /* === BUTTONS === */
    Button {
        background: #4ade80;
        color: #0a0a0a;
        border: none;

        text-style: bold;
        padding: 1 2;
        min-width: 8;
    }
    
    Button:hover {
        background: #22c55e;
        color: #ffffff;
    }
    
    Button.-primary {
        background: #3b82f6;
        color: #ffffff;
    }
    
    Button.-primary:hover {
        background: #2563eb;
    }
    
    /* === MESSAGE STYLING === */
    .message-user {
        color: #4ade80;
        text-style: bold;
    }
    
    .message-agent {
        color: #60a5fa;
        text-style: bold;
    }
    
    .message-system {
        color: #9ca3af;
        text-style: italic;
    }
    
    .message-error {
        color: #ef4444;
        text-style: bold;
    }
    
    .message-success {
        color: #22c55e;
        text-style: bold;
    }
    
    .message-warning {
        color: #f59e0b;
        text-style: bold;
    }
    
    /* === SCROLLBARS === */
    * {
        scrollbar-color: #404040 #1a1a1a;
        scrollbar-color-hover: #525252 #262626;
        scrollbar-color-active: #6b7280 #374151;
    }
    
    /* === LOADING/THINKING INDICATORS === */
    .thinking {
        color: #9ca3af;
        text-style: italic;
        background: #1a1a1a;
        padding: 1;
        border-left: solid #60a5fa;

    }
    
    /* === STATUS INDICATORS === */
    .status-online {
        color: #22c55e;
    }
    
    .status-offline {
        color: #ef4444;
    }
    
    .status-working {
        color: #f59e0b;
    }
    """
    
    def __init__(self):
        super().__init__()
        self.agent = LocalCodingAgent()
        self.message_count = 0
        self.tool_calls = 0
        self.start_time = datetime.now()
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield StatusBar(self.agent)
        
        with Container(id="main_container"):
            with Container(id="left_panel"):
                yield FileExplorer(self.agent.workspace)
            
            with Container(id="center_panel"):
                yield ChatPanel()
            
            with Container(id="right_panel"):
                yield WorkspacePanel()
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the application when mounted"""
        # Initialize status
        status_log = self.query_one("#status_log", RichLog)
        status_log.write(Text.from_markup("[bold green]✅ Agent initialized[/bold green]"))
        status_log.write(Text.from_markup(f"[cyan]🤖 Model:[/cyan] [white]{self.agent.agent_model}[/white]"))
        status_log.write(Text.from_markup(f"[magenta]🔮 Oracle:[/magenta] [white]{self.agent.oracle_model}[/white]"))
        status_log.write(Text.from_markup(f"[blue]📁 Workspace:[/blue] [yellow]{self.agent.workspace}[/yellow]"))
        
        # Initialize stats table
        stats_table = self.query_one("#stats_table", DataTable)
        stats_table.add_columns("Metric", "Value")
        stats_table.add_row("Messages", "0")
        stats_table.add_row("Tool Calls", "0") 
        stats_table.add_row("Uptime", "0s")
        
        # Welcome message with better formatting
        chat_history = self.query_one("#chat_history", RichLog)
        
        # Create a beautiful welcome banner
        welcome_panel = Panel(
            Text.from_markup(
                "[bold bright_blue]🤖 Local Coding Agent[/bold bright_blue]\n\n"
                "[white]Welcome! I'm your local AI coding assistant.[/white]\n"
                "[dim]• Read/write files • Execute commands • Analyze code •[/dim]\n\n"
                f"[dim]📁 Working in:[/dim] [yellow]{self.agent.workspace}[/yellow]\n"
                f"[dim]🤖 Powered by:[/dim] [cyan]{self.agent.agent_model}[/cyan]\n\n"
                "[green]Type your question or task below to get started! 🚀[/green]"
            ),
            title="[bold green]● READY[/bold green]",
            border_style="green",
            padding=(1, 2)
        )
        
        chat_history.write(welcome_panel)
        
        # Focus on input
        self.query_one("#chat_input", Input).focus()
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "send_button":
            await self.send_message()
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission"""
        if event.input.id == "chat_input":
            await self.send_message()
    
    async def send_message(self) -> None:
        """Send a message to the agent"""
        chat_input = self.query_one("#chat_input", Input)
        chat_history = self.query_one("#chat_history", RichLog)
        tool_log = self.query_one("#tool_log", RichLog)
        
        user_message = chat_input.value.strip()
        if not user_message:
            return
        
        # Clear input
        chat_input.value = ""
        
        # Show user message in a styled panel
        user_panel = Panel(
            Text.from_markup(f"[white]{user_message}[/white]"),
            title="[bold green]🚀 You[/bold green]",
            border_style="green",
            padding=(0, 1)
        )
        chat_history.write(user_panel)
        
        # Show thinking indicator with animation
        thinking_panel = Panel(
            Text.from_markup("[bold yellow]🤔 Processing your request...[/bold yellow]"),
            title="[bold blue]● Agent[/bold blue]", 
            border_style="blue",
            padding=(0, 1)
        )
        chat_history.write(thinking_panel)
        
        try:
            # Process with agent
            response = await asyncio.to_thread(self.agent.process_request, user_message)
            
            # Show agent response in a styled panel
            response_panel = Panel(
                Text.from_markup(f"[white]{response}[/white]"),
                title="[bold cyan]🤖 Agent[/bold cyan]",
                border_style="cyan",
                padding=(0, 1)
            )
            chat_history.write(response_panel)
            
            # Log to tool output
            tool_log.write(Text.from_markup(f"[green]✅ Processed message:[/green] [dim]{user_message[:50]}{'...' if len(user_message) > 50 else ''}[/dim]"))
            
            # Update stats
            self.message_count += 1
            self.update_stats()
            
        except Exception as e:
            error_panel = Panel(
                Text.from_markup(f"[red]{str(e)}[/red]"),
                title="[bold red]❌ Error[/bold red]",
                border_style="red",
                padding=(0, 1)
            )
            chat_history.write(error_panel)
            tool_log.write(Text.from_markup(f"[red]❌ Error:[/red] {str(e)}"))
    
    def update_stats(self) -> None:
        """Update the stats table"""
        stats_table = self.query_one("#stats_table", DataTable)
        uptime = datetime.now() - self.start_time
        uptime_str = f"{int(uptime.total_seconds())}s"
        
        # Clear and rebuild table (simpler than updating cells)
        stats_table.clear()
        stats_table.add_columns("Metric", "Value")
        stats_table.add_row("Messages", str(self.message_count))
        stats_table.add_row("Tool Calls", str(self.tool_calls))
        stats_table.add_row("Uptime", uptime_str)
    
    def action_toggle_dark(self) -> None:
        """Toggle dark mode"""
        self.dark = not self.dark
    
    def action_quit(self) -> None:
        """Quit the application"""
        self.exit()
    
    async def action_oracle_mode(self) -> None:
        """Toggle oracle mode"""
        chat_history = self.query_one("#chat_history", RichLog)
        oracle_panel = Panel(
            Text.from_markup(
                "[bold bright_magenta]🔮 Oracle Mode Activated[/bold bright_magenta]\n\n"
                "[white]The Oracle is now available for:[/white]\n"
                "[cyan]• Code reviews and architecture analysis[/cyan]\n"
                "[cyan]• Complex reasoning and problem solving[/cyan]\n"
                "[cyan]• Best practices and optimization advice[/cyan]\n\n"
                "[yellow]Prefix your message with '/oracle' to use this mode[/yellow]"
            ),
            title="[bold magenta]🔮 Oracle Ready[/bold magenta]",
            border_style="magenta",
            padding=(1, 2)
        )
        chat_history.write(oracle_panel)
    
    async def action_clear_chat(self) -> None:
        """Clear chat history"""
        chat_history = self.query_one("#chat_history", RichLog)
        chat_history.clear()
        
        # Show a nice clear message
        clear_panel = Panel(
            Text.from_markup("[dim]Chat history cleared. Ready for new conversation![/dim]"),
            title="[bold blue]🧹 Cleared[/bold blue]",
            border_style="blue",
            padding=(0, 1)
        )
        chat_history.write(clear_panel)


async def run_tui():
    """Run the TUI application"""
    app = AgentTUI()
    await app.run_async()


if __name__ == "__main__":
    asyncio.run(run_tui())
