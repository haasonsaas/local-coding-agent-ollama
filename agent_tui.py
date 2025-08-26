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
        yield Static(f"🤖 Agent: {self.agent.agent_model} | 🔮 Oracle: {self.agent.oracle_model} | 📁 Workspace: {self.agent.workspace.name}", id="status")


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
        with VerticalScroll(id="chat_container"):
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
    Screen {
        background: #1a1a1a;
    }
    
    .panel-title {
        color: #00d4aa;
        text-style: bold;
        background: #2d2d2d;
        padding: 0 1;
        margin-bottom: 1;
    }
    
    .section-title {
        color: #ffd700;
        text-style: bold;
        margin: 1 0;
    }
    
    #status {
        background: #2d2d2d;
        color: #00d4aa;
        padding: 0 1;
    }
    
    #main_container {
        layout: horizontal;
        height: 1fr;
    }
    
    #left_panel {
        width: 25%;
        background: #252525;
        padding: 1;
        border-right: solid #444;
    }
    
    #center_panel {
        width: 50%;
        background: #1e1e1e;
        padding: 1;
    }
    
    #right_panel {
        width: 25%;
        background: #252525;
        padding: 1;
        border-left: solid #444;
    }
    
    #chat_history {
        height: 1fr;
        background: #1a1a1a;
        border: solid #444;
        margin-bottom: 1;
    }
    
    #input_container {
        height: 3;
        background: #2d2d2d;
        padding: 1;
    }
    
    #chat_input {
        width: 1fr;
        margin-right: 1;
    }
    
    #file_tree {
        height: 1fr;
        background: #1a1a1a;
        border: solid #444;
    }
    
    #workspace_tabs {
        height: 1fr;
    }
    
    #status_log, #tool_log {
        height: 1fr;
        background: #1a1a1a;
        border: solid #444;
    }
    
    #stats_table {
        height: 1fr;
        background: #1a1a1a;
        border: solid #444;
    }
    
    Button {
        background: #00d4aa;
        color: #000;
    }
    
    Button:hover {
        background: #00b894;
    }
    
    Input {
        background: #2d2d2d;
        color: #fff;
        border: solid #444;
    }
    
    Input:focus {
        border: solid #00d4aa;
    }
    
    DirectoryTree {
        color: #fff;
    }
    
    TabbedContent {
        background: #1e1e1e;
    }
    
    TabPane {
        background: #1e1e1e;
    }
    
    .message-user {
        color: #00d4aa;
        text-style: bold;
    }
    
    .message-agent {
        color: #ffd700;
        text-style: bold;
    }
    
    .message-system {
        color: #888;
        text-style: italic;
    }
    
    .message-error {
        color: #ff6b6b;
        text-style: bold;
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
        status_log.write("✅ Agent initialized")
        status_log.write(f"🤖 Model: {self.agent.agent_model}")
        status_log.write(f"🔮 Oracle: {self.agent.oracle_model}")
        status_log.write(f"📁 Workspace: {self.agent.workspace}")
        
        # Initialize stats table
        stats_table = self.query_one("#stats_table", DataTable)
        stats_table.add_columns("Metric", "Value")
        stats_table.add_row("Messages", "0")
        stats_table.add_row("Tool Calls", "0")
        stats_table.add_row("Uptime", "0s")
        
        # Welcome message
        chat_history = self.query_one("#chat_history", RichLog)
        welcome_text = Text.from_markup(
            "[bold cyan]🤖 Local Coding Agent[/bold cyan]\n"
            "Welcome! I'm ready to help with your coding tasks.\n"
            "I can read/write files, execute commands, and analyze code.\n"
            f"Working in: [yellow]{self.agent.workspace}[/yellow]\n"
            "Type your question or task below!"
        )
        chat_history.write(welcome_text)
        
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
        
        # Show user message
        user_text = Text.from_markup(f"[bold green]🚀 You:[/bold green] {user_message}")
        chat_history.write(user_text)
        
        # Show thinking indicator
        thinking_text = Text.from_markup("[italic dim]🤔 Agent is thinking...[/italic dim]")
        chat_history.write(thinking_text)
        
        try:
            # Process with agent
            response = await asyncio.to_thread(self.agent.process_request, user_message)
            
            # Remove thinking indicator
            chat_history.clear_last()
            
            # Show agent response
            agent_text = Text.from_markup(f"[bold yellow]🤖 Agent:[/bold yellow]\n{response}")
            chat_history.write(agent_text)
            
            # Update stats
            self.message_count += 1
            self.update_stats()
            
        except Exception as e:
            chat_history.clear_last()
            error_text = Text.from_markup(f"[bold red]❌ Error:[/bold red] {str(e)}")
            chat_history.write(error_text)
            tool_log.write(f"Error: {str(e)}")
    
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
        oracle_text = Text.from_markup(
            "[bold magenta]🔮 Oracle Mode Activated[/bold magenta]\n"
            "Ask me for code reviews, architecture advice, or complex reasoning!"
        )
        chat_history.write(oracle_text)
    
    async def action_clear_chat(self) -> None:
        """Clear chat history"""
        chat_history = self.query_one("#chat_history", RichLog)
        chat_history.clear()
        welcome_text = Text.from_markup("[italic dim]Chat cleared.[/italic dim]")
        chat_history.write(welcome_text)


async def run_tui():
    """Run the TUI application"""
    app = AgentTUI()
    await app.run_async()


if __name__ == "__main__":
    asyncio.run(run_tui())
