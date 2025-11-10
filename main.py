"""
Main entry point for Android version of TaikoMini
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    try:
        # Import and run the main Taiko game
        from TaikoMini import main as taiko_main
        taiko_main()
    except Exception as e:
        import traceback
        print(f"Error running TaikoMini: {e}")
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == '__main__':
    main()