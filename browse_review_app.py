#!/usr/bin/env python3
"""
Browse & Review App - Tree view of all domains and tasks.
Browse everything at once, rate at task level.
"""

import json
from pathlib import Path
from flask import Flask, render_template_string, jsonify, request
from collections import defaultdict

app = Flask(__name__)

# Paths
MANIFEST_PATH = Path("/workspaces/Taskpedia/taskpedia-web/public/data/manifest.json")
VALUE_RATINGS_PATH = Path("/workspaces/Taskpedia/value_ratings.jsonl")

# Load manifest
with open(MANIFEST_PATH) as f:
    MANIFEST = json.load(f)

# Load existing ratings
RATINGS = {}
if VALUE_RATINGS_PATH.exists():
    with open(VALUE_RATINGS_PATH) as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                RATINGS[data['task_id']] = data['tier']

# Organize by domain -> tasks
TREE = defaultdict(list)
for task_id, task in MANIFEST.items():
    if task.get('node_type') == 'task':
        domain = task_id.split('/')[0]
        TREE[domain].append({
            'id': task_id,
            'name': task.get('name', ''),
            'children_count': len(task.get('children_ids', [])),
            'rating': RATINGS.get(task_id, None)
        })

# Sort domains and tasks
for domain in TREE:
    TREE[domain].sort(key=lambda x: x['name'])

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Browse & Review - All Tasks</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }

        .header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            position: sticky;
            top: 20px;
            z-index: 1000;
        }
        .header h1 {
            font-size: 2em;
            color: #333;
            margin-bottom: 10px;
        }
        .header .subtitle {
            color: #666;
            margin-bottom: 20px;
        }

        .stats {
            display: flex;
            gap: 20px;
            margin-top: 15px;
        }
        .stat {
            padding: 10px 20px;
            border-radius: 10px;
            font-weight: 600;
        }
        .stat.premium { background: #fce4ec; color: #e91e63; }
        .stat.high { background: #e3f2fd; color: #2196f3; }
        .stat.medium { background: #fff3e0; color: #ff9800; }
        .stat.low { background: #f5f5f5; color: #9e9e9e; }
        .stat.trash { background: #ffebee; color: #f44336; }

        .controls {
            margin-top: 15px;
            display: flex;
            gap: 10px;
        }
        .controls input {
            flex: 1;
            padding: 10px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 1em;
        }
        .controls button {
            padding: 10px 20px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
        }
        .controls select {
            padding: 10px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 1em;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        .domain-section {
            background: white;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }

        .domain-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 30px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            user-select: none;
        }
        .domain-header:hover {
            background: linear-gradient(135deg, #5568d3 0%, #653a8b 100%);
        }
        .domain-header h2 {
            font-size: 1.5em;
        }
        .domain-header .count {
            background: rgba(255,255,255,0.3);
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
        }
        .domain-header .arrow {
            font-size: 1.5em;
            transition: transform 0.3s;
        }
        .domain-section.collapsed .arrow {
            transform: rotate(-90deg);
        }

        .task-list {
            display: none;
        }
        .domain-section.expanded .task-list {
            display: block;
        }

        .task-row {
            padding: 15px 30px;
            border-bottom: 1px solid #f0f0f0;
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 20px;
            align-items: center;
            transition: background 0.2s;
        }
        .task-row:hover {
            background: #f9f9f9;
        }
        .task-row:last-child {
            border-bottom: none;
        }
        .task-row.rated {
            background: #f5f5f5;
        }

        .task-info {
            flex: 1;
        }
        .task-name {
            font-size: 1.1em;
            font-weight: 500;
            color: #333;
            margin-bottom: 5px;
        }
        .task-meta {
            font-size: 0.85em;
            color: #999;
        }

        .rating-buttons {
            display: flex;
            gap: 8px;
        }
        .rate-btn {
            width: 45px;
            height: 45px;
            border: 2px solid transparent;
            border-radius: 8px;
            font-size: 1.2em;
            cursor: pointer;
            transition: all 0.2s;
            background: #f5f5f5;
        }
        .rate-btn:hover {
            transform: scale(1.1);
            box-shadow: 0 3px 10px rgba(0,0,0,0.2);
        }
        .rate-btn.selected {
            border-color: #333;
            box-shadow: 0 0 0 3px rgba(0,0,0,0.1);
        }
        .rate-btn.premium:hover, .rate-btn.premium.selected { background: #e91e63; color: white; }
        .rate-btn.high:hover, .rate-btn.high.selected { background: #2196f3; color: white; }
        .rate-btn.medium:hover, .rate-btn.medium.selected { background: #ff9800; color: white; }
        .rate-btn.low:hover, .rate-btn.low.selected { background: #9e9e9e; color: white; }
        .rate-btn.trash:hover, .rate-btn.trash.selected { background: #f44336; color: white; }

        .expand-all {
            margin-bottom: 20px;
            text-align: center;
        }
        .expand-all button {
            padding: 12px 30px;
            background: white;
            border: 2px solid #667eea;
            color: #667eea;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            font-size: 1em;
            margin: 0 5px;
        }
        .expand-all button:hover {
            background: #667eea;
            color: white;
        }

        .no-results {
            padding: 40px;
            text-align: center;
            color: #999;
            font-size: 1.2em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 Browse All Tasks</h1>
            <div class="subtitle">Explore domains → Review tasks → Rate them</div>

            <div class="stats">
                <div class="stat premium">⭐ <span id="premium-count">0</span> Premium</div>
                <div class="stat high">🔥 <span id="high-count">0</span> High</div>
                <div class="stat medium">👍 <span id="medium-count">0</span> Medium</div>
                <div class="stat low">👎 <span id="low-count">0</span> Low</div>
                <div class="stat trash">🗑️ <span id="trash-count">0</span> Trash</div>
            </div>

            <div class="controls">
                <input type="text" id="search" placeholder="Search tasks..." onkeyup="filterTasks()">
                <select id="filter-rating" onchange="filterTasks()">
                    <option value="all">All Tasks</option>
                    <option value="unrated">Unrated Only</option>
                    <option value="rated">Rated Only</option>
                    <option value="premium">Premium</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                    <option value="trash">Trash</option>
                </select>
                <button onclick="exportRatings()">Export</button>
            </div>
        </div>

        <div class="expand-all">
            <button onclick="expandAll()">Expand All Domains</button>
            <button onclick="collapseAll()">Collapse All</button>
        </div>

        <div id="content"></div>
    </div>

    <script>
        let tree = {};
        let ratings = {};
        let stats = {PREMIUM: 0, HIGH: 0, MEDIUM: 0, LOW: 0, TRASH: 0};

        async function init() {
            const response = await fetch('/api/tree');
            const data = await response.json();
            tree = data.tree;
            ratings = data.ratings;

            // Count existing ratings
            for (let tier of Object.values(ratings)) {
                stats[tier]++;
            }
            updateStats();

            renderTree();
        }

        function renderTree() {
            const content = document.getElementById('content');
            content.innerHTML = '';

            const domains = Object.keys(tree).sort();

            let visibleDomains = 0;
            domains.forEach(domain => {
                const section = createDomainSection(domain, tree[domain]);
                if (section) {
                    content.appendChild(section);
                    visibleDomains++;
                }
            });

            if (visibleDomains === 0) {
                content.innerHTML = '<div class="no-results">No tasks match your filters</div>';
            }
        }

        function createDomainSection(domain, tasks) {
            const searchTerm = document.getElementById('search').value.toLowerCase();
            const filterRating = document.getElementById('filter-rating').value;

            // Filter tasks
            const filteredTasks = tasks.filter(task => {
                // Search filter
                if (searchTerm && !task.name.toLowerCase().includes(searchTerm)) {
                    return false;
                }

                // Rating filter
                const taskRating = ratings[task.id];
                if (filterRating === 'unrated' && taskRating) return false;
                if (filterRating === 'rated' && !taskRating) return false;
                if (filterRating !== 'all' && filterRating !== 'unrated' && filterRating !== 'rated') {
                    if (taskRating?.toLowerCase() !== filterRating) return false;
                }

                return true;
            });

            if (filteredTasks.length === 0) return null;

            const section = document.createElement('div');
            section.className = 'domain-section collapsed';
            section.innerHTML = `
                <div class="domain-header" onclick="toggleDomain(this)">
                    <div>
                        <h2>${domain.replace(/_/g, ' ').toUpperCase()}</h2>
                    </div>
                    <div style="display: flex; gap: 20px; align-items: center;">
                        <div class="count">${filteredTasks.length} tasks</div>
                        <div class="arrow">▼</div>
                    </div>
                </div>
                <div class="task-list" id="tasks-${domain}"></div>
            `;

            const taskList = section.querySelector('.task-list');
            filteredTasks.forEach(task => {
                taskList.appendChild(createTaskRow(task));
            });

            return section;
        }

        function createTaskRow(task) {
            const row = document.createElement('div');
            row.className = 'task-row';
            row.dataset.id = task.id;

            if (ratings[task.id]) {
                row.classList.add('rated');
            }

            const currentRating = ratings[task.id];

            row.innerHTML = `
                <div class="task-info">
                    <div class="task-name">${task.name}</div>
                    <div class="task-meta">${task.children_count} subtasks</div>
                </div>
                <div class="rating-buttons">
                    <button class="rate-btn premium ${currentRating === 'PREMIUM' ? 'selected' : ''}"
                            onclick="rate('${task.id}', 'PREMIUM')" title="Premium">⭐</button>
                    <button class="rate-btn high ${currentRating === 'HIGH' ? 'selected' : ''}"
                            onclick="rate('${task.id}', 'HIGH')" title="High">🔥</button>
                    <button class="rate-btn medium ${currentRating === 'MEDIUM' ? 'selected' : ''}"
                            onclick="rate('${task.id}', 'MEDIUM')" title="Medium">👍</button>
                    <button class="rate-btn low ${currentRating === 'LOW' ? 'selected' : ''}"
                            onclick="rate('${task.id}', 'LOW')" title="Low">👎</button>
                    <button class="rate-btn trash ${currentRating === 'TRASH' ? 'selected' : ''}"
                            onclick="rate('${task.id}', 'TRASH')" title="Trash">🗑️</button>
                </div>
            `;

            return row;
        }

        function toggleDomain(header) {
            const section = header.parentElement;
            section.classList.toggle('collapsed');
            section.classList.toggle('expanded');
        }

        function expandAll() {
            document.querySelectorAll('.domain-section').forEach(section => {
                section.classList.remove('collapsed');
                section.classList.add('expanded');
            });
        }

        function collapseAll() {
            document.querySelectorAll('.domain-section').forEach(section => {
                section.classList.remove('expanded');
                section.classList.add('collapsed');
            });
        }

        async function rate(taskId, tier) {
            const oldRating = ratings[taskId];

            // Update stats
            if (oldRating) {
                stats[oldRating]--;
            }
            stats[tier]++;

            ratings[taskId] = tier;
            updateStats();

            // Update UI
            const row = document.querySelector(`[data-id="${taskId}"]`);
            row.classList.add('rated');

            // Update button states
            row.querySelectorAll('.rate-btn').forEach(btn => btn.classList.remove('selected'));
            row.querySelector(`.rate-btn.${tier.toLowerCase()}`).classList.add('selected');

            // Save to server
            await fetch('/api/rate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({task_id: taskId, tier: tier})
            });
        }

        function updateStats() {
            document.getElementById('premium-count').textContent = stats.PREMIUM;
            document.getElementById('high-count').textContent = stats.HIGH;
            document.getElementById('medium-count').textContent = stats.MEDIUM;
            document.getElementById('low-count').textContent = stats.LOW;
            document.getElementById('trash-count').textContent = stats.TRASH;
        }

        function filterTasks() {
            renderTree();
        }

        async function exportRatings() {
            const response = await fetch('/api/export');
            const data = await response.json();

            const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'task_ratings.json';
            a.click();
        }

        init();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/tree')
def get_tree():
    """Get organized tree structure."""
    return jsonify({
        'tree': dict(TREE),
        'ratings': RATINGS
    })

@app.route('/api/rate', methods=['POST'])
def rate_task():
    """Rate a task."""
    data = request.json
    task_id = data['task_id']
    tier = data['tier']

    task = MANIFEST.get(task_id, {})

    record = {
        'task_id': task_id,
        'name': task.get('name', ''),
        'tier': tier,
        'domain': task_id.split('/')[0],
        'children_count': len(task.get('children_ids', [])),
    }

    with open(VALUE_RATINGS_PATH, 'a') as f:
        f.write(json.dumps(record) + '\n')

    RATINGS[task_id] = tier

    return jsonify({'success': True})

@app.route('/api/export')
def export_ratings():
    """Export all ratings."""
    rated_tasks = []
    for task_id, tier in RATINGS.items():
        if task_id in MANIFEST:
            task = MANIFEST[task_id]
            rated_tasks.append({
                'task_id': task_id,
                'name': task.get('name', ''),
                'tier': tier,
                'domain': task_id.split('/')[0],
                'children_count': len(task.get('children_ids', [])),
            })

    return jsonify({
        'total': len(rated_tasks),
        'by_tier': {
            'PREMIUM': len([t for t in rated_tasks if t['tier'] == 'PREMIUM']),
            'HIGH': len([t for t in rated_tasks if t['tier'] == 'HIGH']),
            'MEDIUM': len([t for t in rated_tasks if t['tier'] == 'MEDIUM']),
            'LOW': len([t for t in rated_tasks if t['tier'] == 'LOW']),
            'TRASH': len([t for t in rated_tasks if t['tier'] == 'TRASH']),
        },
        'tasks': rated_tasks
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5006, debug=True)
