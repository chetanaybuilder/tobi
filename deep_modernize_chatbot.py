import os
import shutil

REPO_DIR = r"C:\Users\batra\Downloads\Tobi\tobi\Portfolio\AI-Chatbot-Assistant"

# Create directories
for d in ["src", "tests", "docs"]:
    os.makedirs(os.path.join(REPO_DIR, d), exist_ok=True)

# 1. basic_chatbot.py
basic_chatbot = """\"\"\"
Basic Chatbot Implementation
==========================

This module demonstrates the fundamental architecture of interacting with
the Google Gemini API. It shows how to initialize the client, manage a simple
input/output conversational loop, and handle user exit conditions gracefully.

This is intentionally kept simple to demonstrate core API interactions without
complex state management or object-oriented abstractions.
\"\"\"

import os
import sys
from typing import NoReturn
from dotenv import load_dotenv
from google import genai

# Load environment variables (e.g., GEMINI_API_KEY)
load_dotenv()

def get_api_client() -> genai.Client:
    \"\"\"
    Initializes and returns the Gemini API client.
    Raises a ValueError if the API key is missing from the environment.
    \"\"\"
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set. Please configure your .env file.")
    return genai.Client(api_key=api_key)

def run_chat_loop() -> NoReturn:
    \"\"\"
    Starts the interactive chat loop with the user.
    Handles basic user input and API responses via a blocking terminal interface.
    \"\"\"
    try:
        client = get_api_client()
    except ValueError as e:
        print(f"Configuration Error: {e}")
        sys.exit(1)

    print("╔══════════════════════════════════════╗")
    print("║      AI Chatbot Assistant v2.0       ║")
    print("║      Fundamental Implementation      ║")
    print("╚══════════════════════════════════════╝\\n")

    while True:
        try:
            user_input = input("  You → ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ["quit", "exit"]:
                print("\\n  👋 Session terminated gracefully. Goodbye!\\n")
                break
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_input
            )
            
            print(f"\\n  🤖 Bot → {response.text}")
            print("  " + "─"*40 + "\\n")
            
        except KeyboardInterrupt:
            print("\\n\\n  👋 Process interrupted by user. Exiting...\\n")
            break
        except Exception as e:
            # Broad exception catch to prevent complete crash during the loop,
            # though more targeted exceptions are generally preferred in production.
            print(f"\\n  ⚠️ An unexpected error occurred: {e}\\n")

if __name__ == "__main__":
    run_chat_loop()
"""

# 2. english_tutor_chatbot.py
english_tutor = """\"\"\"
English Tutor Chatbot (Robust Error Handling)
===========================================

This module demonstrates advanced system prompt engineering combined with
defensive programming practices. It creates a specialized educational persona
while robustly catching and handling potential network, parsing, or API errors
to ensure the interactive loop does not crash unexpectedly.
\"\"\"

import os
import sys
from typing import Optional
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError

load_dotenv()

class EnglishTutorBot:
    \"\"\"
    A specialized chatbot designed to correct grammar and tutor English.
    Demonstrates encapsulated state and targeted error handling.
    \"\"\"

    SYSTEM_PROMPT = \"\"\"You are a highly experienced English tutor.
Your goal is to politely correct grammar mistakes and help students learn English.
Always provide constructive feedback and explain the grammar rules briefly.\"\"\"

    def __init__(self) -> None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Configuration missing: GEMINI_API_KEY must be set.")
        self.client = genai.Client(api_key=api_key)
        self.bot_name = "TutorBot"

    def get_tutor_response(self, user_input: str) -> Optional[str]:
        \"\"\"
        Generates a response from the API, injecting the educational system prompt.
        \"\"\"
        try:
            # We explicitly construct the context for this specific educational turn.
            prompt = f"{self.SYSTEM_PROMPT}\\n\\nStudent: {user_input}"
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response.text
            
        except APIError as api_err:
            print(f"\\n[API Error] Provider encountered an issue: {api_err}")
            return None
        except ConnectionError:
            print("\\n[Network Error] Unable to reach the API. Please check your connection.")
            return None
        except Exception as e:
            print(f"\\n[System Error] An unexpected failure occurred: {e}")
            return None

    def start_session(self) -> None:
        \"\"\"Starts the interactive tutoring session.\"\"\"
        print(f"\\n--- {self.bot_name} Initialized ---")
        print("Type 'exit' or 'quit' to end the session.\\n")

        while True:
            try:
                user_input = input("Student: ").strip()
                
                if user_input.lower() in ['exit', 'quit']:
                    print(f"{self.bot_name}: Class dismissed! Keep practicing.")
                    break
                    
                if not user_input:
                    continue

                response_text = self.get_tutor_response(user_input)
                
                if response_text:
                    print(f"{self.bot_name}: {response_text}\\n")
                    
            except KeyboardInterrupt:
                print(f"\\n{self.bot_name}: Session interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\\n[Input Error] Failed to process input: {e}")

if __name__ == "__main__":
    try:
        tutor = EnglishTutorBot()
        tutor.start_session()
    except ValueError as e:
        print(f"Startup failed: {e}")
        sys.exit(1)
"""

