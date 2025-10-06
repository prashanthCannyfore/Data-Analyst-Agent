#!/bin/bash
# Install dependencies
pip install -r requirements.txt
# Force Matplotlib to build its cache now, not during server startup
python -c "import matplotlib.pyplot as plt; plt.figure(); plt.savefig('/tmp/dummy.png')"