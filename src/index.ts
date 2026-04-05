import { Hono } from 'hono'
import { cors } from 'hono/cors'

type Bindings = {
  WEIGHT_KV: KVNamespace
}

const app = new Hono<{ Bindings: Bindings }>()

app.use('/*', cors())

const PER_PAGE = 10
const DATA_KEY = 'weight_records'

async function loadRecords(env: Bindings) {
  const data = await env.WEIGHT_KV.get(DATA_KEY, 'json')
  return (data as any[]) || []
}

async function saveRecords(env: Bindings, records: any[]) {
  await env.WEIGHT_KV.put(DATA_KEY, JSON.stringify(records))
}

app.get('/', (c) => {
  return c.html(`
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>体重记录</title>
    <script src="https://cdn.jsdelivr.net/npm/flatpickr"></script>
    <script src="https://cdn.jsdelivr.net/npm/flatpickr/dist/l10n/zh.js"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/themes/material_blue.css">
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
        input[type="number"] {
            width: 100%; padding: 12px; border: 1px solid #ddd;
            border-radius: 8px; font-size: 16px;
        }
        .date-input {
            width: 100%; padding: 12px; border: 1px solid #ddd;
            border-radius: 8px; font-size: 16px;
            background: white;
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
            <input type="text" id="date" class="date-input" required>
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
        
        flatpickr("#date", {
            locale: "zh",
            dateFormat: "Y-m-d",
            defaultDate: new Date()
        });

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
                    
                    list.innerHTML = data.records.map(r => \`
                        <div class="record-item">
                            <div>
                                <div class="record-date">\${r.date}</div>
                                <div class="record-time">\${r.time}</div>
                            </div>
                            <div style="display:flex;align-items:center;gap:12px;">
                                <span class="record-weight">\${r.weight} kg</span>
                                <button class="delete-btn" onclick="deleteRecord('\${r.id}')">删除</button>
                            </div>
                        </div>
                    \`).join('');
                    
                    totalPages = data.totalPages;
                    renderPagination();
                    updateStats(data);
                    
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
            
            let html = \`<button \${currentPage === 1 ? 'disabled' : ''} onclick="loadRecords(1)">首页</button>\`;
            html += \`<button \${currentPage === 1 ? 'disabled' : ''} onclick="loadRecords(\${currentPage - 1})">上一页</button>\`;
            html += \`<span class="page-info">\${currentPage} / \${totalPages}</span>\`;
            html += \`<button \${currentPage === totalPages ? 'disabled' : ''} onclick="loadRecords(\${currentPage + 1})">下一页</button>\`;
            html += \`<button \${currentPage === totalPages ? 'disabled' : ''} onclick="loadRecords(\${totalPages})">末页</button>\`;
            
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
  `)
})

app.get('/api/records', async (c) => {
  const page = parseInt(c.req.query('page') || '1')
  const perPage = parseInt(c.req.query('per_page') || String(PER_PAGE))

  const allRecords = await loadRecords(c.env)
  allRecords.sort((a, b) => b.date.localeCompare(a.date))

  const total = allRecords.length
  const totalPages = Math.ceil(total / perPage) || 1

  const start = (page - 1) * perPage
  const end = start + perPage
  const records = allRecords.slice(start, end)

  return c.json({
    records,
    total,
    page,
    per_page: perPage,
    totalPages
  })
})

app.post('/api/records', async (c) => {
  const data = await c.req.json()
  const records = await loadRecords(c.env)

  const newRecord = {
    id: String(Date.now()),
    date: data.date,
    weight: data.weight,
    time: new Date().toTimeString().split(' ')[0]
  }
  records.push(newRecord)
  await saveRecords(c.env, records)

  return c.json({ success: true })
})

app.delete('/api/records/:id', async (c) => {
  const id = c.req.param('id')
  const records = await loadRecords(c.env)
  const filtered = records.filter(r => r.id !== id)
  await saveRecords(c.env, filtered)

  return c.json({ success: true })
})

export default app
