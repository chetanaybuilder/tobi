from google import genai
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "chetanay"


# Keep your exact API key setup
client = genai.Client(api_key=os.environ("gemini_api_key"))
conn = sqlite3.connect("chatbot.db", check_same_thread=False)
cursor = conn.cursor()

# Your exact table setup
cursor.execute("""
CREATE TABLE IF NOT EXISTS messages(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_message TEXT,
bot_response TEXT)
""")
conn.commit()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT NOT NULL,
email TEXT UNIQUE NOT NULL,
password TEXT NOT NULL)
""")
conn.commit()

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/chat", methods=["GET", "POST"])
def index():
    if "user_id" not in session:
        return redirect("/login")
    response = ""
    rows = []
    if request.method == "POST":
        user_message = request.form.get("message")
        if user_message:
            # Your exact Gemini call
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
            
            cursor.execute("""
            INSERT INTO messages(user_message,bot_response)
            VALUES(?,?)
            """, (user_message, bot_reply))
            conn.commit()
            response = bot_reply
            
    cursor.execute("SELECT * FROM messages ORDER BY id")
    rows = cursor.fetchall()
    return render_template("index.html", response=response, chat_history=rows)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        
        print(username)
        print(email)
        print(password)
        
        try:
            cursor.execute("""
                INSERT INTO users(username,email,password) VALUES(?,?,?)""",
                (username, email, password)
            )
            conn.commit()
            
            # 👇 THIS IS THE ONLY LINE I ADDED 👇
            # After successful registration, push them to the login page!
            return redirect(url_for("login")) 
            
        except sqlite3.IntegrityError:
            # ignore duplicate email for simplicity
            pass
            
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        cursor.execute("""
            SELECT * FROM users WHERE email=? AND password=?""",
            (email, password)
        )
        
        user = cursor.fetchone()
        
        if user:
          session["user_id"] = user[0]  
          print(session)    
          return redirect(url_for("index"))
        else:
            return "invalid email or password"

            
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")



if __name__ == "__main__":
    app.run(debug=True)
    conn.close()