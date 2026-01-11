#!/bin/bash
# Resource monitoring script for PRAXIS generation
# Shows CPU, memory usage, and Ray worker activity

echo "=== PRAXIS Resource Monitor ==="
echo "Press Ctrl+C to stop"
echo ""

while true; do
    clear
    echo "=== System Resources ($(date +%T)) ==="
    echo ""

    # Show top processes sorted by CPU
    echo "--- Top CPU Consumers ---"
    top -l 1 -n 10 -o cpu -stats pid,command,cpu,mem | head -15

    echo ""
    echo "--- Ray Workers ---"
    ps aux | grep -E "(ray::)|(raylet)|(ray start)" | grep -v grep | awk '{printf "%-10s %-8s %-8s %s\n", $2, $3"%", $4"%", $11}'

    echo ""
    echo "--- Overall CPU Usage ---"
    top -l 1 | grep "CPU usage"

    echo ""
    echo "--- Memory Usage ---"
    top -l 1 | grep PhysMem

    echo ""
    echo "--- Ray Status ---"
    # Count active Ray workers
    RAY_WORKERS=$(ps aux | grep -E "ray::" | grep -v grep | wc -l | xargs)
    echo "Active Ray workers: $RAY_WORKERS"

    # Check if Ray dashboard is accessible
    if curl -s http://127.0.0.1:8265 > /dev/null 2>&1; then
        echo "Ray dashboard: http://127.0.0.1:8265 (accessible)"
    else
        echo "Ray dashboard: Not available"
    fi

    sleep 2
done
