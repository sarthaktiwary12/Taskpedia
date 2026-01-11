#!/usr/bin/env python3
"""Count YAML files with llm_generated as source in task_hierarchy."""

import yaml
from pathlib import Path
from collections import Counter
import sys

def count_by_source(task_dir: str = "./task_hierarchy"):
    """Count nodes by their source."""
    root = Path(task_dir)
    
    if not root.exists():
        print(f"Directory not found: {task_dir}")
        sys.exit(1)
    
    source_counts = Counter()
    total = 0
    llm_generated_files = []
    
    for yaml_path in root.glob("**/*.yaml"):
        try:
            with open(yaml_path) as f:
                data = yaml.safe_load(f)
            
            if data and "sources" in data:
                sources = data["sources"]
                for source in sources:
                    source_counts[source] += 1
                
                if "llm_generated" in sources:
                    llm_generated_files.append(yaml_path)
            
            total += 1
        except Exception as e:
            pass  # Skip files that can't be parsed
    
    print(f"Total YAML files: {total:,}")
    print(f"\nBy source:")
    for source, count in source_counts.most_common():
        pct = (count / total * 100) if total > 0 else 0
        print(f"  {source}: {count:,} ({pct:.1f}%)")
    
    print(f"\nLLM Generated: {len(llm_generated_files):,} files")
    
    return len(llm_generated_files)

if __name__ == "__main__":
    task_dir = sys.argv[1] if len(sys.argv) > 1 else "./task_hierarchy"
    count_by_source(task_dir)
