#!/usr/bin/env python3
"""
Web-based Task Review Interface.

Run: python review_app.py
Then open: http://localhost:5000
"""

from flask import Flask, render_template_string, request, jsonify
import json
import random
from pathlib import Path
from datetime import datetime

app = Flask(__name__)

# Data files
MANIFEST_FILE = Path("taskpedia-web/public/data/manifest.json")
APPROVED_FILE = Path("user_approved_tasks.jsonl")
REJECTED_FILE = Path("user_rejected_tasks.jsonl")
SESSION_STATE_FILE = Path("review_session_state.json")

# Load manifest
manifest = {}
if MANIFEST_FILE.exists():
    manifest = json.loads(MANIFEST_FILE.read_text())

# Track reviewed tasks in session
reviewed_ids = set()

# Load existing reviews
if APPROVED_FILE.exists():
    with open(APPROVED_FILE) as f:
        for line in f:
            reviewed_ids.add(json.loads(line)["task_id"])

if REJECTED_FILE.exists():
    with open(REJECTED_FILE) as f:
        for line in f:
            reviewed_ids.add(json.loads(line)["task_id"])

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Taskpedia Review Interface</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        .header {
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .header h1 {
            color: #667eea;
            font-size: 32px;
            margin-bottom: 10px;
        }
        .stats {
            display: flex;
            gap: 20px;
            margin-top: 15px;
        }
        .stat {
            flex: 1;
            background: #f7fafc;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-value {
            font-size: 28px;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            font-size: 14px;
            color: #718096;
            margin-top: 5px;
        }
        .card {
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .task-info {
            margin-bottom: 25px;
        }
        .task-name {
            font-size: 24px;
            font-weight: bold;
            color: #2d3748;
            margin-bottom: 15px;
        }
        .task-meta {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            margin-top: 10px;
        }
        .meta-item {
            background: #f7fafc;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 14px;
            color: #4a5568;
        }
        .meta-label {
            font-weight: 600;
            margin-right: 5px;
        }
        .buttons {
            display: flex;
            gap: 15px;
            margin-top: 25px;
        }
        button {
            flex: 1;
            padding: 15px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        .btn-approve {
            background: #48bb78;
            color: white;
        }
        .btn-approve:hover {
            background: #38a169;
        }
        .btn-reject {
            background: #f56565;
            color: white;
        }
        .btn-reject:hover {
            background: #e53e3e;
        }
        .btn-skip {
            background: #edf2f7;
            color: #4a5568;
        }
        .btn-skip:hover {
            background: #e2e8f0;
        }
        .reason-input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 14px;
            margin-top: 10px;
            display: none;
        }
        .reason-input.show {
            display: block;
        }
        .export-section {
            text-align: center;
            padding: 20px;
        }
        .btn-export {
            background: #667eea;
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
        }
        .btn-export:hover {
            background: #5a67d8;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #718096;
        }
        .filter-section {
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .filter-section select {
            padding: 10px;
            border-radius: 6px;
            border: 2px solid #e2e8f0;
            font-size: 14px;
            margin-right: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Taskpedia Quality Review</h1>
            <p style="color: #718096; margin-top: 10px;">Review and approve/reject generated tasks</p>
            <div class="stats">
                <div class="stat">
                    <div class="stat-value" id="approved-count">0</div>
                    <div class="stat-label">✅ Approved</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="rejected-count">0</div>
                    <div class="stat-label">❌ Rejected</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="reviewed-count">0</div>
                    <div class="stat-label">📊 Total Reviewed</div>
                </div>
            </div>
        </div>

        <div class="filter-section">
            <label style="font-weight: 600; margin-right: 10px;">Filter by type:</label>
            <select id="filter-type" onchange="loadTask()">
                <option value="">All types</option>
                <option value="atomic">Atomic</option>
                <option value="subtask">Subtask</option>
                <option value="task">Task</option>
                <option value="domain">Domain</option>
            </select>
        </div>

        <div class="card" id="task-card">
            <div class="loading">Loading task...</div>
        </div>

        <div class="card export-section">
            <button class="btn-export" onclick="exportFeedback()">
                📥 Export Feedback to File
            </button>
        </div>
    </div>

    <script>
        let currentTask = null;
        let stats = { approved: 0, rejected: 0, total: 0 };

        async function loadTask() {
            const filterType = document.getElementById('filter-type').value;
            const response = await fetch(`/api/next-task?type=${filterType}`);
            const data = await response.json();

            if (data.error) {
                document.getElementById('task-card').innerHTML = `
                    <div class="loading">${data.error}</div>
                `;
                return;
            }

            currentTask = data;
            displayTask(data);
        }

        function displayTask(task) {
            const card = document.getElementById('task-card');
            const parent = task.parent ? `<div class="meta-item"><span class="meta-label">Parent:</span>${task.parent}</div>` : '';
            const children = task.children_count > 0 ? `<div class="meta-item"><span class="meta-label">Children:</span>${task.children_count}</div>` : '';

            card.innerHTML = `
                <div class="task-info">
                    <div class="task-name">${task.name}</div>
                    <div class="task-meta">
                        <div class="meta-item"><span class="meta-label">Type:</span>${task.type}</div>
                        <div class="meta-item"><span class="meta-label">ID:</span><code style="font-size: 11px;">${task.id}</code></div>
                        ${parent}
                        ${children}
                    </div>
                </div>
                <input type="text" id="reject-reason" class="reason-input" placeholder="Why reject? (optional)">
                <div class="buttons">
                    <button class="btn-approve" onclick="approve()">✅ Approve</button>
                    <button class="btn-reject" onclick="showRejectInput()">❌ Reject</button>
                    <button class="btn-skip" onclick="skip()">⏭️ Skip</button>
                </div>
            `;
        }

        function showRejectInput() {
            const reasonInput = document.getElementById('reject-reason');
            reasonInput.classList.add('show');
            reasonInput.focus();

            // Change button to confirm
            const rejectBtn = document.querySelector('.btn-reject');
            rejectBtn.textContent = '✓ Confirm Reject';
            rejectBtn.onclick = reject;
        }

        async function approve() {
            await submitFeedback('approve');
            stats.approved++;
            stats.total++;
            updateStats();
            loadTask();
        }

        async function reject() {
            const reason = document.getElementById('reject-reason').value;
            await submitFeedback('reject', reason);
            stats.rejected++;
            stats.total++;
            updateStats();
            loadTask();
        }

        async function skip() {
            loadTask();
        }

        async function submitFeedback(action, reason = '') {
            await fetch('/api/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    task_id: currentTask.id,
                    action: action,
                    reason: reason
                })
            });
        }

        async function exportFeedback() {
            const response = await fetch('/api/export');
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `taskpedia_feedback_${new Date().toISOString().split('T')[0]}.json`;
            a.click();
        }

        function updateStats() {
            document.getElementById('approved-count').textContent = stats.approved;
            document.getElementById('rejected-count').textContent = stats.rejected;
            document.getElementById('reviewed-count').textContent = stats.total;
        }

        async function loadStats() {
            const response = await fetch('/api/stats');
            stats = await response.json();
            updateStats();
        }

        // Load initial task and stats
        loadTask();
        loadStats();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/next-task')
def next_task():
    """Get next task to review."""
    filter_type = request.args.get('type', '')

    # Filter candidates
    candidates = []
    for task_id, task in manifest.items():
        if task_id in reviewed_ids:
            continue
        if filter_type and task.get('node_type') != filter_type:
            continue
        # Prefer LLM-generated tasks
        if 'llm_generated' in str(task.get('sources', [])).lower():
            candidates.append((task_id, task))

    if not candidates:
        # Fall back to any unreviewed
        candidates = [(tid, t) for tid, t in manifest.items() if tid not in reviewed_ids]

    if not candidates:
        return jsonify({'error': 'No more tasks to review!'})

    task_id, task = random.choice(candidates)

    # Get parent info
    parent_name = None
    if task.get('parent_id'):
        parent = manifest.get(task['parent_id'], {})
        parent_name = parent.get('name', 'Unknown')

    return jsonify({
        'id': task_id,
        'name': task['name'],
        'type': task['node_type'],
        'parent': parent_name,
        'children_count': len(task.get('children_ids', []))
    })

@app.route('/api/feedback', methods=['POST'])
def feedback():
    """Submit feedback for a task."""
    data = request.json
    task_id = data['task_id']
    action = data['action']
    reason = data.get('reason', '')

    task = manifest.get(task_id, {})

    feedback_entry = {
        'task_id': task_id,
        'name': task.get('name', ''),
        'type': task.get('node_type', ''),
        'parent_id': task.get('parent_id', ''),
        'approved': action == 'approve',
        'reason': reason,
        'timestamp': datetime.utcnow().isoformat()
    }

    target_file = APPROVED_FILE if action == 'approve' else REJECTED_FILE
    with open(target_file, 'a') as f:
        f.write(json.dumps(feedback_entry) + '\n')

    reviewed_ids.add(task_id)

    return jsonify({'status': 'success'})

@app.route('/api/stats')
def stats():
    """Get current stats."""
    approved = 0
    rejected = 0

    if APPROVED_FILE.exists():
        with open(APPROVED_FILE) as f:
            approved = sum(1 for _ in f)

    if REJECTED_FILE.exists():
        with open(REJECTED_FILE) as f:
            rejected = sum(1 for _ in f)

    return jsonify({
        'approved': approved,
        'rejected': rejected,
        'total': approved + rejected
    })

@app.route('/api/export')
def export():
    """Export all feedback as JSON."""
    feedback = {
        'approved': [],
        'rejected': [],
        'stats': {}
    }

    if APPROVED_FILE.exists():
        with open(APPROVED_FILE) as f:
            feedback['approved'] = [json.loads(line) for line in f]

    if REJECTED_FILE.exists():
        with open(REJECTED_FILE) as f:
            feedback['rejected'] = [json.loads(line) for line in f]

    feedback['stats'] = {
        'total_approved': len(feedback['approved']),
        'total_rejected': len(feedback['rejected']),
        'total_reviewed': len(feedback['approved']) + len(feedback['rejected']),
        'export_date': datetime.utcnow().isoformat()
    }

    return jsonify(feedback)

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🌐 TASKPEDIA REVIEW INTERFACE")
    print("="*60)
    print("\n📍 Open in your browser: http://localhost:5000")
    print("\n⌨️  Press Ctrl+C to stop the server\n")
    app.run(host='0.0.0.0', port=5000, debug=False)
