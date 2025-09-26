from datetime import datetime, timedelta
import os
import json

from flask import Flask, jsonify, request, redirect, url_for, session, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt
)
from werkzeug.security import generate_password_hash, check_password_hash
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
import requests

# Allow HTTP for local development (OAuth2 normally requires HTTPS)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# ------------------ App & Config ------------------
app = Flask(__name__)

# envs (set in .env / docker-compose)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://app:app@db:5432/app")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change_me")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-me")

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=12)
app.config["SECRET_KEY"] = SECRET_KEY

# Google OAuth Config
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid_configuration"

db = SQLAlchemy(app)
jwt = JWTManager(app)

# ------------------ Models ------------------
class Family(db.Model):
    __tablename__ = "families"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)  # Nullable for OAuth users
    google_id = db.Column(db.String(255), unique=True, nullable=True)  # Google OAuth ID
    name = db.Column(db.String(255), nullable=True)  # User's display name
    picture = db.Column(db.String(500), nullable=True)  # Profile picture URL
    family_id = db.Column(db.Integer, db.ForeignKey("families.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    family = db.relationship("Family")

class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey("families.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    monthly_budget = db.Column(db.Numeric(12, 2), default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Transaction(db.Model):
    __tablename__ = "transactions"
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey("families.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    transaction_type = db.Column(db.String(50), nullable=False)  # 'income', 'expense', 'bill'
    note = db.Column(db.String(255))
    occurred_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to Category
    category = db.relationship("Category", backref="transactions")

# ------------------ Helpers ------------------
def create_default_family(name: str) -> Family:
    fam = Family(name=name)
    db.session.add(fam)
    db.session.flush()  # get ID
    return fam

def token_claims(user: User):
    # claims for authZ (family scoping)
    return {"uid": user.id, "family_id": user.family_id, "email": user.email}

def get_google_provider_cfg():
    # Use hardcoded Google OAuth endpoints (more reliable than discovery)
    return {
        "authorization_endpoint": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_endpoint": "https://oauth2.googleapis.com/token",
        "userinfo_endpoint": "https://www.googleapis.com/oauth2/v2/userinfo"
    }

def create_oauth_flow():
    google_provider_cfg = get_google_provider_cfg()
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": google_provider_cfg["authorization_endpoint"],
                "token_uri": google_provider_cfg["token_endpoint"],
                "redirect_uris": ["http://localhost:8888/auth/google/callback", "http://127.0.0.1:8888/auth/google/callback"]
            }
        },
        scopes=["openid", "email", "profile"]
    )
    # Always use the correct redirect URI with port 8888
    flow.redirect_uri = "http://localhost:8888/auth/google/callback"
    return flow

# ------------------ Routes ------------------
@app.route("/")
def root():
    return redirect(url_for("budget_app"))

@app.route("/oauth-debug")
def oauth_debug():
    debug_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>OAuth Debug Info</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            .info {{ background: #f0f0f0; padding: 15px; margin: 10px 0; border-radius: 5px; }}
            .error {{ background: #ffe6e6; padding: 15px; margin: 10px 0; border-radius: 5px; }}
            code {{ background: #e0e0e0; padding: 2px 5px; }}
        </style>
    </head>
    <body>
        <h1>OAuth Configuration Debug</h1>
        
        <div class="info">
            <h3>Current Configuration:</h3>
            <p><strong>Client ID:</strong> <code>***HIDDEN***</code></p>
            <p><strong>Redirect URI:</strong> <code>http://localhost:8888/auth/google/callback</code></p>
            <p><strong>Scopes:</strong> <code>openid email profile</code></p>
        </div>
        
        <div class="info">
            <h3>Google Cloud Console Checklist:</h3>
            <ol>
                <li>Go to <a href="https://console.cloud.google.com/apis/credentials" target="_blank">Google Cloud Console - Credentials</a></li>
                <li>Find your OAuth 2.0 Client ID: <code>{GOOGLE_CLIENT_ID}</code></li>
                <li>Click on it to edit</li>
                <li>Verify "Authorized redirect URIs" contains exactly: <code>http://localhost:8888/auth/google/callback</code></li>
                <li>Check OAuth consent screen is configured</li>
                <li>If app is in testing mode, add your email as a test user</li>
            </ol>
        </div>
        
        <div class="info">
            <h3>Test OAuth Flow:</h3>
            <p><a href="/auth/google" style="background: #4285f4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">🔗 Test Google OAuth</a></p>
        </div>
        
        <div class="info">
            <h3>Manual OAuth URL:</h3>
            <p>If the button doesn't work, try this URL directly:</p>
            <textarea style="width: 100%; height: 100px;" readonly>OAuth URL hidden for security</textarea>
        </div>
        
        <p><a href="/login">← Back to Login Page</a></p>
    </body>
    </html>
    """
    return debug_html

@app.route("/login")
def login_page():
    login_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Budget App - Login</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            
            .login-container {
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                padding: 40px;
                width: 100%;
                max-width: 400px;
                text-align: center;
            }
            
            .logo {
                font-size: 2.5rem;
                font-weight: bold;
                color: #333;
                margin-bottom: 10px;
            }
            
            .subtitle {
                color: #666;
                margin-bottom: 40px;
                font-size: 1.1rem;
            }
            
            .auth-section {
                margin-bottom: 30px;
            }
            
            .section-title {
                font-size: 1.2rem;
                font-weight: 600;
                color: #333;
                margin-bottom: 20px;
            }
            
            .google-btn {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 100%;
                padding: 12px 20px;
                border: 2px solid #e0e0e0;
                border-radius: 50px;
                background: white;
                color: #333;
                text-decoration: none;
                font-weight: 500;
                font-size: 1rem;
                transition: all 0.3s ease;
                margin-bottom: 20px;
            }
            
            .google-btn:hover {
                border-color: #4285f4;
                box-shadow: 0 4px 12px rgba(66, 133, 244, 0.2);
                transform: translateY(-2px);
            }
            
            .google-icon {
                width: 20px;
                height: 20px;
                margin-right: 12px;
            }
            

        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="logo">💰 Budget App</div>
            <div class="subtitle">Manage your family finances</div>
            
            <div class="auth-section">
                <div class="section-title">Sign in with Google</div>
                <a href="{{ url_for('google_login') }}" class="google-btn">
                    <svg class="google-icon" viewBox="0 0 24 24">
                        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                    </svg>
                    Continue with Google
                </a>
                <div style="margin: 20px 0; color: #999; font-size: 0.9rem;">OR</div>
                <a href="/demo" class="google-btn" style="background: #28a745; color: white; border-color: #28a745;">
                    🚀 Skip Login (Demo Mode)
                </a>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(login_html)

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "time": datetime.utcnow().isoformat()}), 200

@app.route("/db")
def db_test():
    try:
        # simple query to ensure DB up
        db.session.execute(db.text("SELECT 1"))
        return "✅ Database connection successful!"
    except Exception as e:
        return f"❌ Database connection failed: {e}"

# -------- Auth --------
@app.route("/api/auth/register", methods=["POST"])
def register():
    payload = request.get_json(force=True)
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password")
    family_name = (payload.get("family_name") or "").strip()

    if not email or not password or not family_name:
        return jsonify({"error": "email, password, family_name are required"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "user already exists"}), 409

    fam = Family.query.filter_by(name=family_name).first()
    if not fam:
        fam = create_default_family(family_name)

    user = User(
        email=email,
        password_hash=generate_password_hash(password),
        family_id=fam.id,
    )
    db.session.add(user)
    db.session.commit()

    access = create_access_token(identity=email, additional_claims=token_claims(user))
    return jsonify({"access_token": access, "user_id": user.id, "family_id": fam.id}), 201

@app.route("/demo")
def demo_login():
    """Demo mode - create a temporary session and clear any existing auth"""
    # Clear any existing session data
    session.clear()
    
    # Create or get demo user
    demo_user = User.query.filter_by(email="demo@budgetapp.local").first()
    if not demo_user:
        # Create demo family first (without admin_user_id)
        demo_family = Family(name="Demo Family")
        db.session.add(demo_family)
        db.session.flush()  # Get the family.id
        
        # Create demo user with family_id
        demo_user = User(
            email="demo@budgetapp.local",
            google_id="demo_user",
            name="Demo User",
            picture="",
            password_hash=None,
            family_id=demo_family.id
        )
        db.session.add(demo_user)
        db.session.flush()  # Get the user.id
        
        # Update family with admin_user_id
        demo_family.admin_user_id = demo_user.id
        db.session.commit()
        
        # Create default categories for demo family
        create_default_categories()
    
    # Set fresh session
    session['user_id'] = demo_user.id
    session['family_id'] = demo_user.family_id
    session['demo_mode'] = True  # Flag to indicate demo mode
    
    # Return HTML that clears localStorage and redirects
    demo_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Demo Mode</title>
    </head>
    <body>
        <div style="text-align: center; padding: 50px; font-family: Arial;">
            <h2>🚀 Starting Demo Mode...</h2>
            <p>Clearing previous session data...</p>
        </div>
        <script>
            // Clear any existing tokens
            localStorage.clear();
            
            // Set demo tokens for the budget app
            localStorage.setItem('access_token', 'demo_token_' + Date.now());
            localStorage.setItem('user_id', '{demo_user.id}');
            localStorage.setItem('family_id', '{demo_user.family_id}');
            
            // Redirect to budget app
            setTimeout(() => {{
                window.location.href = '/budget';
            }}, 1000);
        </script>
    </body>
    </html>
    """
    return demo_html

@app.route("/budget")
def budget_app():
    budget_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Simple Budget App</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body {
                font-family: Arial, sans-serif;
                background: #f0f0f0;
                padding: 20px;
            }
            
            .header {
                background: #4CAF50;
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 10px;
                margin-bottom: 20px;
            }
            
            .user-indicator {
                position: fixed;
                top: 20px;
                right: 20px;
                background: rgba(255, 255, 255, 0.95);
                border-radius: 25px;
                padding: 10px 15px;
                box-shadow: 0 2px 15px rgba(0,0,0,0.1);
                display: flex;
                align-items: center;
                gap: 10px;
                font-size: 0.9rem;
                z-index: 1000;
                border: 1px solid #e0e0e0;
                backdrop-filter: blur(10px);
            }
            
            .user-avatar {
                width: 30px;
                height: 30px;
                border-radius: 50%;
                object-fit: cover;
            }
            
            .demo-badge {
                background: linear-gradient(135deg, #28a745, #20c997);
                color: white;
                padding: 5px 10px;
                border-radius: 15px;
                font-size: 0.8rem;
                font-weight: bold;
            }
            
            .oauth-info {
                display: flex;
                flex-direction: column;
                line-height: 1.3;
            }
            
            .oauth-name {
                font-weight: bold;
                color: #333;
            }
            
            .oauth-email {
                color: #666;
                font-size: 0.8rem;
            }
            
            .container {
                max-width: 600px;
                margin: 0 auto;
            }
            
            .balance {
                background: white;
                padding: 30px;
                border-radius: 10px;
                text-align: center;
                margin-bottom: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            
            .balance-amount {
                font-size: 3rem;
                font-weight: bold;
                color: #4CAF50;
            }
            
            .quick-buttons {
                display: grid;
                grid-template-columns: 1fr 1fr 1fr;
                gap: 15px;
                margin-bottom: 30px;
            }
            
            .quick-btn {
                background: white;
                border: none;
                padding: 20px;
                border-radius: 10px;
                cursor: pointer;
                font-size: 1.1rem;
                font-weight: bold;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                transition: all 0.3s;
            }
            
            .quick-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            }
            
            .income-btn { border-left: 5px solid #4CAF50; }
            .expense-btn { border-left: 5px solid #f44336; }
            .bill-btn { border-left: 5px solid #ff9800; }
            
            .form-section {
                background: white;
                padding: 25px;
                border-radius: 10px;
                margin-bottom: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                display: none;
            }
            
            .form-section.active {
                display: block;
            }
            
            .form-group {
                margin-bottom: 15px;
            }
            
            .form-group label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
            }
            
            .form-group input {
                width: 100%;
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 1rem;
            }
            
            .submit-btn {
                background: #4CAF50;
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 5px;
                font-size: 1.1rem;
                font-weight: bold;
                cursor: pointer;
                width: 100%;
            }
            
            .submit-btn:hover {
                background: #45a049;
            }
            
            .cancel-btn {
                background: #f44336;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                margin-right: 10px;
            }
            
            .summary {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            
            .summary-item {
                display: flex;
                justify-content: space-between;
                padding: 10px 0;
                border-bottom: 1px solid #eee;
            }
            
            .logout-btn {
                background: #f44336;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                text-decoration: none;
                display: inline-block;
                margin-top: 10px;
            }
        </style>
    </head>
    <body>
        <!-- User Indicator -->
        <div class="user-indicator" id="userIndicator">
            <div class="demo-badge">Loading...</div>
        </div>
        
        <div class="container">
            <div class="header">
                <h1>💰 Simple Budget App</h1>
                <p>Click buttons to add income, expenses, or bills</p>
                <a href="/auth/logout" class="logout-btn">Logout</a>
            </div>
            
            <div class="balance">
                <div>Current Balance</div>
                <div class="balance-amount" id="balance">₪0.00</div>
            </div>
            
                         <div class="quick-buttons">
                 <button class="quick-btn income-btn" onclick="showForm('income')">
                     💵<br>Add Income
                 </button>
                 <button class="quick-btn expense-btn" onclick="showForm('expense')">
                     💸<br>Add Expense
                 </button>
                 <button class="quick-btn bill-btn" onclick="showForm('bill')">
                     📄<br>Add Bill
                 </button>
                 <button class="quick-btn" onclick="window.location.href='/history'" style="border-left: 5px solid #9c27b0;">
                     📊<br>View History
                 </button>
             </div>
            
                         <div id="incomeForm" class="form-section">
                 <h3>💵 Add Income</h3>
                 <form onsubmit="addTransaction(event, 'income')">
                     <div class="form-group">
                         <label>Date</label>
                         <input type="date" required>
                     </div>
                     <div class="form-group">
                         <label>Category</label>
                         <input type="text" class="category-input" required placeholder="e.g., Salary, Bonus">
                     </div>
                     <div class="form-group">
                         <label>Amount (₪)</label>
                         <input type="number" step="0.01" required placeholder="e.g., 3000">
                     </div>
                     <div class="form-group">
                         <label>Description</label>
                         <input type="text" required placeholder="e.g., Salary, Freelance">
                     </div>
                     <button type="button" class="cancel-btn" onclick="hideForm()">Cancel</button>
                     <button type="submit" class="submit-btn">Add Income</button>
                 </form>
             </div>
            
                         <div id="expenseForm" class="form-section">
                 <h3>💸 Add Expense</h3>
                 <form onsubmit="addTransaction(event, 'expense')">
                     <div class="form-group">
                         <label>Date</label>
                         <input type="date" required>
                     </div>
                     <div class="form-group">
                         <label>Category</label>
                         <input type="text" class="category-input" required placeholder="e.g., Groceries, Shopping">
                     </div>
                     <div class="form-group">
                         <label>Amount (₪)</label>
                         <input type="number" step="0.01" required placeholder="e.g., 50">
                     </div>
                     <div class="form-group">
                         <label>Description</label>
                         <input type="text" required placeholder="e.g., Groceries, Gas">
                     </div>
                     <button type="button" class="cancel-btn" onclick="hideForm()">Cancel</button>
                     <button type="submit" class="submit-btn">Add Expense</button>
                 </form>
             </div>
            
                         <div id="billForm" class="form-section">
                 <h3>📄 Add Bill</h3>
                 <form onsubmit="addTransaction(event, 'bill')">
                     <div class="form-group">
                         <label>Date</label>
                         <input type="date" required>
                     </div>
                     <div class="form-group">
                         <label>Category</label>
                         <input type="text" class="category-input" required placeholder="e.g., Utilities, Rent">
                     </div>
                     <div class="form-group">
                         <label>Amount (₪)</label>
                         <input type="number" step="0.01" required placeholder="e.g., 100">
                     </div>
                     <div class="form-group">
                         <label>Description</label>
                         <input type="text" required placeholder="e.g., Electric, Internet">
                     </div>
                     <button type="button" class="cancel-btn" onclick="hideForm()">Cancel</button>
                     <button type="submit" class="submit-btn">Add Bill</button>
                 </form>
             </div>
            
            <div class="summary">
                <h3>Summary</h3>
                <div class="summary-item">
                    <span>💵 Total Income:</span>
                    <span id="totalIncome">₪0.00</span>
                </div>
                <div class="summary-item">
                    <span>💸 Total Expenses:</span>
                    <span id="totalExpenses">₪0.00</span>
                </div>
                <div class="summary-item">
                    <span>📄 Total Bills:</span>
                    <span id="totalBills">₪0.00</span>
                </div>
            </div>
            
            <div class="summary">
                <h3>📊 Categories This Month</h3>
                <div id="categoryBreakdown">
                    <p>Loading categories...</p>
                </div>
            </div>
        </div>
        
        <script>
            const token = localStorage.getItem('access_token');
            if (!token) {
                window.location.href = '/login';
            }
            
            // Initialize user indicator
            function initUserIndicator() {
                const userIndicator = document.getElementById('userIndicator');
                const userId = localStorage.getItem('user_id');
                const familyId = localStorage.getItem('family_id');
                
                // Check if this is demo mode
                if (token && token.startsWith('demo_token_')) {
                    userIndicator.innerHTML = '<div class="demo-badge">🚀 Demo Mode</div>';
                    return;
                }
                
                // For OAuth users, fetch user info from session/API
                fetch('/api/user-info', {
                    headers: {
                        'Authorization': 'Bearer ' + token
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.picture && data.name) {
                        // OAuth user with profile
                        userIndicator.innerHTML = `
                            <img src="${data.picture}" alt="Profile" class="user-avatar" onerror="this.style.display='none'">
                            <div class="oauth-info">
                                <div class="oauth-name">${data.name}</div>
                                <div class="oauth-email">${data.email || ''}</div>
                            </div>
                        `;
                    } else {
                        // Fallback for users without profile info
                        userIndicator.innerHTML = `
                            <div class="oauth-info">
                                <div class="oauth-name">👤 User</div>
                                <div class="oauth-email">${data.email || 'Authenticated'}</div>
                            </div>
                        `;
                    }
                })
                .catch(error => {
                    // Fallback if API fails
                    userIndicator.innerHTML = '<div class="demo-badge">👤 Logged In</div>';
                });
            }
            
            // Initialize on page load
            initUserIndicator();

            
            function showForm(type) {
                hideForm();
                const form = document.getElementById(type + 'Form');
                form.classList.add('active');
                
                // Set today's date as default
                const dateInput = form.querySelector('input[type="date"]');
                if (dateInput) {
                    const today = new Date().toISOString().split('T')[0];
                    dateInput.value = today;
                }
                

            }
            
            function hideForm() {
                document.querySelectorAll('.form-section').forEach(form => {
                    form.classList.remove('active');
                });
            }
            
            async function addTransaction(event, type) {
                event.preventDefault();
                
                const form = event.target;
                const date = form.querySelector('input[type="date"]').value;
                const categoryId = form.querySelector('.category-input').value;
                const amount = parseFloat(form.querySelector('input[type="number"]').value);
                const description = form.querySelector('input[type="text"]').value;
                
                try {
                    const response = await fetch('/api/budget/transaction', {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${token}`,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ type, amount, description, date, categoryId })
                    });
                    
                    if (response.ok) {
                        form.reset();
                        hideForm();
                        loadBudgetData();
                    } else {
                        alert('Error adding transaction');
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            }
            
            async function loadBudgetData() {
                try {
                    const response = await fetch('/api/budget/summary', {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    
                    if (response.ok) {
                        const data = await response.json();
                        document.getElementById('balance').textContent = `₪${data.balance.toFixed(2)}`;
                        document.getElementById('totalIncome').textContent = `₪${data.income.toFixed(2)}`;
                        document.getElementById('totalExpenses').textContent = `₪${data.expenses.toFixed(2)}`;
                        document.getElementById('totalBills').textContent = `₪${data.bills.toFixed(2)}`;
                        
                        // Update category breakdown
                        const categoryDiv = document.getElementById('categoryBreakdown');
                        if (data.categories && data.categories.length > 0) {
                            let categoryHtml = '';
                            data.categories.forEach(cat => {
                                categoryHtml += `
                                    <div class="summary-item">
                                        <span>📂 ${cat.name}:</span>
                                        <span>₪${cat.amount.toFixed(2)}</span>
                                    </div>
                                `;
                            });
                            categoryDiv.innerHTML = categoryHtml;
                        } else {
                            categoryDiv.innerHTML = '<p>No transactions this month</p>';
                        }
                    }
                } catch (error) {
                    console.error('Error loading budget data:', error);
                }
            }
            
            // Load data when page loads
            loadBudgetData();
        </script>
    </body>
    </html>
    """
    return budget_html

@app.route("/history")
def history_page():
    history_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Transaction History</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body {
                font-family: Arial, sans-serif;
                background: #f0f0f0;
                padding: 20px;
            }
            
            .header {
                background: #9c27b0;
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 10px;
                margin-bottom: 20px;
            }
            
            .container {
                max-width: 1000px;
                margin: 0 auto;
            }
            
            .nav-buttons {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
            }
            
            .nav-btn {
                background: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
            }
            
            .filters {
                background: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            
            .filter-group {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-bottom: 15px;
            }
            
            .filter-group label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
            }
            
            .filter-group input, .filter-group select {
                width: 100%;
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 5px;
            }
            
            .charts-section {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-bottom: 20px;
            }
            
            .chart-container {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            
            .chart-container h3 {
                text-align: center;
                margin-bottom: 15px;
                color: #333;
            }
            
            .history-section {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            
            .transaction-item {
                display: grid;
                grid-template-columns: 100px 1fr 100px 80px;
                gap: 15px;
                padding: 15px;
                border-bottom: 1px solid #eee;
                align-items: center;
            }
            
            .transaction-item:hover {
                background: #f9f9f9;
            }
            
            .transaction-date {
                font-size: 0.9rem;
                color: #666;
            }
            
            .transaction-desc {
                font-weight: bold;
            }
            
            .desc-text {
                margin-bottom: 4px;
            }
            
            .category-tag {
                font-size: 0.85em;
                color: #666;
                background: #f0f0f0;
                padding: 2px 8px;
                border-radius: 12px;
                display: inline-block;
                font-weight: normal;
            }
            
            .transaction-amount {
                font-weight: bold;
                text-align: right;
            }
            
            .transaction-type {
                padding: 4px 8px;
                border-radius: 15px;
                font-size: 0.8rem;
                text-align: center;
                color: white;
            }
            
            .type-income { background: #4CAF50; }
            .type-expense { background: #f44336; }
            .type-bill { background: #ff9800; }
            
            .delete-btn {
                background: #f44336;
                color: white;
                border: none;
                border-radius: 50%;
                width: 30px;
                height: 30px;
                cursor: pointer;
                font-size: 14px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-left: 10px;
                transition: background 0.3s;
            }
            
            .delete-btn:hover {
                background: #d32f2f;
                transform: scale(1.1);
            }
            
            .no-data {
                text-align: center;
                color: #666;
                padding: 40px;
            }
            
            @media (max-width: 768px) {
                .charts-section {
                    grid-template-columns: 1fr;
                }
                
                .transaction-item {
                    grid-template-columns: 1fr;
                    gap: 5px;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Transaction History</h1>
                <p>View your spending patterns and transaction history</p>
            </div>
            
            <div class="nav-buttons">
                <a href="/budget" class="nav-btn">← Back to Budget</a>
                <button class="nav-btn" onclick="exportData()">📥 Export Data</button>
            </div>
            
            <div class="filters">
                <h3>Filters</h3>
                <div class="filter-group">
                    <div>
                        <label>From Date</label>
                        <input type="date" id="fromDate">
                    </div>
                    <div>
                        <label>To Date</label>
                        <input type="date" id="toDate">
                    </div>
                    <div>
                        <label>Type</label>
                        <select id="typeFilter">
                            <option value="">All Types</option>
                            <option value="income">Income</option>
                            <option value="expense">Expense</option>
                            <option value="bill">Bill</option>
                        </select>
                    </div>
                    <div>
                        <button class="nav-btn" onclick="applyFilters()" style="margin-top: 25px;">Apply Filters</button>
                    </div>
                </div>
            </div>
            
            <div class="charts-section">
                <div class="chart-container">
                    <h3>💸 Expenses by Category</h3>
                    <canvas id="expenseChart" width="300" height="300"></canvas>
                </div>
                
                <div class="chart-container">
                    <h3>📊 Monthly Overview</h3>
                    <canvas id="monthlyChart" width="300" height="300"></canvas>
                </div>
            </div>
            
            <div class="history-section">
                <h3>Transaction History</h3>
                <div id="transactionsList">
                    <div class="no-data">Loading transactions...</div>
                </div>
            </div>
        </div>
        
        <script>
            const token = localStorage.getItem('access_token');
            if (!token) {
                window.location.href = '/login';
            }
            
            let allTransactions = [];
            let expenseChart = null;
            let monthlyChart = null;
            
            // Set default dates (last 30 days)
            const today = new Date();
            const thirtyDaysAgo = new Date(today.getTime() - (30 * 24 * 60 * 60 * 1000));
            document.getElementById('toDate').value = today.toISOString().split('T')[0];
            document.getElementById('fromDate').value = thirtyDaysAgo.toISOString().split('T')[0];
            
            async function loadTransactions() {
                try {
                    const response = await fetch('/api/budget/transactions', {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    
                    if (response.ok) {
                        allTransactions = await response.json();
                        applyFilters();
                    } else {
                        document.getElementById('transactionsList').innerHTML = '<div class="no-data">Error loading transactions</div>';
                    }
                } catch (error) {
                    console.error('Error loading transactions:', error);
                    document.getElementById('transactionsList').innerHTML = '<div class="no-data">Error loading transactions</div>';
                }
            }
            
            function applyFilters() {
                const fromDate = document.getElementById('fromDate').value;
                const toDate = document.getElementById('toDate').value;
                const typeFilter = document.getElementById('typeFilter').value;
                
                let filtered = allTransactions.filter(t => {
                    const tDate = new Date(t.date);
                    const matchesDate = (!fromDate || tDate >= new Date(fromDate)) && 
                                       (!toDate || tDate <= new Date(toDate));
                    const matchesType = !typeFilter || t.type === typeFilter;
                    return matchesDate && matchesType;
                });
                
                displayTransactions(filtered);
                updateCharts(filtered);
            }
            
            function displayTransactions(transactions) {
                const container = document.getElementById('transactionsList');
                
                if (transactions.length === 0) {
                    container.innerHTML = '<div class="no-data">No transactions found for the selected filters</div>';
                    return;
                }
                
                const html = transactions.map(t => `
                    <div class="transaction-item">
                        <div class="transaction-date">${new Date(t.date).toLocaleDateString()}</div>
                        <div class="transaction-desc">
                            <div class="desc-text">${t.description}</div>
                            <div class="category-tag">📂 ${t.category}</div>
                        </div>
                        <div class="transaction-amount">₪${t.amount.toFixed(2)}</div>
                        <div class="transaction-type type-${t.type}">${t.type}</div>
                        <button class="delete-btn" onclick="deleteTransaction(${t.id})" title="Delete transaction">🗑️</button>
                    </div>
                `).join('');
                
                container.innerHTML = html;
            }
            
            function updateCharts(transactions) {
                updateExpenseChart(transactions);
                updateMonthlyChart(transactions);
            }
            
            function updateExpenseChart(transactions) {
                const expenses = transactions.filter(t => t.type === 'expense' || t.type === 'bill');
                const categories = {};
                
                expenses.forEach(t => {
                    const category = t.category || 'Other';
                    categories[category] = (categories[category] || 0) + t.amount;
                });
                
                const ctx = document.getElementById('expenseChart').getContext('2d');
                
                if (expenseChart) {
                    expenseChart.destroy();
                }
                
                expenseChart = new Chart(ctx, {
                    type: 'pie',
                    data: {
                        labels: Object.keys(categories),
                        datasets: [{
                            data: Object.values(categories),
                            backgroundColor: ['#f44336', '#ff9800', '#9c27b0', '#2196f3', '#4caf50']
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'bottom'
                            }
                        }
                    }
                });
            }
            
            function updateMonthlyChart(transactions) {
                const monthly = {};
                
                transactions.forEach(t => {
                    const month = new Date(t.date).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
                    if (!monthly[month]) {
                        monthly[month] = { income: 0, expenses: 0, bills: 0 };
                    }
                    monthly[month][t.type] += t.amount;
                });
                
                const months = Object.keys(monthly).sort();
                const incomeData = months.map(m => monthly[m].income);
                const expenseData = months.map(m => monthly[m].expenses);
                const billData = months.map(m => monthly[m].bills);
                
                const ctx = document.getElementById('monthlyChart').getContext('2d');
                
                if (monthlyChart) {
                    monthlyChart.destroy();
                }
                
                monthlyChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: months,
                        datasets: [
                            {
                                label: 'Income',
                                data: incomeData,
                                backgroundColor: '#4caf50'
                            },
                            {
                                label: 'Expenses',
                                data: expenseData,
                                backgroundColor: '#f44336'
                            },
                            {
                                label: 'Bills',
                                data: billData,
                                backgroundColor: '#ff9800'
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            }
            
            function exportData() {
                const fromDate = document.getElementById('fromDate').value;
                const toDate = document.getElementById('toDate').value;
                const typeFilter = document.getElementById('typeFilter').value;
                
                let filtered = allTransactions.filter(t => {
                    const tDate = new Date(t.date);
                    const matchesDate = (!fromDate || tDate >= new Date(fromDate)) && 
                                       (!toDate || tDate <= new Date(toDate));
                    const matchesType = !typeFilter || t.type === typeFilter;
                    return matchesDate && matchesType;
                });
                
                const csv = 'Date,Description,Amount (₪),Type\\n' + 
                           filtered.map(t => `${t.date},"${t.description}",₪${t.amount},${t.type}`).join('\\n');
                
                const blob = new Blob([csv], { type: 'text/csv' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `transactions_${fromDate}_to_${toDate}.csv`;
                a.click();
                window.URL.revokeObjectURL(url);
            }
            
            // Delete transaction function
            async function deleteTransaction(transactionId) {
                if (!confirm('Are you sure you want to delete this transaction? This action cannot be undone.')) {
                    return;
                }
                
                try {
                    const response = await fetch(`/api/budget/transaction/${transactionId}`, {
                        method: 'DELETE',
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    });
                    
                    if (response.ok) {
                        // Reload transactions to update the display
                        loadTransactions();
                        alert('Transaction deleted successfully!');
                    } else {
                        const error = await response.json();
                        alert('Error deleting transaction: ' + (error.error || 'Unknown error'));
                    }
                } catch (error) {
                    console.error('Error deleting transaction:', error);
                    alert('Error deleting transaction. Please try again.');
                }
            }
            
            // Load data when page loads
            loadTransactions();
        </script>
    </body>
    </html>
    """
    return history_html

@app.route("/dashboard")
def dashboard():
    dashboard_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Budget App - Dashboard</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: #f8f9fa;
                min-height: 100vh;
            }
            
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px 0;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            
            .header-content {
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .logo {
                font-size: 1.5rem;
                font-weight: bold;
            }
            
            .user-info {
                display: flex;
                align-items: center;
                gap: 15px;
            }
            
            .logout-btn {
                background: rgba(255,255,255,0.2);
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 20px;
                cursor: pointer;
                text-decoration: none;
                font-size: 0.9rem;
            }
            
            .logout-btn:hover {
                background: rgba(255,255,255,0.3);
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 40px 20px;
            }
            
            .welcome-card {
                background: white;
                border-radius: 15px;
                padding: 30px;
                margin-bottom: 30px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                text-align: center;
            }
            
            .welcome-title {
                font-size: 2rem;
                font-weight: bold;
                color: #333;
                margin-bottom: 10px;
            }
            
            .welcome-subtitle {
                color: #666;
                font-size: 1.1rem;
            }
            
            .navigation-buttons {
                display: flex;
                gap: 15px;
                justify-content: center;
                flex-wrap: wrap;
            }
            
            .nav-button {
                padding: 12px 24px;
                border-radius: 25px;
                text-decoration: none;
                font-weight: 600;
                font-size: 1rem;
                transition: all 0.3s ease;
                display: inline-flex;
                align-items: center;
                gap: 8px;
            }
            
            .nav-button.primary {
                background: #4CAF50;
                color: white;
            }
            
            .nav-button.primary:hover {
                background: #45a049;
                transform: translateY(-2px);
            }
            
            .nav-button.secondary {
                background: #2196F3;
                color: white;
            }
            
            .nav-button.secondary:hover {
                background: #1976D2;
                transform: translateY(-2px);
            }
            
            .nav-button.logout {
                background: #f44336;
                color: white;
            }
            
            .nav-button.logout:hover {
                background: #d32f2f;
                transform: translateY(-2px);
            }
            
            .features-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-top: 30px;
            }
            
            .feature-card {
                background: white;
                border-radius: 15px;
                padding: 25px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                text-align: center;
                transition: transform 0.3s ease;
            }
            
            .feature-card:hover {
                transform: translateY(-5px);
            }
            
            .feature-icon {
                font-size: 3rem;
                margin-bottom: 15px;
            }
            
            .feature-title {
                font-size: 1.3rem;
                font-weight: bold;
                color: #333;
                margin-bottom: 10px;
            }
            
            .feature-description {
                color: #666;
                line-height: 1.5;
            }
            
            .api-info {
                background: white;
                border-radius: 15px;
                padding: 25px;
                margin-top: 30px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }
            
            .api-title {
                font-size: 1.5rem;
                font-weight: bold;
                color: #333;
                margin-bottom: 15px;
            }
            
            .token-display {
                background: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 15px;
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                font-size: 0.9rem;
                word-break: break-all;
                margin-bottom: 15px;
            }
            
            .api-endpoints {
                margin-top: 20px;
            }
            
            .endpoint {
                background: #f8f9fa;
                border-left: 4px solid #667eea;
                padding: 10px 15px;
                margin-bottom: 10px;
                border-radius: 0 8px 8px 0;
            }
            
            .method {
                font-weight: bold;
                color: #667eea;
                margin-right: 10px;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <div class="logo">💰 Budget App</div>
                <div class="user-info">
                    <span id="userEmail">Loading...</span>
                    <a href="/auth/logout" class="logout-btn">Logout</a>
                </div>
            </div>
        </div>
        
        <div class="container">
            <div class="welcome-card">
                <div class="welcome-title">Welcome to Your Budget Dashboard!</div>
                <div class="welcome-subtitle">Manage your family finances with ease</div>
                
                <div class="navigation-buttons" style="margin-top: 30px;">
                    <a href="/budget" class="nav-button primary">💰 Budget Manager</a>
                    <a href="/history" class="nav-button secondary">📊 View History</a>
                    <a href="/auth/logout" class="nav-button logout">🚪 Logout</a>
                </div>
            </div>
            
            <div class="features-grid">
                <div class="feature-card">
                    <div class="feature-icon">📊</div>
                    <div class="feature-title">Track Expenses</div>
                    <div class="feature-description">Monitor your spending across different categories and stay within budget.</div>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">👨‍👩‍👧‍👦</div>
                    <div class="feature-title">Family Sharing</div>
                    <div class="feature-description">Share budgets and expenses with your family members securely.</div>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">🎯</div>
                    <div class="feature-title">Budget Goals</div>
                    <div class="feature-description">Set monthly budgets for categories and track your progress.</div>
                </div>
            </div>
            
            <div class="api-info">
                <div class="api-title">API Access</div>
                <p>Your authentication token (stored in localStorage):</p>
                <div class="token-display" id="tokenDisplay">Loading...</div>
                
                <div class="api-endpoints">
                    <div class="endpoint">
                        <span class="method">GET</span>
                        <code>/api/categories</code> - List all categories
                    </div>
                    <div class="endpoint">
                        <span class="method">POST</span>
                        <code>/api/categories</code> - Create new category
                    </div>
                    <div class="endpoint">
                        <span class="method">GET</span>
                        <code>/api/health</code> - Health check
                    </div>
                </div>
                
                <p style="margin-top: 15px; color: #666; font-size: 0.9rem;">
                    Include your token in the Authorization header: <code>Bearer YOUR_TOKEN</code>
                </p>
            </div>
        </div>
        
        <script>
            // Load user info from localStorage
            const token = localStorage.getItem('access_token');
            const userEmail = localStorage.getItem('user_email') || 'User';
            
            if (!token) {
                window.location.href = '/login';
            } else {
                document.getElementById('tokenDisplay').textContent = token;
                
                // Try to decode JWT to get email (basic decode, not secure validation)
                try {
                    const payload = JSON.parse(atob(token.split('.')[1]));
                    document.getElementById('userEmail').textContent = payload.sub || userEmail;
                } catch (e) {
                    document.getElementById('userEmail').textContent = userEmail;
                }
            }
        </script>
    </body>
    </html>
    """
    return dashboard_html

@app.route("/api/auth/login", methods=["POST"])
def login():
    payload = request.get_json(force=True)
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password")

    user = User.query.filter_by(email=email).first()
    if not user or not user.password_hash or not check_password_hash(user.password_hash, password or ""):
        return jsonify({"error": "invalid credentials"}), 401

    access = create_access_token(identity=email, additional_claims=token_claims(user))
    return jsonify({"access_token": access, "user_id": user.id, "family_id": user.family_id}), 200

# -------- Google OAuth Routes --------
@app.route("/auth/google")
def google_login():
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return jsonify({"error": "Google OAuth not configured"}), 500
    
    try:
        flow = create_oauth_flow()
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        session['state'] = state
        return redirect(authorization_url)
    except Exception as e:
        return jsonify({"error": f"OAuth setup failed: {str(e)}"}), 500

@app.route("/auth/google/callback")
def google_callback():
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return jsonify({"error": "Google OAuth not configured"}), 500
    
    try:
        # Verify state parameter (only if we have a state in session)
        request_state = request.args.get('state')
        session_state = session.get('state')
        
        if session_state and request_state != session_state:
            return jsonify({
                "error": "Invalid state parameter", 
                "debug": f"Expected: {session_state}, Got: {request_state}"
            }), 400
        elif not request_state:
            return jsonify({"error": "Missing state parameter - please start login from beginning"}), 400
        
        # Get authorization code from Google
        authorization_code = request.args.get('code')
        if not authorization_code:
            return jsonify({"error": "Missing authorization code"}), 400
        
        # Exchange authorization code for access token manually
        google_provider_cfg = get_google_provider_cfg()
        token_url = google_provider_cfg["token_endpoint"]
        
        token_data = {
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'code': authorization_code,
            'grant_type': 'authorization_code',
            'redirect_uri': 'http://localhost:8888/auth/google/callback'
        }
        
        token_response = requests.post(token_url, data=token_data)
        if token_response.status_code != 200:
            return jsonify({"error": f"Failed to exchange code for token: {token_response.text}"}), 400
        
        token_json = token_response.json()
        access_token = token_json.get('access_token')
        
        if not access_token:
            return jsonify({"error": "No access token received"}), 400
        
        # Get user info from Google using the access token
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        headers = {'Authorization': f'Bearer {access_token}'}
        userinfo_response = requests.get(userinfo_endpoint, headers=headers)
        
        if userinfo_response.status_code != 200:
            return jsonify({"error": "Failed to get user info from Google"}), 400
            
        userinfo = userinfo_response.json()
        
        # Check if email is verified (some Google accounts may not have this field)
        email_verified = userinfo.get("email_verified", True)  # Default to True if not present
        if email_verified is False:  # Only reject if explicitly False
            return jsonify({"error": "User email not verified by Google"}), 400
        
        # Check if user exists
        email = userinfo.get("email", "").lower()
        google_id = userinfo.get("sub") or userinfo.get("id", "")  # Handle both 'sub' and 'id' fields
        name = userinfo.get("name", "")
        picture = userinfo.get("picture", "")
        
        if not email:
            return jsonify({"error": "No email received from Google"}), 400
        if not google_id:
            return jsonify({"error": "No user ID received from Google"}), 400
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Update existing user with Google info if not already set
            if not user.google_id:
                user.google_id = google_id
                user.name = name
                user.picture = picture
                db.session.commit()
        else:
            # Create new user
            # Create a default family based on user's name or email
            family_name = f"{name}'s Family" if name else f"{email.split('@')[0]}'s Family"
            fam = Family.query.filter_by(name=family_name).first()
            if not fam:
                fam = create_default_family(family_name)
            
            user = User(
                email=email,
                google_id=google_id,
                name=name,
                picture=picture,
                family_id=fam.id
            )
            db.session.add(user)
            db.session.commit()
        
        # Create JWT token
        access = create_access_token(identity=email, additional_claims=token_claims(user))
        
        # Return success page with token
        success_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login Successful</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0;
                }}
                .container {{
                    background: white;
                    padding: 40px;
                    border-radius: 20px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                    text-align: center;
                    max-width: 400px;
                }}
                .success-icon {{
                    font-size: 4rem;
                    margin-bottom: 20px;
                }}
                .title {{
                    font-size: 1.5rem;
                    font-weight: bold;
                    color: #333;
                    margin-bottom: 10px;
                }}
                .message {{
                    color: #666;
                    margin-bottom: 30px;
                }}
                .token-info {{
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    font-size: 0.9rem;
                    color: #666;
                }}
                .continue-btn {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 12px 30px;
                    border: none;
                    border-radius: 25px;
                    font-size: 1rem;
                    font-weight: 600;
                    cursor: pointer;
                    text-decoration: none;
                    display: inline-block;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success-icon">✅</div>
                <div class="title">Login Successful!</div>
                <div class="message">Welcome, {name or email}!</div>
                <div class="token-info">
                    Your access token has been saved to localStorage.
                </div>
                <a href="/budget" class="continue-btn">Continue to Budget App</a>
            </div>
            <script>
                localStorage.setItem('access_token', '{access}');
                localStorage.setItem('user_id', '{user.id}');
                localStorage.setItem('family_id', '{user.family_id}');
            </script>
        </body>
        </html>
        """
        
        return success_html
        
    except Exception as e:
        return jsonify({"error": f"OAuth callback failed: {str(e)}"}), 500

@app.route("/auth/logout")
def logout():
    session.clear()
    logout_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Logged Out</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0;
            }
            .container {
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                text-align: center;
                max-width: 400px;
            }
            .logout-icon {
                font-size: 4rem;
                margin-bottom: 20px;
            }
            .title {
                font-size: 1.5rem;
                font-weight: bold;
                color: #333;
                margin-bottom: 10px;
            }
            .message {
                color: #666;
                margin-bottom: 30px;
            }
            .login-btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 12px 30px;
                border: none;
                border-radius: 25px;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logout-icon">👋</div>
            <div class="title">Logged Out</div>
            <div class="message">You have been successfully logged out.</div>
            <a href="/login" class="login-btn">Login Again</a>
        </div>
        <script>
            localStorage.removeItem('access_token');
            localStorage.removeItem('user_id');
            localStorage.removeItem('family_id');
        </script>
    </body>
    </html>
    """
    return logout_html

# -------- User Info (protected) --------
@app.route("/api/user-info", methods=["GET"])
@jwt_required()
def get_user_info():
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first()
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
        "google_id": user.google_id
    }), 200

# -------- Categories (protected) --------
@app.route("/api/categories", methods=["GET"])
@jwt_required()
def list_categories():
    fam_id = get_jwt()["family_id"]
    cats = Category.query.filter_by(family_id=fam_id).order_by(Category.name).all()
    return jsonify([
        {"id": c.id, "name": c.name, "monthly_budget": float(c.monthly_budget or 0)}
        for c in cats
    ])

@app.route("/api/categories", methods=["POST"])
@jwt_required()
def create_category():
    fam_id = get_jwt()["family_id"]
    data = request.get_json(force=True)
    name = (data.get("name") or "").strip()
    monthly = data.get("monthly_budget", 0)

    if not name:
        return jsonify({"error": "name is required"}), 400

    cat = Category(family_id=fam_id, name=name, monthly_budget=monthly)
    db.session.add(cat)
    db.session.commit()
    return jsonify({"id": cat.id, "name": cat.name, "monthly_budget": float(cat.monthly_budget or 0)}), 201

# -------- Budget API --------
@app.route("/api/budget/summary", methods=["GET"])
@jwt_required()
def budget_summary():
    fam_id = get_jwt()["family_id"]
    
    # Get all transactions for this family
    from sqlalchemy import func
    
    # Calculate totals by type
    income = db.session.query(func.sum(Transaction.amount)).filter_by(
        family_id=fam_id, transaction_type='income'
    ).scalar() or 0
    
    expenses = db.session.query(func.sum(Transaction.amount)).filter_by(
        family_id=fam_id, transaction_type='expense'
    ).scalar() or 0
    
    bills = db.session.query(func.sum(Transaction.amount)).filter_by(
        family_id=fam_id, transaction_type='bill'
    ).scalar() or 0
    
    balance = float(income) - float(expenses) - float(bills)
    
    # Get category breakdown for this month
    from datetime import datetime, date
    current_month = date.today().replace(day=1)
    
    category_totals = db.session.query(
        Category.name,
        func.sum(Transaction.amount).label('total')
    ).join(Transaction).filter(
        Transaction.family_id == fam_id,
        Transaction.occurred_at >= current_month
    ).group_by(Category.name).order_by(func.sum(Transaction.amount).desc()).all()
    
    categories = []
    for cat_name, total in category_totals:
        categories.append({
            "name": cat_name,
            "amount": float(total)
        })
    
    return jsonify({
        "balance": balance,
        "income": float(income),
        "expenses": float(expenses),
        "bills": float(bills),
        "categories": categories
    })

@app.route("/api/budget/transaction", methods=["POST"])
@jwt_required()
def add_transaction():
    fam_id = get_jwt()["family_id"]
    data = request.get_json(force=True)
    
    transaction_type = data.get("type")
    amount = data.get("amount")
    description = data.get("description", "")
    transaction_date = data.get("date")
    category_id = data.get("categoryId")
    
    if not transaction_type or not amount or not category_id:
        return jsonify({"error": "Type, amount, and category are required"}), 400
    
    if transaction_type not in ['income', 'expense', 'bill']:
        return jsonify({"error": "Invalid transaction type"}), 400
    
    # Parse the date
    occurred_at = datetime.utcnow()  # Default to now
    if transaction_date:
        try:
            occurred_at = datetime.strptime(transaction_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    
    # Get or create the selected category
    if category_id.isdigit():
        # If it's a number, treat as category ID
        category = Category.query.filter_by(id=int(category_id), family_id=fam_id).first()
    else:
        # If it's a string, treat as category name
        category = Category.query.filter_by(name=category_id, family_id=fam_id).first()
    
    # If category doesn't exist, create it
    if not category:
        category = Category(family_id=fam_id, name=str(category_id), monthly_budget=0)
        db.session.add(category)
        db.session.flush()
    
    # Create transaction
    transaction = Transaction(
        family_id=fam_id,
        category_id=category.id,
        amount=amount,
        transaction_type=transaction_type,
        note=description,
        occurred_at=occurred_at
    )
    
    db.session.add(transaction)
    db.session.commit()
    
    return jsonify({
        "id": transaction.id,
        "type": transaction_type,
        "amount": float(amount),
        "description": description
    }), 201

@app.route("/api/categories", methods=["GET"])
@jwt_required()
def get_categories():
    fam_id = get_jwt()["family_id"]
    
    # Get all categories for this family
    categories = Category.query.filter_by(family_id=fam_id).order_by(Category.name).all()
    
    return jsonify([
        {
            "id": cat.id,
            "name": cat.name,
            "budget": float(cat.monthly_budget)
        }
        for cat in categories
    ])

@app.route("/api/budget/transactions", methods=["GET"])
@jwt_required()
def get_transactions():
    fam_id = get_jwt()["family_id"]
    
    # Get all transactions for this family
    transactions = Transaction.query.filter_by(family_id=fam_id).order_by(Transaction.occurred_at.desc()).all()
    
    return jsonify([
        {
            "id": t.id,
            "date": t.occurred_at.isoformat(),
            "description": t.note or "No description",
            "amount": float(t.amount),
            "type": t.transaction_type,
            "category": t.category.name if t.category else "Unknown"
        }
        for t in transactions
    ])

@app.route("/api/budget/transaction/<int:transaction_id>", methods=["DELETE"])
@jwt_required()
def delete_transaction(transaction_id):
    fam_id = get_jwt()["family_id"]
    
    # Find the transaction and make sure it belongs to the user's family
    transaction = Transaction.query.filter_by(id=transaction_id, family_id=fam_id).first()
    
    if not transaction:
        return jsonify({"error": "Transaction not found or access denied"}), 404
    
    try:
        db.session.delete(transaction)
        db.session.commit()
        return jsonify({"message": "Transaction deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete transaction"}), 500

# ------------------ Bootstrap ------------------
def init_db():
    """Initialize database with retry logic"""
    import time
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            with app.app_context():
                db.create_all()
            print("✅ Database initialized successfully!")
            return
        except Exception as e:
            retry_count += 1
            print(f"⚠️  Database connection attempt {retry_count}/{max_retries} failed: {e}")
            if retry_count >= max_retries:
                print("❌ Failed to connect to database after maximum retries")
                raise
            time.sleep(2)

# Initialize database when module is imported
def migrate_db():
    """Add missing columns to existing tables"""
    try:
        with app.app_context():
            # Check if transaction_type column exists
            result = db.session.execute(db.text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='transactions' AND column_name='transaction_type'
            """)).fetchone()
            
            if not result:
                print("Adding transaction_type column...")
                db.session.execute(db.text("""
                    ALTER TABLE transactions 
                    ADD COLUMN transaction_type VARCHAR(50) DEFAULT 'expense'
                """))
                db.session.commit()
                print("✅ Added transaction_type column")
            else:
                print("✅ transaction_type column already exists")
                
    except Exception as e:
        print(f"Migration error: {e}")
        # If migration fails, recreate all tables
        print("Recreating all tables...")
        db.drop_all()
        db.create_all()
        print("✅ Tables recreated")

init_db()
migrate_db()

def create_default_categories():
    """Create default categories for all families"""
    try:
        with app.app_context():
            # Get all families
            families = Family.query.all()
            
            for family in families:
                # Check if family already has categories
                existing_categories = Category.query.filter_by(family_id=family.id).count()
                
                if existing_categories == 0:
                    default_categories = [
                        {"name": "Salary", "budget": 0},
                        {"name": "Groceries", "budget": 500},
                        {"name": "Transportation", "budget": 200},
                        {"name": "Utilities", "budget": 300},
                        {"name": "Entertainment", "budget": 150},
                        {"name": "Healthcare", "budget": 200},
                        {"name": "Shopping", "budget": 300},
                        {"name": "Rent/Mortgage", "budget": 1200},
                        {"name": "Other", "budget": 0}
                    ]
                    
                    for cat_data in default_categories:
                        category = Category(
                            family_id=family.id,
                            name=cat_data["name"],
                            monthly_budget=cat_data["budget"]
                        )
                        db.session.add(category)
                    
                    db.session.commit()
                    print(f"✅ Created default categories for family: {family.name}")
                else:
                    print(f"⏭️ Family {family.name} already has {existing_categories} categories")
                
    except Exception as e:
        print(f"Error creating default categories: {e}")

create_default_categories()

if __name__ == "__main__":
    # For dev only; in container Gunicorn runs this module
    app.run(host="0.0.0.0", port=5000)
