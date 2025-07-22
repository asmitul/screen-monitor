#!/usr/bin/env python3
"""
Test script to validate the screen monitor setup
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test if all required packages can be imported"""
    print("Testing imports...")
    
    try:
        import cv2
        print("✓ OpenCV imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import OpenCV: {e}")
        return False
    
    try:
        import numpy as np
        print("✓ NumPy imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import NumPy: {e}")
        return False
    
    try:
        from PIL import ImageGrab
        print("✓ Pillow imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import Pillow: {e}")
        return False
    
    try:
        from telegram import Update
        from telegram.ext import ApplicationBuilder
        print("✓ python-telegram-bot imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import python-telegram-bot: {e}")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✓ python-dotenv imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import python-dotenv: {e}")
        return False
    
    return True

def test_screenshot():
    """Test if screenshot functionality works"""
    print("\nTesting screenshot functionality...")
    
    try:
        from PIL import ImageGrab
        # Take a small test screenshot
        screenshot = ImageGrab.grab(bbox=(0, 0, 100, 100))
        screenshot.save("test_screenshot.png")
        print("✓ Screenshot test successful")
        
        # Clean up
        if os.path.exists("test_screenshot.png"):
            os.remove("test_screenshot.png")
            
        return True
    except Exception as e:
        print(f"✗ Screenshot test failed: {e}")
        return False

def test_environment():
    """Test environment configuration"""
    print("\nTesting environment configuration...")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ['TOKEN', 'DEVELOPER_CHAT_ID']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"✗ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please create a .env file with the required variables")
        return False
    else:
        print("✓ All required environment variables found")
        return True

def test_opencv_functionality():
    """Test OpenCV image processing functionality"""
    print("\nTesting OpenCV functionality...")
    
    try:
        import cv2
        import numpy as np
        
        # Create a test image
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        test_image[25:75, 25:75] = [255, 255, 255]  # White rectangle
        
        # Test basic operations
        gray = cv2.cvtColor(test_image, cv2.COLOR_BGR2GRAY)
        _, threshold = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        
        print("✓ OpenCV image processing test successful")
        return True
    except Exception as e:
        print(f"✗ OpenCV functionality test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Screen Monitor Setup Test")
    print("=" * 30)
    
    tests = [
        test_imports,
        test_screenshot,
        test_environment,
        test_opencv_functionality
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 30)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed! Your setup is ready.")
        print("\nNext steps:")
        print("1. Configure your .env file with your bot token and chat ID")
        print("2. Run: python main.py")
        print("3. Send /start to your bot to begin monitoring")
    else:
        print("✗ Some tests failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 