#!/bin/bash
# Test script to verify CPU saturation with PRAXIS generation

echo "=== PRAXIS CPU Saturation Test ==="
echo ""
echo "This will:"
echo "  - Use 9 CPU cores (leaving 1 for system)"
echo "  - Spawn 36 Ray workers (4 workers per CPU)"
echo "  - Generate 1000 tasks using mock provider"
echo ""
echo "Monitor in another terminal with: ./monitor_resources.sh"
echo "Or check Ray dashboard at: http://127.0.0.1:8265"
echo ""
read -p "Press Enter to start..."

# Run generation with verbose output
uv run python praxis/cli.py -v generate \
    --provider mock \
    --max-tasks 1000 \
    --output-dir output/

echo ""
echo "=== Test Complete ==="
echo "Check output/ directory for generated tasks"
