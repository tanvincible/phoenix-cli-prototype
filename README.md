# Phoenix Prototype

> Code using plain English. Your AI agents will do the rest.  
> Powered by Gemini · Orchestrated via gRPC · Built for multi-agent extension.

## What is Phoenix?

Phoenix is a **natural language to code** prototype where your commands are routed to AI agents:

- **MainAI**: Understands your command and edits `main.py` accordingly.
- **DepAI**: Adds necessary packages to `requirements.txt` when asked by MainAI.
- Communication happens over **gRPC**, enabling modular, multi-agent behavior.

It’s like **Cursor**, but local.  
You write:  
> `add a function that fetches a URL and logs the result`

Phoenix writes:
```python
import requests

def fetch_and_log():
    response = requests.get('https://example.com')
    print(response.text)
```

And it updates `requirements.txt` for you.

## Quickstart

### 1. Clone + Install Dependencies

```bash
git clone https://github.com/tanvincible/phoenix-cli-prototype.git
cd phoenix-cli-prototype
pip install grpcio grpcio-tools protobuf
```

### 2. Set Up Your Gemini API Key

Phoenix uses **Gemini** to interpret your intent.

1. [Get a Gemini API key](https://aistudio.google.com/apikey/)
2. Create a `.env` file:

```bash
echo "GEMINI_API_KEY=your-key-here" > .env
source .env
```

If you forget this, `run.sh` will remind you.

### 3. Run the Prototype

```bash
bash run.sh
```

This will:

* Generate gRPC Python code
* Start the MainAI and DepAI agents
* Launch the Phoenix CLI

## Talk to Phoenix

After it starts, use natural language:

```
>> add a function that fetches weather data using requests
```

Phoenix will:

* Ask Gemini to understand your command
* Add the function to `files/main.py`
* If needed, ask DepAI to add `requests` to `files/requirements.txt`
* Confirm success

You’ll see:

```
✅ Function added successfully
```

## Project Structure

```
phoenix-prototype
├── agents/         # MainAI and DepAI gRPC servers
├── cli/            # NL-to-code CLI (phoenix_cli.py)
├── common/         # Gemini wrapper
├── files/          # Your generated codebase (main.py, requirements.txt)
├── generated/      # gRPC-generated stubs
├── proto/          # .proto definitions
├── run.sh          # One-step bootstrap script
└── README.md
```

## Agent Architecture

```
You
 ↓
Phoenix CLI ──[gRPC]──▶ MainAI ──[gRPC]──▶ DepAI
                           │                │
               understands code       adds to requirements.txt
                           ▼                ▼
                      files/main.py   files/requirements.txt
```

## Example Command

```
>> add a function that parses a JSON response from an API and prints a field
```

Phoenix might generate:

```python
import requests

def print_name_field():
    r = requests.get("https://api.example.com/data")
    print(r.json().get("name"))
```

And it’ll add `requests` to `requirements.txt` via DepAI.


## 🛠 Dev Notes

To regenerate gRPC code (e.g., if `.proto` files change):

```bash
python -m grpc_tools.protoc -Iproto \
  --python_out=generated \
  --grpc_python_out=generated \
  proto/*.proto
```

To fix generated import paths:

```bash
find generated -name "*_pb2*.py" -exec sed -i 's/^import \([a-zA-Z0-9_]*_pb2\) as/from . import \1 as/' {} +
```

## Why Phoenix?

Because **NL-first programming** should be:

* Modular
* Transparent
* Locally controlled
* Multi-agent from day one

## LICENSE

MIT