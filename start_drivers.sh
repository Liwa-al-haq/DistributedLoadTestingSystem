#!/bin/bash

# Ensure all background jobs are killed when script exits
# trap 'kill $(jobs -p)' EXIT

# Start 8 driver nodes in the background
python3 driver.py driver1 3001 &
python3 driver.py driver2 3002 &
python3 driver.py driver3 3003 &
python3 driver.py driver4 3004 &
python3 driver.py driver5 3005 &
python3 driver.py driver6 3006 &
python3 driver.py driver7 3007 &
python3 driver.py driver8 3008 &

# Wait for all background jobs to finish
wait
