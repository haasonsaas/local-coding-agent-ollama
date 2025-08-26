# Local Coding Agent with Ollama

A **local-only** coding agent that uses Ollama through its OpenAI-compatible API with tool calling capabilities. Works entirely offline with open-weight models.

## 🎯 Why Local-Only Coding Agents Matter

### The Problem with Cloud-Based AI Coding Assistants

While cloud-based AI coding assistants have revolutionized software development, they come with significant limitations:

**🔒 Privacy & Security Concerns**
- Your proprietary code is sent to third-party servers
- Enterprise codebases risk intellectual property exposure  
- Compliance issues with regulations like GDPR, HIPAA, SOX
- No guarantee your code won't be used for training future models

**💸 Cost Escalation**
- Usage-based pricing can become expensive for heavy users
- Team licenses multiply costs across organizations
- API rate limits can interrupt workflows
- Unpredictable monthly bills as usage scales

**📡 Internet Dependency**
- Requires stable internet connection to function
- Latency affects response times and user experience
- Complete failure during network outages
- Unreliable in remote locations or poor connectivity areas

**🎛️ Limited Customization**
- Locked into vendor's model choices and capabilities
- Cannot fine-tune models for your specific domain
- Limited control over system prompts and behavior
- Vendor lock-in with proprietary APIs and workflows

### The Local-Only Solution

This project addresses these challenges by bringing AI coding assistance directly to your machine:

**🏠 Complete Privacy**
- Your code never leaves your machine
- Zero data transmission to external servers
- Full compliance with enterprise security policies
- Perfect for sensitive or classified projects

**💰 Zero Ongoing Costs**
- One-time setup with no recurring fees
- Run unlimited queries without usage billing
- Scale across teams without per-seat licensing
- Predictable infrastructure costs

**⚡ Always Available**
- Works completely offline after initial setup
- No network latency - instant responses
- Reliable operation regardless of internet status
- Perfect for air-gapped environments

**🎨 Full Customization**
- Choose from multiple open-weight models
- Fine-tune models for your specific use cases  
- Customize system prompts and behavior
- Add domain-specific tools and capabilities

**🔧 Tool Calling & Function Integration**
- Native function calling with local file system access
- Execute commands safely within sandboxed workspace
- Integrate with your existing development tools
- Extensible architecture for custom tool development

### Perfect for These Use Cases

- **Enterprise Development**: Companies with strict security requirements
- **Remote/Offline Work**: Developers in areas with poor connectivity
- **Educational Institutions**: Teaching environments without internet access
- **Government/Defense**: Air-gapped systems and classified projects
- **Cost-Conscious Teams**: Startups and small teams avoiding subscription fees
- **Privacy-First Developers**: Those who prioritize data sovereignty
- **Research & Experimentation**: Academic research requiring reproducibility

### Performance Comparison

| Feature | Cloud Agents | Local Agent |
|---------|-------------|-------------|
| Privacy | ❌ Code sent externally | ✅ Fully local |
| Cost | ❌ Monthly subscriptions | ✅ One-time setup |
| Offline | ❌ Internet required | ✅ Works offline |
| Latency | ⚠️ Network dependent | ✅ Instant response |
| Customization | ⚠️ Limited options | ✅ Full control |
| Enterprise | ⚠️ Compliance issues | ✅ Audit-friendly |

This local coding agent proves that you don't need to sacrifice privacy, pay ongoing costs, or depend on internet connectivity to get powerful AI coding assistance.

## Setup

1. **Install Ollama** (if not already installed):
   ```bash
   # macOS
   brew install --cask ollama
   
   # Linux
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. **Start Ollama daemon**:
   ```bash
   ollama serve >/tmp/ollama.log 2>&1 &
   ```

3. **Pull required models**:
   ```bash
   ollama pull llama3.1:8b          # Main agent model
   ollama pull deepseek-r1:7b       # Oracle/reasoning model
   ollama pull deepseek-coder-v2    # Alternative coding model
   ```

4. **Set up Python environment**:
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

5. **Load environment**:
   ```bash
   set -a; source .env; set +a
   ```

## Usage

### 🎨 TUI Mode (Recommended)
Beautiful terminal interface with dark theme and organized panels:
```bash
source .venv/bin/activate
python agent_ollama.py --tui
```

**TUI Features:**
- 📁 **File Explorer**: Browse and manage workspace files
- 💬 **Chat Interface**: Interactive conversation with the agent
- 📊 **Status Panel**: Real-time agent status and statistics
- 🔧 **Tool Outputs**: Monitor tool execution and results
- ⌨️ **Keyboard Shortcuts**: Efficient navigation and controls

### 💻 Interactive CLI Mode
Traditional command-line interface:
```bash
source .venv/bin/activate
python agent_ollama.py
```

### ⚡ Single Command Mode
Execute one-off commands:
```bash
python agent_ollama.py "create a simple Python hello world script"
```

### 🔮 Oracle Mode (reasoning assistant)
In interactive mode, use `/oracle <question>` to consult the reasoning model:
```
/oracle How should I structure a REST API in Python?
```

## Available Tools

The agent has access to these tools:
- **read_file**: Read file contents
- **write_file**: Write content to files
- **list_directory**: List files and directories
- **run_command**: Execute shell commands
- **search_files**: Search for text patterns in files

## Configuration

Edit `.env` to customize:
- `AGENT_MODEL`: Main model for tool calling (default: llama3.1:8b)
- `ORACLE_MODEL`: Reasoning model (default: deepseek-r1:7b)
- `WORKSPACE`: Working directory (default: ./ws)

## Features

- 🏠 **Fully local**: No internet required after setup
- 🔧 **Tool calling**: Uses function calling for file operations
- 🧠 **Reasoning**: Oracle model for code review and planning
- 🔒 **Sandboxed**: Works within designated workspace
- ⚡ **Fast**: Direct Ollama API calls
- 🎯 **Context-aware**: Maintains conversation context

## Examples

```bash
# Create a Python project
python agent_ollama.py "create a simple web server using Flask"

# Debug code
python agent_ollama.py "find and fix any syntax errors in the Python files"

# Code review
python agent_ollama.py "review the code quality and suggest improvements"
```
