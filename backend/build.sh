#!/bin/bash
pip install -r requirements.txt
python -c "import matplotlib.pyplot as plt; plt.figure(); plt.savefig('/tmp/dummy.png')"