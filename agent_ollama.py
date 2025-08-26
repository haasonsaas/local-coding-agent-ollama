#!/usr/bin/env python3
"""
Local-only coding agent using Ollama through OpenAI-compatible API.
Works entirely offline with open-weight models and tool calling.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LocalCodingAgent:
    def __init__(self):
        # Initialize OpenAI client pointed at Ollama
        self.client = openai.Client(
            base_url=os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1"),
            api_key=os.getenv("OPENAI_API_KEY", "ollama")
        )
        
        # Model configuration
        self.agent_model = os.getenv("AGENT_MODEL", "llama3.1:8b")
        self.oracle_model = os.getenv("ORACLE_MODEL", "deepseek-r1:7b")
        
        # Workspace setup
        self.workspace = Path(os.getenv("WORKSPACE", "./ws")).resolve()
        self.workspace.mkdir(exist_ok=True)
        
        # Tool definitions for function calling
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read the contents of a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to the file to read"
                            }
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write content to a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to the file to write"
                            },
                            "content": {
                                "type": "string",
                                "description": "Content to write to the file"
                            }
                        },
                        "required": ["path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_directory",
                    "description": "List files and directories in a path",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to the directory to list"
                            }
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_command",
                    "description": "Execute a shell command",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Command to execute"
                            },
                            "cwd": {
                                "type": "string",
                                "description": "Working directory for the command (optional)"
                            }
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_files",
                    "description": "Search for text patterns in files",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "Text pattern to search for"
                            },
                            "directory": {
                                "type": "string",
                                "description": "Directory to search in (optional)"
                            }
                        },
                        "required": ["pattern"]
                    }
                }
            }
        ]
    
    def _safe_path(self, path: str) -> Path:
        """Ensure the path is within the workspace"""
        abs_path = Path(path).resolve()
        try:
            abs_path.relative_to(self.workspace)
            return abs_path
        except ValueError:
            # If path is outside workspace, put it in workspace
            return self.workspace / Path(path).name
    
    def read_file(self, path: str) -> str:
        """Read file contents"""
        try:
            safe_path = self._safe_path(path)
            return safe_path.read_text(encoding='utf-8')
        except Exception as e:
            return f"Error reading file: {e}"
    
    def write_file(self, path: str, content: str) -> str:
        """Write content to file"""
        try:
            safe_path = self._safe_path(path)
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            safe_path.write_text(content, encoding='utf-8')
            return f"Successfully wrote to {safe_path}"
        except Exception as e:
            return f"Error writing file: {e}"
    
    def list_directory(self, path: str = ".") -> str:
        """List directory contents"""
        try:
            if path == ".":
                dir_path = self.workspace
            else:
                dir_path = self._safe_path(path)
            
            if not dir_path.is_dir():
                return f"Error: {dir_path} is not a directory"
            
            items = []
            for item in sorted(dir_path.iterdir()):
                if item.is_dir():
                    items.append(f"[DIR]  {item.name}/")
                else:
                    size = item.stat().st_size
                    items.append(f"[FILE] {item.name} ({size} bytes)")
            
            return "\n".join(items) if items else "Directory is empty"
        except Exception as e:
            return f"Error listing directory: {e}"
    
    def run_command(self, command: str, cwd: str = None) -> str:
        """Execute shell command"""
        try:
            work_dir = self._safe_path(cwd) if cwd else self.workspace
            result = subprocess.run(
                command,
                shell=True,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = []
            if result.stdout:
                output.append(f"STDOUT:\n{result.stdout}")
            if result.stderr:
                output.append(f"STDERR:\n{result.stderr}")
            output.append(f"Exit code: {result.returncode}")
            
            return "\n".join(output)
        except subprocess.TimeoutExpired:
            return "Command timed out after 30 seconds"
        except Exception as e:
            return f"Error executing command: {e}"
    
    def search_files(self, pattern: str, directory: str = None) -> str:
        """Search for text patterns in files"""
        try:
            search_dir = self._safe_path(directory) if directory else self.workspace
            
            if not search_dir.exists():
                return f"Directory {search_dir} does not exist"
            
            matches = []
            for file_path in search_dir.rglob("*"):
                if file_path.is_file():
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        lines = content.split('\n')
                        for i, line in enumerate(lines, 1):
                            if pattern.lower() in line.lower():
                                matches.append(f"{file_path.relative_to(self.workspace)}:{i}: {line.strip()}")
                    except:
                        continue  # Skip binary or unreadable files
            
            return "\n".join(matches[:50]) if matches else "No matches found"  # Limit to 50 results
        except Exception as e:
            return f"Error searching files: {e}"
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool function"""
        tool_functions = {
            "read_file": self.read_file,
            "write_file": self.write_file,
            "list_directory": self.list_directory,
            "run_command": self.run_command,
            "search_files": self.search_files,
        }
        
        if tool_name not in tool_functions:
            return f"Unknown tool: {tool_name}"
        
        try:
            return tool_functions[tool_name](**arguments)
        except TypeError as e:
            return f"Invalid arguments for {tool_name}: {e}"
    
    def chat_with_oracle(self, prompt: str, context: str = "") -> str:
        """Use the oracle model for reasoning/validation"""
        try:
            full_prompt = f"{context}\n\n{prompt}" if context else prompt
            
            response = self.client.chat.completions.create(
                model=self.oracle_model,
                messages=[
                    {"role": "system", "content": "You are an expert code reviewer and reasoning assistant. Provide thoughtful analysis and suggestions."},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Oracle error: {e}"
    
    def process_request(self, user_input: str) -> str:
        """Process user request with tool calling"""
        try:
            # System prompt for the agent
            system_prompt = """You are a local coding agent that helps with software development tasks. 
            You have access to tools for reading/writing files, executing commands, and searching code.
            Always use the appropriate tools to complete tasks. Be thorough and helpful.
            Work within the workspace directory and maintain good coding practices.
            
            When working on code:
            1. Read existing files to understand the codebase
            2. Make incremental changes
            3. Test your changes when possible
            4. Follow good software engineering practices
            """
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
            
            # Initial LLM call with tools
            response = self.client.chat.completions.create(
                model=self.agent_model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                temperature=0.3,
                max_tokens=2000
            )
            
            # Handle tool calls
            while response.choices[0].message.tool_calls:
                # Add assistant message
                messages.append(response.choices[0].message)
                
                # Execute each tool call
                for tool_call in response.choices[0].message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    tool_result = self.execute_tool(tool_name, tool_args)
                    
                    # Add tool result
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result
                    })
                
                # Get next response
                response = self.client.chat.completions.create(
                    model=self.agent_model,
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto",
                    temperature=0.3,
                    max_tokens=2000
                )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error processing request: {e}"
    
    def run_interactive(self):
        """Run interactive chat session"""
        print("🤖 Local Coding Agent (powered by Ollama)")
        print(f"📁 Workspace: {self.workspace}")
        print(f"🧠 Agent Model: {self.agent_model}")
        print(f"🔮 Oracle Model: {self.oracle_model}")
        print("💡 Type 'quit', 'exit', or 'bye' to stop")
        print("-" * 50)
        
        while True:
            try:
                user_input = input("\n🚀 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                # Special commands
                if user_input.startswith("/oracle "):
                    oracle_prompt = user_input[8:]
                    print(f"\n🔮 Oracle: {self.chat_with_oracle(oracle_prompt)}")
                    continue
                
                print(f"\n🤖 Agent: {self.process_request(user_input)}")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")

def main():
    """Main entry point"""
    agent = LocalCodingAgent()
    
    if len(sys.argv) > 1:
        # Process single command
        command = " ".join(sys.argv[1:])
        print(agent.process_request(command))
    else:
        # Interactive mode
        agent.run_interactive()

if __name__ == "__main__":
    main()
