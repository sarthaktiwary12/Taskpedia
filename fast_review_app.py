#!/usr/bin/env python3
"""
Fast Review App - See many tasks at once, rate them all quickly.
No waiting between tasks!
"""

import json
import random
from pathlib import Path
from flask import Flask, render_template_string, jsonify, request

app = Flask(__name__)

# Paths
MANIFEST_PATH = Path("/workspaces/Taskpedia/taskpedia-web/public/data/manifest.json")
VALUE_RATINGS_PATH = Path("/workspaces/Taskpedia/value_ratings.jsonl")

# Load manifest
with open(MANIFEST_PATH) as f:
    MANIFEST = json.load(f)

# Get all high-level tasks (with many children = complete activities)
TASKS = []
for task_id, task in MANIFEST.items():
    node_type = task.get('node_type', '')
    children_count = len(task.get('children_ids', []))

    # Show tasks or subtasks with 5+ children (high-level activities)
    # Examples: "Housework", "Food Preparation", "Barista duties"
    if (node_type in ['task', 'subtask']) and children_count >= 5:
        TASKS.append({
            'id': task_id,
            'name': task.get('name', ''),
            'domain': task_id.split('/')[0],
            'children_count': children_count,
            'node_type': node_type,
        })

# Load existing ratings
RATED_IDS = set()
if VALUE_RATINGS_PATH.exists():
    with open(VALUE_RATINGS_PATH) as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                RATED_IDS.add(data['task_id'])

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>TaskPedia Fast Review</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }

        .header {
            background: white;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 20px;
            z-index: 1000;
        }

        .stats {
            display: flex;
            gap: 20px;
        }
        .stat {
            text-align: center;
        }
        .stat .number {
            font-size: 1.5em;
            font-weight: bold;
        }
        .stat .label {
            font-size: 0.8em;
            color: #666;
        }
        .stat.premium .number { color: #e91e63; }
        .stat.high .number { color: #2196f3; }
        .stat.medium .number { color: #ff9800; }
        .stat.low .number { color: #9e9e9e; }
        .stat.trash .number { color: #f44336; }

        .controls {
            display: flex;
            gap: 10px;
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

        .task-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-width: 1200px;
            margin: 0 auto;
        }

        .task-row {
            background: white;
            border-radius: 10px;
            padding: 15px 20px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.2);
            display: grid;
            grid-template-columns: 40px 1fr auto;
            gap: 20px;
            align-items: center;
            transition: all 0.2s;
        }
        .task-row:hover {
            transform: translateX(5px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.3);
        }

        .task-row.rated {
            opacity: 0.4;
        }

        .task-number {
            font-size: 1.2em;
            font-weight: bold;
            color: #999;
        }

        .task-info {
            flex: 1;
        }
        .task-name {
            font-size: 1.2em;
            font-weight: 600;
            color: #333;
            margin-bottom: 5px;
        }
        .task-meta {
            font-size: 0.85em;
            color: #999;
        }
        .task-domain {
            display: inline-block;
            background: #f3e5f5;
            color: #9c27b0;
            padding: 3px 10px;
            border-radius: 10px;
            font-size: 0.8em;
            font-weight: 600;
            margin-right: 10px;
        }

        .rating-buttons {
            display: flex;
            gap: 5px;
        }
        .rate-btn {
            width: 50px;
            height: 50px;
            border: none;
            border-radius: 8px;
            font-size: 1.3em;
            cursor: pointer;
            transition: all 0.2s;
            font-weight: bold;
        }
        .rate-btn:hover {
            transform: scale(1.1);
        }
        .rate-btn.premium { background: #e91e63; color: white; }
        .rate-btn.high { background: #2196f3; color: white; }
        .rate-btn.medium { background: #ff9800; color: white; }
        .rate-btn.low { background: #9e9e9e; color: white; }
        .rate-btn.trash { background: #f44336; color: white; }

        .keyboard-hint {
            background: rgba(0,0,0,0.3);
            color: white;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            margin-top: 20px;
            max-width: 1200px;
            margin-left: auto;
            margin-right: auto;
        }
        .key {
            display: inline-block;
            background: white;
            color: #333;
            padding: 5px 10px;
            border-radius: 5px;
            font-weight: bold;
            margin: 0 3px;
            font-family: monospace;
        }

        .load-more {
            text-align: center;
            margin: 30px 0;
        }
        .load-more button {
            padding: 15px 40px;
            background: white;
            color: #667eea;
            border: none;
            border-radius: 10px;
            font-size: 1.2em;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 5px 20px rgba(0,0,0,0.2);
        }
        .load-more button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.3);
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="stats">
            <div class="stat premium">
                <div class="number" id="premium-count">0</div>
                <div class="label">⭐ PREMIUM</div>
            </div>
            <div class="stat high">
                <div class="number" id="high-count">0</div>
                <div class="label">🔥 HIGH</div>
            </div>
            <div class="stat medium">
                <div class="number" id="medium-count">0</div>
                <div class="label">👍 MEDIUM</div>
            </div>
            <div class="stat low">
                <div class="number" id="low-count">0</div>
                <div class="label">👎 LOW</div>
            </div>
            <div class="stat trash">
                <div class="number" id="trash-count">0</div>
                <div class="label">🗑️ TRASH</div>
            </div>
        </div>
        <div class="controls">
            <button onclick="hideRated()">Hide Rated</button>
            <button onclick="showAll()">Show All</button>
            <button onclick="loadMore()">Load More</button>
        </div>
    </div>

    <div class="task-list" id="task-list"></div>

    <div class="load-more">
        <button onclick="loadMore()">Load 50 More Tasks</button>
    </div>

    <div class="keyboard-hint">
        <strong>Keyboard shortcuts:</strong> Click a task, then press
        <span class="key">5</span> Premium
        <span class="key">4</span> High
        <span class="key">3</span> Medium
        <span class="key">2</span> Low
        <span class="key">1</span> Trash
        | Or just click the emoji buttons!
    </div>

    <script>
        let allTasks = [];
        let displayedCount = 0;
        let stats = {PREMIUM: 0, HIGH: 0, MEDIUM: 0, LOW: 0, TRASH: 0};
        let selectedTaskId = null;

        async function init() {
            const response = await fetch('/api/unrated-tasks');
            allTasks = await response.json();
            loadMore();
        }

        function loadMore() {
            const batchSize = 50;
            const nextBatch = allTasks.slice(displayedCount, displayedCount + batchSize);

            nextBatch.forEach((task, index) => {
                addTaskRow(task, displayedCount + index + 1);
            });

            displayedCount += nextBatch.length;

            if (displayedCount >= allTasks.length) {
                document.querySelector('.load-more').style.display = 'none';
            }
        }

        function addTaskRow(task, number) {
            const list = document.getElementById('task-list');
            const row = document.createElement('div');
            row.className = 'task-row';
            row.dataset.id = task.id;
            row.id = 'task-' + task.id.replace(/[^a-z0-9]/gi, '_');

            row.innerHTML = `
                <div class="task-number">#${number}</div>
                <div class="task-info">
                    <div class="task-name">${task.name}</div>
                    <div class="task-meta">
                        <span class="task-domain">${task.domain.replace(/_/g, ' ')}</span>
                        ${task.children_count} subtasks
                    </div>
                </div>
                <div class="rating-buttons">
                    <button class="rate-btn premium" onclick="rate('${task.id}', 'PREMIUM')" title="5 - Premium">⭐</button>
                    <button class="rate-btn high" onclick="rate('${task.id}', 'HIGH')" title="4 - High">🔥</button>
                    <button class="rate-btn medium" onclick="rate('${task.id}', 'MEDIUM')" title="3 - Medium">👍</button>
                    <button class="rate-btn low" onclick="rate('${task.id}', 'LOW')" title="2 - Low">👎</button>
                    <button class="rate-btn trash" onclick="rate('${task.id}', 'TRASH')" title="1 - Trash">🗑️</button>
                </div>
            `;

            row.onclick = (e) => {
                if (!e.target.classList.contains('rate-btn')) {
                    selectTask(task.id);
                }
            };

            list.appendChild(row);
        }

        function selectTask(taskId) {
            // Deselect previous
            document.querySelectorAll('.task-row').forEach(r => {
                r.style.border = 'none';
            });

            // Select new
            const row = document.querySelector(`[data-id="${taskId}"]`);
            if (row) {
                row.style.border = '3px solid #667eea';
                selectedTaskId = taskId;
            }
        }

        async function rate(taskId, tier) {
            const row = document.querySelector(`[data-id="${taskId}"]`);
            row.classList.add('rated');

            await fetch('/api/rate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({task_id: taskId, tier: tier})
            });

            stats[tier]++;
            updateStats();

            // Auto-select next unrated task
            const allRows = Array.from(document.querySelectorAll('.task-row'));
            const currentIndex = allRows.findIndex(r => r.dataset.id === taskId);
            for (let i = currentIndex + 1; i < allRows.length; i++) {
                if (!allRows[i].classList.contains('rated')) {
                    allRows[i].scrollIntoView({ behavior: 'smooth', block: 'center' });
                    selectTask(allRows[i].dataset.id);
                    break;
                }
            }
        }

        function updateStats() {
            document.getElementById('premium-count').textContent = stats.PREMIUM;
            document.getElementById('high-count').textContent = stats.HIGH;
            document.getElementById('medium-count').textContent = stats.MEDIUM;
            document.getElementById('low-count').textContent = stats.LOW;
            document.getElementById('trash-count').textContent = stats.TRASH;
        }

        function hideRated() {
            document.querySelectorAll('.task-row.rated').forEach(row => {
                row.style.display = 'none';
            });
        }

        function showAll() {
            document.querySelectorAll('.task-row').forEach(row => {
                row.style.display = 'grid';
            });
        }

        // Keyboard controls
        document.addEventListener('keydown', (e) => {
            if (!selectedTaskId) return;

            if (e.key === '5') rate(selectedTaskId, 'PREMIUM');
            else if (e.key === '4') rate(selectedTaskId, 'HIGH');
            else if (e.key === '3') rate(selectedTaskId, 'MEDIUM');
            else if (e.key === '2') rate(selectedTaskId, 'LOW');
            else if (e.key === '1') rate(selectedTaskId, 'TRASH');
        });

        init();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/unrated-tasks')
def get_unrated_tasks():
    """Get all unrated tasks, shuffled."""
    unrated = [t for t in TASKS if t['id'] not in RATED_IDS]
    random.shuffle(unrated)
    return jsonify(unrated)

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

    RATED_IDS.add(task_id)

    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)