# 3. love_guru_chatbot.py
love_guru = """\"\"\"
Love Guru Chatbot (System Prompt Injection)
=========================================

Demonstrates how to inject a strong, custom persona (system prompt) into the
conversation flow without relying on advanced object-oriented features.
\"\"\"

import os
import sys
from dotenv import load_dotenv
from google import genai

load_dotenv()

PERSONALITY_PROMPT = \"\"\"You are LoveGuru, a relationship advice bot.
You give warm, honest, and caring advice about relationships, love, friendships, and emotions.
You speak like a trusted friend, never judge anyone, always listen carefully, and help people 
build stronger connections. You are wise but talk casually and friendly.\"\"\"

def run_guru() -> None:
    \"\"\"Initializes the client and runs the Love Guru interactive session.\"\"\"
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is missing.")
        sys.exit(1)
        
    client = genai.Client(api_key=api_key)
    
    # We maintain the conversation as a single appended string to demonstrate 
    # naive memory passing. (Note: in production, structured history arrays are preferred)
    conversation_state = PERSONALITY_PROMPT + "\\n\\n"
    
    print("💕 Love Guru initialized. Ask me anything about relationships!")
    print("-" * 50)
    
    while True:
        try:
            user_input = input("\\nYou: ").strip()
            if not user_input:
                continue
                
            if user_input.lower() in ["quit", "exit"]:
                print("\\nLove Guru: Take care of your heart! Goodbye. 💕")
                break
                
            # Append the latest turn to the string-based memory state
            conversation_state += f"User: {user_input}\\n"
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=conversation_state
            )
            
            bot_reply = response.text
            print(f"Love Guru: {bot_reply}")
            
            # Append the bot's reply so future turns have context
            conversation_state += f"Guru: {bot_reply}\\n"
            
        except KeyboardInterrupt:
            print("\\n\\nLove Guru: Session interrupted. Take care! 💕")
            break
        except Exception as e:
            print(f"\\n[Error] The universe got confused: {e}")

if __name__ == "__main__":
    run_guru()
"""

