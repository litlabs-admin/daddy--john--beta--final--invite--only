#!/usr/bin/env python3
"""
User Management Script for Daddy John Chatbot
Adds new invited users to the database with hashed passwords
"""

import os
import bcrypt
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Initialize Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

supabase: Client = create_client(url, key)

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def add_user(email: str, password: str, is_active: bool = True):
    """Add a new invited user to the database."""
    try:
        # Check if user already exists
        existing_user = supabase.table('invited_users').select('email').eq('email', email.lower()).execute()
        
        if existing_user.data:
            print(f"❌ User {email} already exists!")
            return False
        
        # Hash the password
        password_hash = hash_password(password)
        
        # Insert new user
        result = supabase.table('invited_users').insert({
            'email': email.lower(),
            'password_hash': password_hash,
            'is_active': is_active
        }).execute()
        
        if result.data:
            print(f"✅ User {email} added successfully!")
            return True
        else:
            print(f"❌ Failed to add user {email}")
            return False
            
    except Exception as e:
        print(f"❌ Error adding user {email}: {str(e)}")
        return False

def list_users():
    """List all invited users."""
    try:
        result = supabase.table('invited_users').select('email, is_active, created_at').execute()
        
        if result.data:
            print("\n📋 Invited Users:")
            print("-" * 50)
            for user in result.data:
                status = "✅ Active" if user['is_active'] else "❌ Inactive"
                print(f"Email: {user['email']}")
                print(f"Status: {status}")
                print(f"Created: {user['created_at']}")
                print("-" * 50)
        else:
            print("No users found.")
            
    except Exception as e:
        print(f"❌ Error listing users: {str(e)}")

def deactivate_user(email: str):
    """Deactivate a user."""
    try:
        result = supabase.table('invited_users').update({'is_active': False}).eq('email', email.lower()).execute()
        
        if result.data:
            print(f"✅ User {email} deactivated successfully!")
            return True
        else:
            print(f"❌ User {email} not found!")
            return False
            
    except Exception as e:
        print(f"❌ Error deactivating user {email}: {str(e)}")
        return False

def activate_user(email: str):
    """Activate a user."""
    try:
        result = supabase.table('invited_users').update({'is_active': True}).eq('email', email.lower()).execute()
        
        if result.data:
            print(f"✅ User {email} activated successfully!")
            return True
        else:
            print(f"❌ User {email} not found!")
            return False
            
    except Exception as e:
        print(f"❌ Error activating user {email}: {str(e)}")
        return False

def main():
    """Main interactive menu."""
    print("🤖 Daddy John Chatbot - User Management")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Add new user")
        print("2. List all users")
        print("3. Deactivate user")
        print("4. Activate user")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            email = input("Enter email: ").strip()
            password = input("Enter password: ").strip()
            
            if email and password:
                add_user(email, password)
            else:
                print("❌ Email and password are required!")
                
        elif choice == '2':
            list_users()
            
        elif choice == '3':
            email = input("Enter email to deactivate: ").strip()
            if email:
                deactivate_user(email)
            else:
                print("❌ Email is required!")
                
        elif choice == '4':
            email = input("Enter email to activate: ").strip()
            if email:
                activate_user(email)
            else:
                print("❌ Email is required!")
                
        elif choice == '5':
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice! Please enter 1-5.")

if __name__ == "__main__":
    main()
