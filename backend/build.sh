#!/bin/bash
pip install -r requirements.txt
python -c "import matplotlib.pyplot as plt; plt.figure(); plt.savefig('/tmp/dummy.png')"

# 3. Save the correct start command to a separate script
echo 'uvicorn main:app --host 0.0.0.0 --port $PORT' > start.sh
chmod +x start.sh