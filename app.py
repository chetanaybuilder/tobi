from google import genai
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "chetanay"

# Safely initialize Gemini Client
api_key = os.environ.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

# --- Database Setup & Auto-Migration ---
def init_db():
    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()
    
    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)
    
    # 2. Messages Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        user_message TEXT,
        bot_response TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    
    # 🛠️ AUTO-FIX: Check if 'user_id' exists in old local database files
    cursor.execute("PRAGMA table_info(messages)")
    columns = [column[1] for column in cursor.fetchall()]
    if "user_id" not in columns:
        try:
            cursor.execute("ALTER TABLE messages ADD COLUMN user_id INTEGER")
            conn.commit()
        except Exception:
            pass

    # 3. Default test user (always available)
    cursor.execute("""
    INSERT OR IGNORE INTO users (username, email, password)
    VALUES ('chetanay', 'admin@gmail.com', '123456')
    """)
    
    conn.commit()
    conn.close()

# Run database setup on startup
init_db()


# --- Routes ---

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/chat", methods=["GET", "POST"])
def chat():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    user_id = session["user_id"]
    response = ""

    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()

    if request.method == "POST":
        user_message = request.form.get("message")
        if user_message:
            if not client:
                bot_reply = "API key not configured!"
            else:
                try:
                    # Your EXACT Gemini Prompt Rules
                    result = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=f"""You are Chetanay AI.
                
                Rules:
                # RESPONSE RULES (VERY IMPORTANT)

You MUST strictly follow these formatting rules.

## General

- Keep answers concise.
- Default answer length: 80–150 words.
- Only give long answers if the user specifically asks for details.
- Never generate huge paragraphs.

---------------------------------

## Answer Structure

Always follow this structure.

Short introduction (2-3 lines)

(blank line)

**Heading**

(blank line)

• Bullet 1

• Bullet 2

• Bullet 3

(blank line)

✨ One-line conclusion.

---------------------------------

## Bullet Rules

Each bullet MUST be on its own separate line.

Correct:

• Easy to learn

• Beginner friendly

• Used in AI

Wrong:

• Easy to learn • Beginner friendly • Used in AI

Never put multiple bullets on one line.

---------------------------------

## Paragraph Rules

Maximum 2 sentences per paragraph.

After every paragraph leave one empty line.

Never create walls of text.

---------------------------------

## Length Rules

Simple question
→ Short answer

Medium question
→ Medium answer

Complex question
→ Detailed answer

Never over-explain.

---------------------------------

## Emoji Rules

Use only 1–2 Apple-style emojis.

Never spam emojis.

---------------------------------

## Markdown

Use:

# Heading

## Heading

**Bold**

• Bullet list

Never use numbered lists unless requested.

---------------------------------

## Example

Question:
What is Python?

Answer:

# 🐍 What is Python?

Python is a beginner-friendly programming language. It is widely used because it is simple, powerful, and easy to read.

**Why is Python popular?**

• Easy to learn

• Used for AI and web development

• Huge collection of libraries

✨ Python is one of the best languages for beginners.

---------------------------------

If you cannot follow these rules,
rewrite your answer until every rule is satisfied.
                
                {user_message}"""
                    )
                    bot_reply = getattr(result, "text", None) or str(result)
                except Exception as e:
                    bot_reply = f"Error calling AI: {str(e)}"
            
            cursor.execute("""
                INSERT INTO messages(user_id, user_message, bot_response)
                VALUES(?, ?, ?)
            """, (user_id, user_message, bot_reply))
            conn.commit()
            response = bot_reply

    cursor.execute("SELECT * FROM messages WHERE user_id = ? ORDER BY id", (user_id,))
    rows = cursor.fetchall()
    conn.close()

    return render_template("index.html", response=response, chat_history=rows)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        
        if not username or not email or not password:
            return render_template("register.html", error="All fields are required!")

        try:
            conn = sqlite3.connect("chatbot.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", 
                           (username, email, password))
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return render_template("register.html", error="Email already exists!")
        except Exception as e:
            return render_template("register.html", error=f"Database error: {str(e)}")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        conn = sqlite3.connect("chatbot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session["user_id"] = user[0]
            session["username"] = user[1]
            return redirect(url_for("chat"))
        else:
            return render_template("login.html", error="Invalid email or password")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)