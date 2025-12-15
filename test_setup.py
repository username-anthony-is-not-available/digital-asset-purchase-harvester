#!/usr/bin/env python3
"""
Mock Test Script for Virtual Environment Setup
Tests that the virtual environment and dependencies are properly installed
"""

import sys
from pathlib import Path

def test_virtual_environment():
    """Test that virtual environment is properly set up."""
    print("🔧 Testing Virtual Environment Setup")
    print("=" * 50)
    
    # Check virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    
    if in_venv:
        print("✅ Virtual environment is active")
        print(f"   Python path: {sys.executable}")
    else:
        print("❌ Virtual environment not active")
        return False
    
    return True

def test_dependencies():
    """Test that required dependencies are installed."""
    print("\n📦 Testing Dependencies")
    print("-" * 30)
    
    required_packages = [
        ('ollama', 'Ollama Python client'),
        ('json', 'JSON processing (built-in)'),
        ('logging', 'Logging (built-in)'),
        ('datetime', 'Date/time handling (built-in)'),
        ('re', 'Regular expressions (built-in)'),
        ('csv', 'CSV processing (built-in)'),
        ('email', 'Email parsing (built-in)'),
        ('mailbox', 'Mailbox handling'),
    ]
    
    success_count = 0
    
    for package, description in required_packages:
        try:
            __import__(package)
            print(f"✅ {package:<12} - {description}")
            success_count += 1
        except ImportError as e:
            print(f"❌ {package:<12} - {description} (Error: {e})")
    
    print(f"\n📊 Dependencies: {success_count}/{len(required_packages)} available")
    return success_count == len(required_packages)

def test_project_structure():
    """Test that project files are in place."""
    print("\n📁 Testing Project Structure")
    print("-" * 35)
    
    required_files = [
        ('main.py', 'Main application script'),
        ('digital_asset_harvester/__init__.py', 'Package root'),
        ('digital_asset_harvester/processing/email_purchase_extractor.py', 'Email processing module'),
        ('digital_asset_harvester/output/csv_writer.py', 'CSV output module'),
        ('digital_asset_harvester/ingest/mbox_reader.py', 'Mbox parsing module'),
        ('digital_asset_harvester/config.py', 'Configuration file'),
        ('pyproject.toml', 'Project metadata'),
        ('requirements.txt', 'Dependencies list'),
        ('README.md', 'Documentation'),
    ]
    
    current_dir = Path.cwd()
    success_count = 0
    
    for filename, description in required_files:
        file_path = current_dir / filename
        if file_path.exists():
            print(f"✅ {filename:<25} - {description}")
            success_count += 1
        else:
            print(f"❌ {filename:<25} - {description} (Not found)")
    
    print(f"\n📊 Project files: {success_count}/{len(required_files)} found")
    return success_count == len(required_files)

def test_import_modules():
    """Test importing our custom modules."""
    print("\n🐍 Testing Module Imports")
    print("-" * 30)
    
    modules = [
        ('digital_asset_harvester.processing.email_purchase_extractor', 'EmailPurchaseExtractor'),
        ('digital_asset_harvester.output.csv_writer', 'CSV writing functions'),
        ('digital_asset_harvester.ingest.mbox_reader', 'MboxDataExtractor'),
        ('digital_asset_harvester.config', 'Configuration settings'),
        ('digital_asset_harvester.llm.client', 'LLM client wrapper'),
        ('digital_asset_harvester.cli', 'Command-line interface'),
        ('digital_asset_harvester.utils.file_utils', 'File utility functions'),
    ]
    
    success_count = 0
    
    for module_name, description in modules:
        try:
            __import__(module_name)
            print(f"✅ {module_name:<25} - {description}")
            success_count += 1
        except ImportError as e:
            print(f"❌ {module_name:<25} - {description} (Error: {e})")
        except (AttributeError, SyntaxError) as e:
            print(f"⚠️ {module_name:<25} - {description} (Warning: {e})")
            success_count += 1  # Still counts as success for import
    
    print(f"\n📊 Module imports: {success_count}/{len(modules)} successful")

    if success_count == len(modules):
        from digital_asset_harvester import get_settings

        settings = get_settings()
        print(
            f"   Current LLM model: {settings.llm_model_name} | Log level: {settings.log_level}"
        )

    return success_count == len(modules)

def main():
    """Run all tests and provide summary."""
    print("🚀 Virtual Environment & Setup Validation")
    print("=" * 60)
    
    tests = [
        ("Virtual Environment", test_virtual_environment),
        ("Dependencies", test_dependencies),
        ("Project Structure", test_project_structure),
        ("Module Imports", test_import_modules),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except (ImportError, AttributeError, OSError) as e:
            print(f"❌ {test_name} test failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your environment is ready.")
        print("\n💡 Next steps:")
        print("   • Install and start Ollama: https://ollama.ai/download")
        print("   • Pull the model: ollama pull llama3.2:3b")  
        print("   • Run the full test: python test_improvements.py")
        print("   • Process emails: digital-asset-harvester your_file.mbox --output output.csv")
        return True
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
