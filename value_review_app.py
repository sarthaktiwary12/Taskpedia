#!/usr/bin/env python3
"""
Value-Focused Review App - Review tasks from robotics company POV.

Focus: Find the most MARKETABLE, IMPRESSIVE tasks that make robots valuable.
"""

import json
import random
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

# Group tasks by domain
TASKS_BY_DOMAIN = defaultdict(list)
for task_id, task in MANIFEST.items():
    if task.get('node_type') == 'task':  # Focus on TASK level
        domain = task_id.split('/')[0]
        TASKS_BY_DOMAIN[domain].append({
            'id': task_id,
            'name': task.get('name', ''),
            'domain': domain,
            'children_count': len(task.get('children_ids', [])),
        })

# HTML Template
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Value Review - Robotics Company POV</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1600px; margin: 0 auto; }

        .header {
            background: white;
            padding: 40px;
            border-radius: 20px;
            margin-bottom: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .header h1 {
            font-size: 3em;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        .header .subtitle {
            font-size: 1.2em;
            color: #666;
            margin-bottom: 20px;
        }
        .header .question {
            font-size: 1.5em;
            color: #333;
            font-weight: bold;
            background: #fff3cd;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #ff6b6b;
        }

        .stats {
            display: flex;
            gap: 15px;
            margin-top: 20px;
        }
        .stat-pill {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 25px;
            border-radius: 50px;
            font-size: 1.1em;
        }

        .domain-selector {
            background: white;
            padding: 25px;
            border-radius: 20px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .domain-selector h2 {
            margin-bottom: 20px;
            color: #333;
        }
        .domain-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 15px;
        }
        .domain-btn {
            padding: 20px;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            border: none;
            border-radius: 15px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            text-align: left;
        }
        .domain-btn:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .domain-btn .count {
            display: block;
            font-size: 2em;
            margin-bottom: 5px;
        }

        .tasks-view {
            display: none;
        }
        .tasks-view.active {
            display: block;
        }

        .tasks-header {
            background: white;
            padding: 25px;
            border-radius: 20px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .tasks-header h2 {
            color: #333;
            font-size: 2em;
        }
        .tasks-header button {
            padding: 12px 30px;
            background: #6c757d;
            color: white;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 1em;
            font-weight: 600;
        }

        .task-list {
            display: grid;
            gap: 15px;
        }
        .task-item {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.2);
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.3s;
        }
        .task-item:hover {
            transform: translateX(10px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }

        .task-info {
            flex: 1;
        }
        .task-info .name {
            font-size: 1.3em;
            font-weight: 600;
            color: #333;
            margin-bottom: 5px;
        }
        .task-info .meta {
            font-size: 0.9em;
            color: #999;
        }

        .value-rating {
            display: flex;
            gap: 10px;
            flex-shrink: 0;
        }
        .value-btn {
            padding: 15px 25px;
            border: none;
            border-radius: 10px;
            font-size: 1.1em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.2s;
            min-width: 120px;
        }
        .value-btn:hover {
            transform: translateY(-3px);
        }
        .value-btn.premium {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }
        .value-btn.high {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
        }
        .value-btn.medium {
            background: #ffc107;
            color: #333;
        }
        .value-btn.low {
            background: #e0e0e0;
            color: #666;
        }
        .value-btn.trash {
            background: #dc3545;
            color: white;
        }

        .rated {
            opacity: 0.5;
        }

        .progress-bar {
            background: white;
            padding: 20px;
            border-radius: 15px;
            margin-top: 20px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.2);
        }
        .progress-bar .bar {
            height: 30px;
            background: #e0e0e0;
            border-radius: 15px;
            overflow: hidden;
        }
        .progress-bar .fill {
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            transition: width 0.5s;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💎 Value Review: Robotics Company POV</h1>
            <div class="subtitle">Find the most MARKETABLE and IMPRESSIVE tasks</div>
            <div class="question">
                🤔 Would a robotics company building humanoids, bi-manual arms, or mobile manipulators
                want to demo this task to customers?
            </div>
            <div class="stats">
                <div class="stat-pill">⭐ Premium: <span id="premium-count">0</span></div>
                <div class="stat-pill">🔥 High: <span id="high-count">0</span></div>
                <div class="stat-pill">👍 Medium: <span id="medium-count">0</span></div>
                <div class="stat-pill">👎 Low: <span id="low-count">0</span></div>
                <div class="stat-pill">🗑️ Trash: <span id="trash-count">0</span></div>
            </div>
        </div>

        <div class="domain-selector" id="domain-selector">
            <h2>📂 Select a Domain to Review</h2>
            <div class="domain-grid" id="domain-grid"></div>
        </div>

        <div class="tasks-view" id="tasks-view">
            <div class="tasks-header">
                <h2 id="domain-title"></h2>
                <button onclick="backToDomains()">← Back to Domains</button>
            </div>
            <div class="task-list" id="task-list"></div>
            <div class="progress-bar">
                <div class="bar">
                    <div class="fill" id="progress-fill">0%</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let domains = {};
        let currentDomain = null;
        let ratings = {};

        // Load initial data
        async function init() {
            const response = await fetch('/api/domains');
            domains = await response.json();

            // Load existing ratings
            const ratingsResponse = await fetch('/api/ratings');
            ratings = await ratingsResponse.json();

            renderDomains();
            updateStats();
        }

        function renderDomains() {
            const grid = document.getElementById('domain-grid');
            grid.innerHTML = '';

            // Sort domains by task count
            const sortedDomains = Object.entries(domains).sort((a, b) => b[1].length - a[1].length);

            sortedDomains.forEach(([domain, tasks]) => {
                const btn = document.createElement('button');
                btn.className = 'domain-btn';
                btn.innerHTML = `
                    <span class="count">${tasks.length}</span>
                    <span>${domain.replace(/_/g, ' ')}</span>
                `;
                btn.onclick = () => showDomain(domain);
                grid.appendChild(btn);
            });
        }

        function showDomain(domain) {
            currentDomain = domain;
            document.getElementById('domain-selector').style.display = 'none';
            document.getElementById('tasks-view').classList.add('active');
            document.getElementById('domain-title').textContent = domain.replace(/_/g, ' ').toUpperCase();

            renderTasks();
        }

        function backToDomains() {
            document.getElementById('domain-selector').style.display = 'block';
            document.getElementById('tasks-view').classList.remove('active');
            currentDomain = null;
        }

        function renderTasks() {
            const list = document.getElementById('task-list');
            list.innerHTML = '';

            const tasks = domains[currentDomain];
            let ratedCount = 0;

            tasks.forEach(task => {
                const item = document.createElement('div');
                item.className = 'task-item';
                if (ratings[task.id]) {
                    item.classList.add('rated');
                    ratedCount++;
                }

                item.innerHTML = `
                    <div class="task-info">
                        <div class="name">${task.name}</div>
                        <div class="meta">${task.children_count} subtasks | ${task.id}</div>
                    </div>
                    <div class="value-rating">
                        <button class="value-btn premium" onclick="rate('${task.id}', 'PREMIUM')">⭐ PREMIUM</button>
                        <button class="value-btn high" onclick="rate('${task.id}', 'HIGH')">🔥 HIGH</button>
                        <button class="value-btn medium" onclick="rate('${task.id}', 'MEDIUM')">👍 MEDIUM</button>
                        <button class="value-btn low" onclick="rate('${task.id}', 'LOW')">👎 LOW</button>
                        <button class="value-btn trash" onclick="rate('${task.id}', 'TRASH')">🗑️ TRASH</button>
                    </div>
                `;

                list.appendChild(item);
            });

            // Update progress
            const progress = (ratedCount / tasks.length) * 100;
            document.getElementById('progress-fill').style.width = progress + '%';
            document.getElementById('progress-fill').textContent = Math.round(progress) + '%';
        }

        async function rate(taskId, tier) {
            ratings[taskId] = tier;

            await fetch('/api/rate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({task_id: taskId, tier: tier})
            });

            updateStats();
            renderTasks();
        }

        function updateStats() {
            const counts = {PREMIUM: 0, HIGH: 0, MEDIUM: 0, LOW: 0, TRASH: 0};
            Object.values(ratings).forEach(tier => {
                counts[tier]++;
            });

            document.getElementById('premium-count').textContent = counts.PREMIUM;
            document.getElementById('high-count').textContent = counts.HIGH;
            document.getElementById('medium-count').textContent = counts.MEDIUM;
            document.getElementById('low-count').textContent = counts.LOW;
            document.getElementById('trash-count').textContent = counts.TRASH;
        }

        init();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/domains')
def get_domains():
    """Get all domains with their tasks."""
    return jsonify(TASKS_BY_DOMAIN)

@app.route('/api/ratings')
def get_ratings():
    """Get existing ratings."""
    if not VALUE_RATINGS_PATH.exists():
        return jsonify({})

    ratings = {}
    with open(VALUE_RATINGS_PATH) as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                ratings[data['task_id']] = data['tier']

    return jsonify(ratings)

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

    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
