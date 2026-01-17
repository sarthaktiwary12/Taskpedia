#!/usr/bin/env python3
"""
Simple Intuitive Review App - Keyboard-driven, card-swiping style.

Press keys to rate:
- 1 = TRASH 🗑️
- 2 = LOW 👎
- 3 = MEDIUM 👍
- 4 = HIGH 🔥
- 5 = PREMIUM ⭐
- Space = Skip
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

# Get all tasks
TASKS = []
for task_id, task in MANIFEST.items():
    if task.get('node_type') == 'task':  # Focus on TASK level
        TASKS.append({
            'id': task_id,
            'name': task.get('name', ''),
            'domain': task_id.split('/')[0],
            'children_count': len(task.get('children_ids', [])),
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
    <title>TaskPedia Review - Simple</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }

        .container {
            width: 90%;
            max-width: 900px;
        }

        .stats-bar {
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
            display: flex;
            gap: 15px;
            justify-content: center;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }
        .stat {
            text-align: center;
            padding: 10px 20px;
        }
        .stat .number {
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .stat .label {
            font-size: 0.9em;
            color: #666;
        }
        .stat.premium .number { color: #e91e63; }
        .stat.high .number { color: #2196f3; }
        .stat.medium .number { color: #ff9800; }
        .stat.low .number { color: #9e9e9e; }
        .stat.trash .number { color: #f44336; }

        .card-container {
            perspective: 1000px;
            height: 400px;
            position: relative;
        }

        .card {
            background: white;
            border-radius: 20px;
            padding: 60px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            position: absolute;
            width: 100%;
            top: 0;
            left: 0;
            transition: transform 0.3s, opacity 0.3s;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
        }

        .card.swipe-left {
            transform: translateX(-1000px) rotate(-30deg);
            opacity: 0;
        }
        .card.swipe-right {
            transform: translateX(1000px) rotate(30deg);
            opacity: 0;
        }

        .card .domain {
            color: #9c27b0;
            font-size: 0.9em;
            font-weight: 600;
            text-transform: uppercase;
            margin-bottom: 20px;
            padding: 8px 20px;
            background: #f3e5f5;
            border-radius: 20px;
        }

        .card .task-name {
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
            margin-bottom: 20px;
            line-height: 1.2;
        }

        .card .meta {
            color: #999;
            font-size: 1.1em;
        }

        .card .id {
            color: #ccc;
            font-size: 0.9em;
            margin-top: 20px;
            font-family: monospace;
        }

        .controls {
            margin-top: 30px;
            display: flex;
            gap: 15px;
            justify-content: center;
        }

        .btn {
            padding: 20px 30px;
            border: none;
            border-radius: 15px;
            font-size: 1.5em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.2s;
            box-shadow: 0 5px 20px rgba(0,0,0,0.2);
            min-width: 120px;
        }
        .btn:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .btn:active {
            transform: translateY(-2px);
        }

        .btn-trash { background: #f44336; color: white; }
        .btn-low { background: #9e9e9e; color: white; }
        .btn-medium { background: #ff9800; color: white; }
        .btn-high { background: #2196f3; color: white; }
        .btn-premium { background: #e91e63; color: white; }

        .keyboard-hint {
            margin-top: 20px;
            text-align: center;
            color: white;
            background: rgba(0,0,0,0.3);
            padding: 15px;
            border-radius: 10px;
        }
        .keyboard-hint .key {
            display: inline-block;
            background: white;
            color: #333;
            padding: 5px 12px;
            border-radius: 5px;
            font-weight: bold;
            margin: 0 3px;
            font-family: monospace;
        }

        .progress {
            margin-top: 20px;
            background: rgba(255,255,255,0.3);
            height: 8px;
            border-radius: 10px;
            overflow: hidden;
        }
        .progress-bar {
            height: 100%;
            background: white;
            transition: width 0.5s;
        }

        .done-message {
            display: none;
            background: white;
            border-radius: 20px;
            padding: 60px;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .done-message.show {
            display: block;
        }
        .done-message h1 {
            font-size: 3em;
            color: #4caf50;
            margin-bottom: 20px;
        }
        .done-message p {
            font-size: 1.5em;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="stats-bar">
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
            <div class="stat">
                <div class="number" id="remaining-count">0</div>
                <div class="label">Remaining</div>
            </div>
        </div>

        <div class="card-container" id="card-container">
            <div class="card" id="current-card">
                <div class="domain" id="domain"></div>
                <div class="task-name" id="task-name">Loading...</div>
                <div class="meta" id="meta"></div>
                <div class="id" id="task-id"></div>
            </div>
        </div>

        <div class="done-message" id="done-message">
            <h1>🎉 All Done!</h1>
            <p>You've reviewed all tasks.</p>
            <p style="margin-top: 20px;">Refresh to review again or check your ratings.</p>
        </div>

        <div class="controls">
            <button class="btn btn-trash" onclick="rate('TRASH')">🗑️<br>TRASH</button>
            <button class="btn btn-low" onclick="rate('LOW')">👎<br>LOW</button>
            <button class="btn btn-medium" onclick="rate('MEDIUM')">👍<br>MEDIUM</button>
            <button class="btn btn-high" onclick="rate('HIGH')">🔥<br>HIGH</button>
            <button class="btn btn-premium" onclick="rate('PREMIUM')">⭐<br>PREMIUM</button>
        </div>

        <div class="keyboard-hint">
            Keyboard: <span class="key">1</span> Trash <span class="key">2</span> Low
            <span class="key">3</span> Medium <span class="key">4</span> High
            <span class="key">5</span> Premium <span class="key">Space</span> Skip
        </div>

        <div class="progress">
            <div class="progress-bar" id="progress-bar" style="width: 0%"></div>
        </div>
    </div>

    <script>
        let tasks = [];
        let currentIndex = 0;
        let stats = {PREMIUM: 0, HIGH: 0, MEDIUM: 0, LOW: 0, TRASH: 0};

        async function init() {
            const response = await fetch('/api/unrated-tasks');
            tasks = await response.json();

            if (tasks.length === 0) {
                showDone();
                return;
            }

            showTask();
            updateStats();
        }

        function showTask() {
            if (currentIndex >= tasks.length) {
                showDone();
                return;
            }

            const task = tasks[currentIndex];
            document.getElementById('domain').textContent = task.domain.replace(/_/g, ' ');
            document.getElementById('task-name').textContent = task.name;
            document.getElementById('meta').textContent = `${task.children_count} subtasks`;
            document.getElementById('task-id').textContent = task.id;

            updateProgress();
        }

        function showDone() {
            document.getElementById('card-container').style.display = 'none';
            document.querySelector('.controls').style.display = 'none';
            document.querySelector('.keyboard-hint').style.display = 'none';
            document.getElementById('done-message').classList.add('show');
        }

        async function rate(tier) {
            if (currentIndex >= tasks.length) return;

            const task = tasks[currentIndex];

            // Animate card out
            const card = document.getElementById('current-card');
            card.classList.add(tier === 'TRASH' || tier === 'LOW' ? 'swipe-left' : 'swipe-right');

            // Save rating
            await fetch('/api/rate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({task_id: task.id, tier: tier})
            });

            stats[tier]++;
            updateStats();

            // Move to next task
            setTimeout(() => {
                currentIndex++;
                card.classList.remove('swipe-left', 'swipe-right');
                showTask();
            }, 300);
        }

        function updateStats() {
            document.getElementById('premium-count').textContent = stats.PREMIUM;
            document.getElementById('high-count').textContent = stats.HIGH;
            document.getElementById('medium-count').textContent = stats.MEDIUM;
            document.getElementById('low-count').textContent = stats.LOW;
            document.getElementById('trash-count').textContent = stats.TRASH;
            document.getElementById('remaining-count').textContent = tasks.length - currentIndex;
        }

        function updateProgress() {
            const progress = (currentIndex / tasks.length) * 100;
            document.getElementById('progress-bar').style.width = progress + '%';
        }

        // Keyboard controls
        document.addEventListener('keydown', (e) => {
            if (e.key === '1') rate('TRASH');
            else if (e.key === '2') rate('LOW');
            else if (e.key === '3') rate('MEDIUM');
            else if (e.key === '4') rate('HIGH');
            else if (e.key === '5') rate('PREMIUM');
            else if (e.key === ' ') {
                e.preventDefault();
                currentIndex++;
                showTask();
            }
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
    app.run(host='0.0.0.0', port=5004, debug=True)
