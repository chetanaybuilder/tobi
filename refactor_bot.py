import os
import shutil
import re

REPO_DIR = r"C:\Users\batra\Downloads\Tobi\tobi\Portfolio\AI-Chatbot-Assistant"
SRC_DIR = os.path.join(REPO_DIR, "src")

# Create src dir
os.makedirs(SRC_DIR, exist_ok=True)

# File mappings
files = {
    "Basic-Chatbot.py": "basic_chatbot.py",
    "English-Tutor-Chatbot using error handling.py": "english_tutor.py",
    "Love-Guru-Chatbot.py": "love_guru.py",
    "Memory-Chatbot.py": "memory_chatbot.py",
    "Save-Load-Chatbot.py": "save_load_chatbot.py",
    "oop-chatbot.py": "oop_chatbot.py"
}

for old, new in files.items():
    old_path = os.path.join(REPO_DIR, old)
    new_path = os.path.join(SRC_DIR, new)
    
    if os.path.exists(old_path):
        with open(old_path, "r", encoding="utf-8") as f:
            code = f.read()
            
        # Fix hardcoded API keys
        code = re.sub(r'api_key=["\'](.*?)["\']', 'api_key=os.environ.get("GEMINI_API_KEY")', code)
        code = re.sub(r'from google import genai', 'import os\nfrom google import genai\nfrom dotenv import load_dotenv\n\nload_dotenv()', code)
        
        with open(new_path, "w", encoding="utf-8") as f:
            f.write(code)
            
        os.remove(old_path)

# Create .env.example
with open(os.path.join(REPO_DIR, ".env.example"), "w") as f:
    f.write("GEMINI_API_KEY=your_gemini_api_key_here\n")

# Create requirements.txt
with open(os.path.join(REPO_DIR, "requirements.txt"), "w") as f:
    f.write("google-genai\npython-dotenv\n")

# Create a professional README
readme = """# AI Chatbot Assistant
> A collection of modular, specialized AI chatbot implementations using the Google GenAI SDK.

## Overview
This repository contains various architectural approaches to building conversational AI agents, ranging from simple procedural scripts to object-oriented memory-persisting chatbots. It demonstrates how to integrate streaming responses, handle API errors gracefully, and persist conversation state.

## Architecture
The repository is structured into distinct modules, each demonstrating a different core concept in conversational AI:
- **Basic Chatbot**: Fundamentals of API connection and content generation.
- **Memory Chatbot**: Implementing sliding-window conversation history.
- **Save/Load Chatbot**: Persisting conversation state to local disk.
- **English Tutor & Love Guru**: System-prompt engineering and specialized persona design.
- **OOP Chatbot**: A clean, scalable class-based architecture for managing agent state.

## Tech Stack
| Layer | Technology |
| --- | --- |
| Language | Python 3.10+ |
| AI Provider | Google Gemini API (gemini-2.5-flash) |
| Configuration | python-dotenv |

## Project Structure
```text
project/
├── src/
│   ├── basic_chatbot.py
│   ├── memory_chatbot.py
│   ├── oop_chatbot.py
│   └── ...
├── requirements.txt
├── .env.example
└── README.md
```

## Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/chetanaybuilder/AI-Chatbot-Assistant.git
   cd AI-Chatbot-Assistant
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   Copy the example environment file and add your Google Gemini API key:
   ```bash
   cp .env.example .env
   ```

4. **Run a Bot**
   ```bash
   python src/oop_chatbot.py
   ```

## Engineering Notes
- **State Management**: The `oop_chatbot.py` implementation moves away from global variables and uses encapsulated instance variables for thread-safe session history.
- **Error Handling**: The English Tutor bot demonstrates how to gracefully catch API rate limits and connection errors without crashing the interactive loop.
"""

with open(os.path.join(REPO_DIR, "README.md"), "w", encoding="utf-8") as f:
    f.write(readme)

print("AI-Chatbot-Assistant refactored successfully.")
