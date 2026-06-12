"""
App package initialization
Sets up Python path for accessing scripts modules
"""
import sys
import os

# Add scripts directory to path so scripts modules can be imported
scripts_dir = os.path.join(os.path.dirname(__file__), '..', 'scripts')
scripts_dir = os.path.abspath(scripts_dir)

if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)
