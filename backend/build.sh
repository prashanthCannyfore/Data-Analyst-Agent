#!/bin/bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. REMOVE the Matplotlib cache line. If it runs at runtime, we cannot stop it here.
# python -c "import matplotlib.pyplot as plt; plt.figure(); plt.savefig('/tmp/dummy.png')"

# 3. Create and set the CORRECT START COMMAND with DEBUGGING
# The debug level will show any internal Uvicorn or Starlette/FastAPI errors.
echo 'uvicorn main:app --host 0.0.0.0 --port $PORT --log-level debug' > start.sh
chmod +x start.sh