#!/bin/bash

# Add src to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)/src

# Run the app
python app.py 