"""
Setup script for Resume Data Extraction Web Application
"""

import os
import sys
from pathlib import Path

def setup_environment():
    """Set up the application environment by creating necessary directories"""
    print("\nSetting up application environment...")
    
    # Create directories if they don't exist
    print("Creating necessary directories...")
    for directory in ["uploads", "output", "output/resume"]:
        os.makedirs(directory, exist_ok=True)
    print("✓ Directories created successfully")
    
    return True

def main():
    """Main setup function"""
    print("=" * 80)
    print(" Resume Data Extraction Web Application Setup")
    print("=" * 80)
    
    if not setup_environment():
        print("\n✗ Environment setup failed. Please resolve the issues and try again.")
        return False
    
    print("\n✓ Directory setup completed successfully!")
    print("\nImportant:")
    print("1. Make sure all dependencies are installed according to README.md")
    print("2. Start the application: python app.py")
    print("3. Open in your browser: http://localhost:5000")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 