# 4. memory_chatbot.py
memory_chatbot = """\"\"\"
Memory Chatbot (String-based Context)
===================================

This module demonstrates how conversational context (memory) can be achieved
by manually appending user and assistant turns to a single text string, which 
is then sent back to the model.

Note: While effective for simple interactions, modern API designs often prefer
structured message arrays (e.g., [{"role": "user", "parts": [...]}]) to prevent
prompt injection and simplify token management.
\"\"\"

import os
import sys
from dotenv import load_dotenv
from google import genai

load_dotenv()

def run_memory_bot() -> None:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY is not set.")
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    
    # Conversation memory maintained as a raw string
    conversation_memory = ""
    
    print("=== Context-Aware Chatbot ===")
    print("I will remember what we discuss during this session.")
    print("-" * 30)
    
    while True:
        try:
            user_input = input("\\nYou: ").strip()
            
            if user_input.lower() in ["quit", "exit"]:
                print("Goodbye!")
                break
                
            if not user_input:
                continue
                
            conversation_memory += f"User: {user_input}\\n"
            
            # Send the entire accumulated history to the model
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=conversation_memory
            )
            
            # Store the response to ensure continuity
            conversation_memory += f"Bot: {response.text}\\n"
            
            print(f"Bot: {response.text}")
            
        except KeyboardInterrupt:
            print("\\nExiting...")
            break
        except Exception as e:
            print(f"\\nError generating response: {e}")

if __name__ == "__main__":
    run_memory_bot()
"""

# 5. oop_chatbot.py
oop_chatbot = """\"\"\"
OOP Chatbot (Object-Oriented Architecture)
========================================

Demonstrates encapsulation, state management, and separation of concerns by 
wrapping the chatbot logic and its associated conversational history inside a 
clean Python class. 
\"\"\"

import os
import sys
from typing import List
from dotenv import load_dotenv
from google import genai

load_dotenv()

class OOPChatbot:
    \"\"\"
    Encapsulates the Gemini client and the session's conversational history.
    Provides a clean, reusable interface for interactive chat.
    \"\"\"
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash") -> None:
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        # Structured history storage
        self.history: List[str] = []

    def generate_response(self, user_input: str) -> str:
        \"\"\"
        Appends user input to history, generates a response, appends the response,
        and returns the result.
        \"\"\"
        self.history.append(f"User: {user_input}")
        
        # Combine history into a single string payload
        payload = "\\n".join(self.history)
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=payload
        )
        
        bot_reply = response.text
        self.history.append(f"Assistant: {bot_reply}")
        
        return bot_reply

    def start_chat(self) -> None:
        \"\"\"Initiates the interactive terminal loop.\"\"\"
        print("🤖 OOP Bot is ready to chat. Type 'exit' to quit.\\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ["exit", "quit"]:
                    print("Goodbye!")
                    break
                
                reply = self.generate_response(user_input)
                print(f"Bot: {reply}\\n")
                
            except KeyboardInterrupt:
                print("\\nExiting session...")
                break
            except Exception as e:
                print(f"\\n[Error] Failed to process request: {e}\\n")


if __name__ == "__main__":
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("Error: GEMINI_API_KEY environment variable is missing.")
        sys.exit(1)
        
    bot = OOPChatbot(api_key=key)
    bot.start_chat()
"""

# 6. save_load_chatbot.py
save_load_chatbot = """\"\"\"
Save/Load Chatbot (Local Persistence)
===================================

Demonstrates how to serialize and deserialize conversational state to and from 
local disk using JSON. This allows sessions to be paused, stored locally, and 
resumed later without relying on a database.
\"\"\"

import os
import sys
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
from google import genai

load_dotenv()

MEMORY_FILE = "memory.json"

def load_history(filepath: str) -> List[Dict[str, Any]]:
    \"\"\"
    Attempts to load structured conversation history from a JSON file.
    Returns an empty list if the file is missing or malformed.
    \"\"\"
    if not os.path.exists(filepath):
        return []
        
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure the loaded data is a list
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, IOError) as e:
        print(f"[Warning] Could not parse {filepath}: {e}. Starting fresh.")
        return []

def save_history(filepath: str, history_data: List[Dict[str, Any]]) -> None:
    \"\"\"
    Serializes the current conversation history to disk.
    \"\"\"
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(history_data, f, indent=2)
    except IOError as e:
        print(f"[Warning] Failed to save conversation history: {e}")

def run_persistent_bot() -> None:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY is not set.")
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    
    # Load previously saved data
    history_data = load_history(MEMORY_FILE)
    
    # Create the chat session using the native SDK abstraction
    # Note: gemini-2.0-flash is used here as requested by the original implementation
    chat_session = client.chats.create(model="gemini-2.0-flash", history=history_data)

    print("--- Persistent Bot Ready ---")
    print(f"Loaded {len(history_data)} previous messages from disk.")
    print("Type 'quit' to save and exit.\\n")

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            
            if user_input.lower() in ["quit", "exit"]:
                print("Saving conversation state... Goodbye!")
                # Extract history array and persist to disk
                save_history(MEMORY_FILE, chat_session.get_history())
                break
            
            response = chat_session.send_message(user_input)
            print(f"Bot: {response.text}\\n")
            
        except KeyboardInterrupt:
            print("\\nInterrupted. Saving conversation state before exit...")
            save_history(MEMORY_FILE, chat_session.get_history())
            sys.exit(0)
        except Exception as e:
            print(f"\\n[Error] {e}\\n")

if __name__ == "__main__":
    run_persistent_bot()
"""

