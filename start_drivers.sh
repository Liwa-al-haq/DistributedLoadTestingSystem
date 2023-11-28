#!/bin/bash

# Start 8 driver nodes in the background
python3 driver.py driver1 &
python3 driver.py driver2 &
python3 driver.py driver3 &
python3 driver.py driver4 &
python3 driver.py driver5 &
python3 driver.py driver6 &
python3 driver.py driver7 &
python3 driver.py driver8 &

# Wait for all background jobs to finish
wait
