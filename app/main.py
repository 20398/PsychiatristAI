import os
import sys

# Ensure app directory is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from api import app

def main():
    print("Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()