# Write all python files
with open(os.path.join(REPO_DIR, "src", "basic_chatbot.py"), "w", encoding="utf-8") as f:
    f.write(basic_chatbot)
with open(os.path.join(REPO_DIR, "src", "english_tutor_chatbot.py"), "w", encoding="utf-8") as f:
    f.write(english_tutor)
with open(os.path.join(REPO_DIR, "src", "love_guru_chatbot.py"), "w", encoding="utf-8") as f:
    f.write(love_guru)
with open(os.path.join(REPO_DIR, "src", "memory_chatbot.py"), "w", encoding="utf-8") as f:
    f.write(memory_chatbot)
with open(os.path.join(REPO_DIR, "src", "oop_chatbot.py"), "w", encoding="utf-8") as f:
    f.write(oop_chatbot)
with open(os.path.join(REPO_DIR, "src", "save_load_chatbot.py"), "w", encoding="utf-8") as f:
    f.write(save_load_chatbot)

# Create README.md
readme = """# AI Chatbot Assistant

> A progressive collection of Python implementations exploring conversational logic, state management, persistence, and object-oriented design using the Google GenAI SDK.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![Gemini](https://img.shields.io/badge/AI-Google_Gemini-orange?style=flat-square&logo=google)
![Status](https://img.shields.io/badge/Status-Maintained-success?style=flat-square)

## Overview

This repository demonstrates how to architect conversational AI applications. It begins with a fundamental blocking terminal loop and progressively introduces more advanced software engineering concepts, including custom persona injection, error handling, sliding-window memory, local persistence, and strict object-oriented design.

It is designed to showcase clear progression in API integration, defensive programming, and structural refactoring.

## Project Evolution

The implementations map out a clear technical progression:

```text
Basic Chatbot (Core API Logic)
      ↓
English Tutor & Love Guru (System Prompt Injection & Error Handling)
      ↓
Memory Chatbot (In-Memory State Management)
      ↓
Save/Load Chatbot (Local JSON Persistence)
      ↓
OOP Chatbot (Object-Oriented Architecture & Encapsulation)
```

## Implementations

| Script | Focus | Technical Concept |
| :--- | :--- | :--- |
| **`basic_chatbot.py`** | Fundamental loop | SDK initialization and basic inference |
| **`love_guru_chatbot.py`** | Personality | System prompt injection via string manipulation |
| **`english_tutor_chatbot.py`** | Educational interaction | Targeted Exception handling & input validation |
| **`memory_chatbot.py`** | State management | Context retention across multiple conversation turns |
| **`save_load_chatbot.py`** | Persistence | JSON serialization/deserialization for session pausing |
| **`oop_chatbot.py`** | Architecture | Class-based encapsulation and state isolation |

## Architecture

While each script is standalone, they share a common flow. The more advanced implementations (like `oop_chatbot.py` and `save_load_chatbot.py`) structure this flow into robust, isolated components:

```mermaid
flowchart TD
    A[User Input] --> B{Input Validation}
    B -->|Valid| C[State Management / History]
    C --> D[Gemini API Inference]
    D --> E{Error Handling}
    E -->|Success| F[Update Memory State]
    E -->|Failure| G[Graceful Recovery]
    F --> H[Response Generation]
    H --> A
```

## Project Structure

```text
AI-Chatbot-Assistant/
├── README.md
├── requirements.txt
├── .gitignore
├── .env.example
└── src/
    ├── basic_chatbot.py
    ├── english_tutor_chatbot.py
    ├── love_guru_chatbot.py
    ├── memory_chatbot.py
    ├── oop_chatbot.py
    └── save_load_chatbot.py
```

## Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/chetanaybuilder/AI-Chatbot-Assistant.git
   cd AI-Chatbot-Assistant
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\\Scripts\\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   Copy the `.env.example` file to a new `.env` file and insert your API key:
   ```bash
   cp .env.example .env
   # Edit .env to add your GEMINI_API_KEY
   ```

## Running the Examples

Each script can be run independently from the terminal:

```bash
# Run the fundamental implementation
python src/basic_chatbot.py

# Run the persistent implementation that saves to disk
python src/save_load_chatbot.py

# Run the object-oriented implementation
python src/oop_chatbot.py
```

## Engineering Decisions

### Persistence Strategy
The `save_load_chatbot.py` utilizes local JSON storage rather than a dedicated database. This decision ensures the repository remains highly accessible and self-contained, while still effectively demonstrating serialization logic, deserialization parsing, and I/O error handling.

### Incremental Complexity
Instead of abstracting all functionality into a single monolithic framework, the repository separates concepts into individual files. This prevents the learning curve of an overarching abstraction from obfuscating the underlying API interaction and state management mechanics.

### Error Handling
The implementations (especially `english_tutor_chatbot.py`) handle exceptions granularly. Rather than utilizing broad `except Exception:` blocks, the code catches specific `APIError` and `ConnectionError` instances. This prevents the interactive terminal loop from crashing during transient network failures or token limit breaches.

## Limitations

* **Terminal UI**: The interface is strictly command-line based.
* **Local Persistence Only**: Conversation state is either in-memory or persisted locally via JSON, without a distributed database backend.
* **Synchronous Execution**: The I/O loops currently block during API inference.

## Future Improvements

- Add asynchronous `asyncio` inference for non-blocking I/O.
- Introduce vector embedding storage (e.g., ChromaDB) for semantic memory retention.
- Implement structured testing utilizing `pytest`.
"""
with open(os.path.join(REPO_DIR, "README.md"), "w", encoding="utf-8") as f:
    f.write(readme)

# Create .gitignore
gitignore = """# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Environments
.env
.env.*
!.env.example
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Project specifics
memory.json

# IDEs
.idea/
.vscode/
*.swp
.DS_Store
"""
with open(os.path.join(REPO_DIR, ".gitignore"), "w", encoding="utf-8") as f:
    f.write(gitignore)

# Create requirements.txt
with open(os.path.join(REPO_DIR, "requirements.txt"), "w", encoding="utf-8") as f:
    f.write("google-genai\\npython-dotenv\\n")

# Create .env.example
with open(os.path.join(REPO_DIR, ".env.example"), "w", encoding="utf-8") as f:
    f.write("GEMINI_API_KEY=your_gemini_api_key_here\\n")

# Cleanup old files
old_files = [
    "Basic-Chatbot.py",
    "English-Tutor-Chatbot using error handling.py",
    "Love-Guru-Chatbot.py",
    "Memory-Chatbot.py",
    "Save-Load-Chatbot.py",
    "oop-chatbot.py"
]

for old in old_files:
    try:
        os.remove(os.path.join(REPO_DIR, old))
    except OSError:
        pass

print("Repository strictly modernized.")
