from flask import Flask, request, jsonify, render_template_string
import json
import os
from datetime import datetime

app = Flask(__name__)
DATA_FILE = 'weight_records.json'

# HTML 模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>体重记录</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 600px; margin: 50px auto; padding: 20px;
            background: #f5f5f5;
        }
        h1 { text-align: center; color: #333; margin-bottom: 30px; }
        h2 { color: #333; margin-bottom: 16px; font-size: 18px; }
        .card {
            background: white; border-radius: 12px; padding: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px;
        }
        .form-group { margin-bottom: 16px; }
        label { display: block; margin-bottom: 8px; color: #666; }
        input[type="number"], input[type="date"] {
            width: 100%; padding: 12px; border: 1px solid #ddd;
            border-radius: 8px; font-size: 16px;
        }
        button {
            width: 100%; padding: 14px; background: #4CAF50;
            color: white; border: none; border-radius: 8px;
            font-size: 16px; cursor: pointer;
        }
        button:hover { background: #45a049; }
        .records { margin-top: 30px; }
        .record-item {
            background: white; padding: 16px; margin-bottom: 12px;
            border-radius: 8px; display: flex; justify-content: space-between;
            align-items: center;
        }
        .record-date { color: #666; }
        .record-weight { font-size: 20px; font-weight: bold; color: #4CAF50; }
        .record-time { font-size: 12px; color: #999; }
        .empty { text-align: center; color: #999; padding: 20px; }
        .delete-btn {
            background: #ff4757; padding: 6px 12px; font-size: 14px; width: auto;
        }
        .delete-btn:hover { background: #ff3344; }
        .chart-container {
            position: relative;
            height: 300px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <h1>📊 体重记录</h1>
    
    <div class="card">
        <div class="form-group">
            <label>日期</label>
            <input type="date" id="date" required>
        </div>
        <div class="form-group">
            <label>体重 (kg)</label>
            <input type="number" id="weight" step="0.1" placeholder="例如: 70.5" required>
        </div>
        <button onclick="addRecord()">记录体重</button>
    </div>

    <div class="card">
        <h2>📈 体重趋势</h2>
        <div class="chart-container">
            <canvas id="weightChart"></canvas>
        </div>
    </div>

    <div class="records">
        <h2>📋 记录历史</h2>
        <div id="recordsList"></div>
    </div>

    <script>
        let chart = null;
        
        // 设置默认日期为今天
        document.getElementById('date').valueAsDate = new Date();

        function loadRecords() {
            fetch('/api/records')
                .then(r => r.json())
                .then(data => {
                    // 更新列表
                    const list = document.getElementById('recordsList');
                    if (data.length === 0) {
                        list.innerHTML = '<div class="empty">暂无记录</div>';
                        updateChart([]);
                        return;
                    }
                    // 按日期倒序排列（用于显示列表）
                    const sortedData = [...data].sort((a, b) => new Date(b.date) - new Date(a.date));
                    list.innerHTML = sortedData.map(r => `
                        <div class="record-item">
                            <div>
                                <div class="record-date">${r.date}</div>
                                <div class="record-time">${r.time}</div>
                            </div>
                            <div style="display:flex;align-items:center;gap:12px;">
                                <span class="record-weight">${r.weight} kg</span>
                                <button class="delete-btn" onclick="deleteRecord('${r.id}')">删除</button>
                            </div>
                        </div>
                    `).join('');
                    
                    // 更新图表（按日期正序）
                    const chartData = [...data].sort((a, b) => new Date(a.date) - new Date(b.date));
                    updateChart(chartData);
                });
        }

        function updateChart(data) {
            const ctx = document.getElementById('weightChart').getContext('2d');
            const labels = data.map(r => r.date);
            const weights = data.map(r => r.weight);
            
            if (chart) {
                chart.destroy();
            }
            
            chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: '体重 (kg)',
                        data: weights,
                        borderColor: '#4CAF50',
                        backgroundColor: 'rgba(76, 175, 80, 0.1)',
                        fill: true,
                        tension: 0.3,
                        pointRadius: 5,
                        pointBackgroundColor: '#4CAF50'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: false,
                            title: {
                                display: true,
                                text: '体重 (kg)'
                            }
                        }
                    }
                }
            });
        }

        function addRecord() {
            const date = document.getElementById('date').value;
            const weight = parseFloat(document.getElementById('weight').value);
            
            if (!date || !weight) {
                alert('请填写日期和体重');
                return;
            }

            fetch('/api/records', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({date, weight})
            }).then(r => r.json())
              .then(data => {
                  if (data.success) {
                      document.getElementById('weight').value = '';
                      loadRecords();
                  }
              });
        }

        function deleteRecord(id) {
            if (!confirm('确定删除这条记录？')) return;
            fetch('/api/records/' + id, {method: 'DELETE'})
                .then(r => r.json())
                .then(data => {
                    if (data.success) loadRecords();
                });
        }

        loadRecords();
    </script>
</body>
</html>
'''

def load_records():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_records(records):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/records', methods=['GET'])
def get_records():
    return jsonify(load_records())

@app.route('/api/records', methods=['POST'])
def add_record():
    data = request.json
    records = load_records()
    
    new_record = {
        'id': str(datetime.now().timestamp()),
        'date': data['date'],
        'weight': data['weight'],
        'time': datetime.now().strftime('%H:%M:%S')
    }
    records.append(new_record)
    save_records(records)
    
    return jsonify({'success': True})

@app.route('/api/records/<record_id>', methods=['DELETE'])
def delete_record(record_id):
    records = load_records()
    records = [r for r in records if r['id'] != record_id]
    save_records(records)
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
