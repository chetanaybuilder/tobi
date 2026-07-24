from google import genai
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "chetanay"

# Initialize Gemini Client
client = genai.Client(api_key=os.environ.get("gemini_api_key"))

# --- Database Setup (Runs on startup) ---
def init_db():
    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()
    
    # Table for storing user accounts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)
    
    # Table for storing user messages (linked to user_id)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        user_message TEXT,
        bot_response TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    
    conn.commit()
    conn.close()

# Run setup
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
            # Gemini Prompt Call
            result = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"""You are Chetanay AI.
                
                Rules:
                - Keep answers concise (80–150 words).
                - Use single-line bullet points starting with •.
                - Max 2 sentences per paragraph.
                - Use only 1-2 Apple-style emojis.
                
                User question: {user_message}"""
            )
            
            bot_reply = getattr(result, "text", None) or str(result)
            
            # Save message specific to current logged-in user
            cursor.execute("""
                INSERT INTO messages(user_id, user_message, bot_response)
                VALUES(?, ?, ?)
            """, (user_id, user_message, bot_reply))
            conn.commit()
            response = bot_reply

    # Fetch chat history ONLY for the logged-in user
    cursor.execute("SELECT * FROM messages WHERE user_id = ? ORDER BY id", (user_id,))
    rows = cursor.fetchall()
    conn.close()

    return render_template("index.html", response=response, chat_history=rows)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        
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

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

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