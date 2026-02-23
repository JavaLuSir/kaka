from flask import Flask, request, jsonify, render_template_string
import json
import os
from datetime import datetime

app = Flask(__name__)
DATA_FILE = 'weight_records.json'
PER_PAGE = 10

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
        .pagination {
            display: flex;
            justify-content: center;
            gap: 8px;
            margin-top: 20px;
        }
        .pagination button {
            width: auto;
            padding: 8px 14px;
            background: #667eea;
        }
        .pagination button:hover { background: #5568d3; }
        .pagination button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        .pagination .page-info {
            display: flex;
            align-items: center;
            color: #666;
            font-size: 14px;
        }
        .stat-card {
            display: flex;
            justify-content: space-around;
            margin-bottom: 20px;
        }
        .stat-item {
            text-align: center;
        }
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #4CAF50;
        }
        .stat-label {
            font-size: 12px;
            color: #999;
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

    <div class="card">
        <h2>📊 数据统计</h2>
        <div class="stat-card">
            <div class="stat-item">
                <div class="stat-value" id="totalCount">-</div>
                <div class="stat-label">总记录数</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="avgWeight">-</div>
                <div class="stat-label">平均体重 (kg)</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="latestWeight">-</div>
                <div class="stat-label">最新体重 (kg)</div>
            </div>
        </div>
    </div>

    <div class="records">
        <h2>📋 记录历史</h2>
        <div id="recordsList"></div>
        <div class="pagination" id="pagination"></div>
    </div>

    <script>
        let chart = null;
        let currentPage = 1;
        let totalPages = 1;
        
        // 设置默认日期为今天
        document.getElementById('date').valueAsDate = new Date();

        function loadRecords(page = 1) {
            currentPage = page;
            fetch('/api/records?page=' + page)
                .then(r => r.json())
                .then(data => {
                    const list = document.getElementById('recordsList');
                    if (data.records.length === 0) {
                        list.innerHTML = '<div class="empty">暂无记录</div>';
                        document.getElementById('pagination').innerHTML = '';
                        updateChart([]);
                        updateStats(null);
                        return;
                    }
                    
                    // 更新列表
                    list.innerHTML = data.records.map(r => `
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
                    
                    // 更新分页
                    totalPages = data.totalPages;
                    renderPagination();
                    
                    // 更新统计
                    updateStats(data);
                    
                    // 更新图表（使用所有数据）
                    fetch('/api/records?page=1&per_page=1000')
                        .then(r => r.json())
                        .then(allData => {
                            const sortedData = allData.records.sort((a, b) => new Date(a.date) - new Date(b.date));
                            updateChart(sortedData);
                        });
                });
        }

        function renderPagination() {
            const pagination = document.getElementById('pagination');
            if (totalPages <= 1) {
                pagination.innerHTML = '';
                return;
            }
            
            let html = `<button ${currentPage === 1 ? 'disabled' : ''} onclick="loadRecords(1)">首页</button>`;
            html += `<button ${currentPage === 1 ? 'disabled' : ''} onclick="loadRecords(${currentPage - 1})">上一页</button>`;
            html += `<span class="page-info">${currentPage} / ${totalPages}</span>`;
            html += `<button ${currentPage === totalPages ? 'disabled' : ''} onclick="loadRecords(${currentPage + 1})">下一页</button>`;
            html += `<button ${currentPage === totalPages ? 'disabled' : ''} onclick="loadRecords(${totalPages})">末页</button>`;
            
            pagination.innerHTML = html;
        }

        function updateStats(data) {
            if (!data || data.records.length === 0) {
                document.getElementById('totalCount').textContent = '-';
                document.getElementById('avgWeight').textContent = '-';
                document.getElementById('latestWeight').textContent = '-';
                return;
            }
            
            const total = data.total;
            const weights = data.records.map(r => r.weight);
            const avg = (weights.reduce((a, b) => a + b, 0) / weights.length).toFixed(1);
            
            // 最新体重（当前页的第一条，因为是倒序）
            const latest = data.records[0].weight;
            
            document.getElementById('totalCount').textContent = total;
            document.getElementById('avgWeight').textContent = avg;
            document.getElementById('latestWeight').textContent = latest;
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
                      loadRecords(1);
                  }
              });
        }

        function deleteRecord(id) {
            if (!confirm('确定删除这条记录？')) return;
            fetch('/api/records/' + id, {method: 'DELETE'})
                .then(r => r.json())
                .then(data => {
                    if (data.success) loadRecords(currentPage);
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
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', PER_PAGE, type=int)
    
    all_records = load_records()
    
    # 按日期倒序排列
    all_records.sort(key=lambda x: x['date'], reverse=True)
    
    total = len(all_records)
    total_pages = (total + per_page - 1) // per_page
    
    start = (page - 1) * per_page
    end = start + per_page
    records = all_records[start:end]
    
    return jsonify({
        'records': records,
        'total': total,
        'page': page,
        'per_page': per_page,
        'totalPages': total_pages
    })

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
