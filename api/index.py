import sys
import os

# Add backend directory to sys.path so 'app' imports resolve cleanly on Vercel
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
backend_dir = os.path.join(root_dir, "backend")

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app

# Expose app for Vercel's ASGI serverless handler
handler = app
