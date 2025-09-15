from flask import Flask
import os
import psycopg2

app = Flask(__name__)

def get_db_connection():
    # A real app would use better connection management
    conn = psycopg2.connect(
        host="db", # This is the service name in docker-compose.yml
        database=os.environ.get("POSTGRES_DB"),
        user=os.environ.get("POSTGRES_USER"),
        password=os.environ.get("POSTGRES_PASSWORD")
    )
    return conn

@app.route('/')
def hello_world():
    return "Hello from Flask!"

@app.route('/db')
def db_test():
    try:
        conn = get_db_connection()
        conn.close()
        return "✅ Database connection successful!"
    except Exception as e:
        return f"❌ Database connection failed: {e}"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)