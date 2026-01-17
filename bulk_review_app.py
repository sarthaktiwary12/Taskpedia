#!/usr/bin/env python3
"""
Bulk Task Review Application - Review tasks in large batches
"""

import json
import random
from pathlib import Path
from flask import Flask, render_template_string, jsonify, request
from datetime import datetime

app = Flask(__name__)

# Paths
MANIFEST_PATH = Path("/workspaces/Taskpedia/taskpedia-web/public/data/manifest.json")
APPROVED_PATH = Path("/workspaces/Taskpedia/user_approved_tasks.jsonl")
REJECTED_PATH = Path("/workspaces/Taskpedia/user_rejected_tasks.jsonl")
REVIEWED_IDS_PATH = Path("/workspaces/Taskpedia/reviewed_ids.json")

# Load manifest
with open(MANIFEST_PATH) as f:
    MANIFEST = json.load(f)

# Track reviewed IDs
def load_reviewed_ids():
    if REVIEWED_IDS_PATH.exists():
        with open(REVIEWED_IDS_PATH) as f:
            return set(json.load(f))
    return set()

def save_reviewed_ids(ids):
    with open(REVIEWED_IDS_PATH, 'w') as f:
        json.dump(list(ids), f)

REVIEWED_IDS = load_reviewed_ids()

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Taskpedia Bulk Review</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        .header {
            background: white;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            margin-bottom: 30px;
        }

        .header h1 {
            font-size: 2.5em;
            color: #667eea;
            margin-bottom: 10px;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }

        .stat-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }

        .stat-box .number {
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }

        .stat-box .label {
            font-size: 0.9em;
            opacity: 0.9;
        }

        .controls {
            background: white;
            padding: 25px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            align-items: center;
        }

        .controls label {
            font-weight: 600;
            color: #333;
        }

        .controls select, .controls input {
            padding: 10px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 1em;
            background: white;
        }

        .controls button {
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }

        .controls button:hover {
            transform: translateY(-2px);
        }

        .controls button:active {
            transform: translateY(0);
        }

        .tasks-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .task-card {
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: all 0.3s;
            cursor: pointer;
            position: relative;
            border: 3px solid transparent;
        }

        .task-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.3);
        }

        .task-card.selected-approve {
            border-color: #4CAF50;
            background: #f1f8f4;
        }

        .task-card.selected-reject {
            border-color: #f44336;
            background: #fef1f0;
        }

        .task-card .type-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.75em;
            font-weight: 600;
            text-transform: uppercase;
            margin-bottom: 10px;
        }

        .type-badge.atomic { background: #e3f2fd; color: #1976d2; }
        .type-badge.subtask { background: #f3e5f5; color: #7b1fa2; }
        .type-badge.task { background: #fff3e0; color: #f57c00; }
        .type-badge.domain { background: #e8f5e9; color: #388e3c; }

        .task-card .name {
            font-size: 1.1em;
            font-weight: 600;
            color: #333;
            margin-bottom: 10px;
            word-wrap: break-word;
        }

        .task-card .id {
            font-size: 0.85em;
            color: #999;
            margin-bottom: 10px;
            font-family: monospace;
            word-wrap: break-word;
        }

        .task-card .description {
            font-size: 0.9em;
            color: #666;
            line-height: 1.4;
            margin-bottom: 10px;
            max-height: 60px;
            overflow: hidden;
        }

        .selection-indicator {
            position: absolute;
            top: 10px;
            right: 10px;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: none;
            align-items: center;
            justify-content: center;
            font-size: 1.2em;
            color: white;
        }

        .task-card.selected-approve .selection-indicator,
        .task-card.selected-reject .selection-indicator {
            display: flex;
        }

        .selected-approve .selection-indicator {
            background: #4CAF50;
        }

        .selected-reject .selection-indicator {
            background: #f44336;
        }

        .bulk-actions {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: white;
            padding: 25px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            display: none;
            z-index: 1000;
        }

        .bulk-actions.visible {
            display: block;
        }

        .bulk-actions h3 {
            margin-bottom: 15px;
            color: #333;
        }

        .bulk-actions .count {
            display: flex;
            gap: 20px;
            margin-bottom: 15px;
        }

        .bulk-actions .count-item {
            text-align: center;
        }

        .bulk-actions .count-item .number {
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }

        .bulk-actions .count-item.approve .number { color: #4CAF50; }
        .bulk-actions .count-item.reject .number { color: #f44336; }

        .bulk-actions .actions {
            display: flex;
            gap: 10px;
        }

        .bulk-actions button {
            flex: 1;
            padding: 12px;
            border: none;
            border-radius: 10px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }

        .bulk-actions button:hover {
            transform: translateY(-2px);
        }

        .bulk-actions .btn-submit {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .bulk-actions .btn-clear {
            background: #e0e0e0;
            color: #666;
        }

        .loading {
            text-align: center;
            padding: 40px;
            color: white;
            font-size: 1.2em;
        }

        .mode-selector {
            display: flex;
            gap: 10px;
            margin-right: auto;
        }

        .mode-btn {
            padding: 10px 20px;
            background: #f0f0f0;
            border: 2px solid transparent;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
        }

        .mode-btn.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-color: #667eea;
        }

        @media (max-width: 768px) {
            .tasks-grid {
                grid-template-columns: 1fr;
            }

            .bulk-actions {
                left: 20px;
                right: 20px;
                bottom: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 Taskpedia Bulk Review</h1>
            <p style="color: #666; margin-top: 10px;">Review tasks in batches - Click to select, bulk approve/reject</p>

            <div class="stats">
                <div class="stat-box">
                    <div class="number" id="stat-total">0</div>
                    <div class="label">Total Tasks</div>
                </div>
                <div class="stat-box">
                    <div class="number" id="stat-reviewed">0</div>
                    <div class="label">Already Reviewed</div>
                </div>
                <div class="stat-box">
                    <div class="number" id="stat-pending">0</div>
                    <div class="label">Pending Review</div>
                </div>
                <div class="stat-box">
                    <div class="number" id="stat-approved">0</div>
                    <div class="label">Approved (Session)</div>
                </div>
                <div class="stat-box">
                    <div class="number" id="stat-rejected">0</div>
                    <div class="label">Rejected (Session)</div>
                </div>
            </div>
        </div>

        <div class="controls">
            <div class="mode-selector">
                <button class="mode-btn active" data-mode="select">Select Mode</button>
                <button class="mode-btn" data-mode="approve">Quick Approve</button>
                <button class="mode-btn" data-mode="reject">Quick Reject</button>
            </div>

            <label>
                Type:
                <select id="filter-type">
                    <option value="all">All Types</option>
                    <option value="atomic">Atomic Only</option>
                    <option value="subtask">Subtask Only</option>
                    <option value="task">Task Only</option>
                    <option value="domain">Domain Only</option>
                </select>
            </label>

            <label>
                Per Page:
                <select id="page-size">
                    <option value="20">20</option>
                    <option value="50" selected>50</option>
                    <option value="100">100</option>
                    <option value="200">200</option>
                </select>
            </label>

            <button onclick="loadTasks()">Load Tasks</button>
            <button onclick="exportFeedback()">Export Feedback</button>
        </div>

        <div id="tasks-container">
            <div class="loading">Click "Load Tasks" to start reviewing</div>
        </div>

        <div class="bulk-actions" id="bulk-actions">
            <h3>Bulk Actions</h3>
            <div class="count">
                <div class="count-item approve">
                    <div class="number" id="approve-count">0</div>
                    <div class="label">To Approve</div>
                </div>
                <div class="count-item reject">
                    <div class="number" id="reject-count">0</div>
                    <div class="label">To Reject</div>
                </div>
            </div>
            <div class="actions">
                <button class="btn-submit" onclick="submitBulkFeedback()">Submit</button>
                <button class="btn-clear" onclick="clearSelections()">Clear</button>
            </div>
        </div>
    </div>

    <script>
        let currentMode = 'select';
        let selectedApprove = new Set();
        let selectedReject = new Set();
        let sessionApproved = 0;
        let sessionRejected = 0;

        // Mode switching
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentMode = btn.dataset.mode;
            });
        });

        // Load tasks
        async function loadTasks() {
            const type = document.getElementById('filter-type').value;
            const pageSize = document.getElementById('page-size').value;

            document.getElementById('tasks-container').innerHTML = '<div class="loading">Loading tasks...</div>';

            const response = await fetch(`/api/bulk-tasks?type=${type}&limit=${pageSize}`);
            const data = await response.json();

            renderTasks(data.tasks);
            updateStats(data.stats);
        }

        // Render tasks
        function renderTasks(tasks) {
            const container = document.getElementById('tasks-container');

            if (tasks.length === 0) {
                container.innerHTML = '<div class="loading">No more tasks to review!</div>';
                return;
            }

            const grid = document.createElement('div');
            grid.className = 'tasks-grid';

            tasks.forEach(task => {
                const card = document.createElement('div');
                card.className = 'task-card';
                card.dataset.id = task.id;

                card.innerHTML = `
                    <span class="type-badge ${task.type}">${task.type}</span>
                    <div class="name">${task.name}</div>
                    <div class="id">${task.id}</div>
                    <div class="description">${task.description || 'No description'}</div>
                    <div class="selection-indicator">✓</div>
                `;

                card.addEventListener('click', () => handleCardClick(card, task.id));
                grid.appendChild(card);
            });

            container.innerHTML = '';
            container.appendChild(grid);
        }

        // Handle card click
        function handleCardClick(card, taskId) {
            if (currentMode === 'select') {
                // Toggle between approve/reject/unselected
                if (card.classList.contains('selected-approve')) {
                    card.classList.remove('selected-approve');
                    card.classList.add('selected-reject');
                    selectedApprove.delete(taskId);
                    selectedReject.add(taskId);
                } else if (card.classList.contains('selected-reject')) {
                    card.classList.remove('selected-reject');
                    selectedReject.delete(taskId);
                } else {
                    card.classList.add('selected-approve');
                    selectedApprove.add(taskId);
                }
            } else if (currentMode === 'approve') {
                // Quick approve mode
                card.classList.remove('selected-reject');
                card.classList.add('selected-approve');
                selectedReject.delete(taskId);
                selectedApprove.add(taskId);
            } else if (currentMode === 'reject') {
                // Quick reject mode
                card.classList.remove('selected-approve');
                card.classList.add('selected-reject');
                selectedApprove.delete(taskId);
                selectedReject.add(taskId);
            }

            updateBulkActions();
        }

        // Update bulk actions panel
        function updateBulkActions() {
            document.getElementById('approve-count').textContent = selectedApprove.size;
            document.getElementById('reject-count').textContent = selectedReject.size;

            const panel = document.getElementById('bulk-actions');
            if (selectedApprove.size > 0 || selectedReject.size > 0) {
                panel.classList.add('visible');
            } else {
                panel.classList.remove('visible');
            }
        }

        // Submit bulk feedback
        async function submitBulkFeedback() {
            if (selectedApprove.size === 0 && selectedReject.size === 0) {
                alert('No tasks selected!');
                return;
            }

            const feedback = {
                approved: Array.from(selectedApprove),
                rejected: Array.from(selectedReject)
            };

            const response = await fetch('/api/bulk-feedback', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(feedback)
            });

            const result = await response.json();

            sessionApproved += selectedApprove.size;
            sessionRejected += selectedReject.size;

            // Clear selections and reload
            clearSelections();
            loadTasks();

            alert(`Submitted! Approved: ${result.approved_count}, Rejected: ${result.rejected_count}`);
        }

        // Clear selections
        function clearSelections() {
            selectedApprove.clear();
            selectedReject.clear();

            document.querySelectorAll('.task-card').forEach(card => {
                card.classList.remove('selected-approve', 'selected-reject');
            });

            updateBulkActions();
        }

        // Update stats
        function updateStats(stats) {
            document.getElementById('stat-total').textContent = stats.total.toLocaleString();
            document.getElementById('stat-reviewed').textContent = stats.reviewed.toLocaleString();
            document.getElementById('stat-pending').textContent = stats.pending.toLocaleString();
            document.getElementById('stat-approved').textContent = sessionApproved.toLocaleString();
            document.getElementById('stat-rejected').textContent = sessionRejected.toLocaleString();
        }

        // Export feedback
        async function exportFeedback() {
            window.location.href = '/api/export';
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && (selectedApprove.size > 0 || selectedReject.size > 0)) {
                submitBulkFeedback();
            } else if (e.key === 'Escape') {
                clearSelections();
            }
        });
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/bulk-tasks')
def bulk_tasks():
    """Get a batch of unreviewed tasks."""
    type_filter = request.args.get('type', 'all')
    limit = int(request.args.get('limit', 50))

    # Filter tasks
    candidates = []
    for task_id, task in MANIFEST.items():
        if task_id in REVIEWED_IDS:
            continue

        if type_filter != 'all' and task.get('node_type') != type_filter:
            continue

        candidates.append({
            'id': task_id,
            'name': task.get('name', ''),
            'type': task.get('node_type', 'unknown'),
            'description': task.get('description', ''),
        })

    # Random sample
    random.shuffle(candidates)
    tasks = candidates[:limit]

    stats = {
        'total': len(MANIFEST),
        'reviewed': len(REVIEWED_IDS),
        'pending': len(MANIFEST) - len(REVIEWED_IDS),
    }

    return jsonify({'tasks': tasks, 'stats': stats})


@app.route('/api/bulk-feedback', methods=['POST'])
def bulk_feedback():
    """Submit bulk feedback."""
    data = request.json
    approved_ids = data.get('approved', [])
    rejected_ids = data.get('rejected', [])

    timestamp = datetime.utcnow().isoformat()

    # Save approved
    for task_id in approved_ids:
        if task_id in MANIFEST:
            task = MANIFEST[task_id]
            record = {
                'id': task_id,
                'name': task.get('name', ''),
                'type': task.get('node_type', ''),
                'description': task.get('description', ''),
                'timestamp': timestamp,
            }
            with open(APPROVED_PATH, 'a') as f:
                f.write(json.dumps(record) + '\n')
            REVIEWED_IDS.add(task_id)

    # Save rejected
    for task_id in rejected_ids:
        if task_id in MANIFEST:
            task = MANIFEST[task_id]
            record = {
                'id': task_id,
                'name': task.get('name', ''),
                'type': task.get('node_type', ''),
                'description': task.get('description', ''),
                'reason': 'Bulk rejected',
                'timestamp': timestamp,
            }
            with open(REJECTED_PATH, 'a') as f:
                f.write(json.dumps(record) + '\n')
            REVIEWED_IDS.add(task_id)

    # Save reviewed IDs
    save_reviewed_ids(REVIEWED_IDS)

    return jsonify({
        'approved_count': len(approved_ids),
        'rejected_count': len(rejected_ids),
    })


@app.route('/api/export')
def export():
    """Export all feedback as JSON."""
    approved = []
    rejected = []

    if APPROVED_PATH.exists():
        with open(APPROVED_PATH) as f:
            approved = [json.loads(line) for line in f if line.strip()]

    if REJECTED_PATH.exists():
        with open(REJECTED_PATH) as f:
            rejected = [json.loads(line) for line in f if line.strip()]

    export_data = {
        'approved': approved,
        'rejected': rejected,
        'stats': {
            'total_approved': len(approved),
            'total_rejected': len(rejected),
        }
    }

    return jsonify(export_data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
