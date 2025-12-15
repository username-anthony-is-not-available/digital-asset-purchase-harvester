#!/usr/bin/env python3
"""
Virtual Environment Status Checker
This script helps users verify their virtual environment is properly activated
"""

import sys
from pathlib import Path

def check_venv_status():
    """Check if virtual environment is activated and provide guidance."""
    
    print("🔍 Virtual Environment Status Check")
    print("=" * 50)
    
    # Check if we're in a virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    
    if in_venv:
        print("✅ Virtual environment is ACTIVE")
        print(f"   Python executable: {sys.executable}")
        
        # Check if we're in the project directory
        current_dir = Path.cwd()
        expected_files = [
            'main.py',
            'digital_asset_harvester/__init__.py',
            'requirements.txt',
        ]
        
        if all((current_dir / file).exists() for file in expected_files):
            print("✅ You're in the correct project directory")
            
            # Check if required packages are installed
            try:
                import ollama  # noqa: F401
                print("✅ Required packages are installed")
                print("\n🚀 Ready to run the application!")
                print("\nNext steps:")
                print("  • Run tests: python test_improvements.py")
                print("  • Process mbox: python main.py your_file.mbox --output output.csv")
                
            except ImportError as e:
                print(f"❌ Missing required package: {e}")
                print("   Run: pip install -r requirements.txt")
                
        else:
            print("⚠️  You might not be in the project directory")
            print("   Make sure you're in the digital-asset-purchase-harvester folder")
            
    else:
        print("❌ Virtual environment is NOT active")
        print("\nTo activate the virtual environment:")
        print("\nWindows PowerShell:")
        print("  .\\venv\\Scripts\\Activate.ps1")
        print("\nWindows Command Prompt:")
        print("  venv\\Scripts\\activate.bat")
        print("\nLinux/macOS:")
        print("  source venv/bin/activate")
        print("\nIf you haven't created the virtual environment yet:")
        print("  python -m venv venv")


if __name__ == "__main__":
    check_venv_status()
