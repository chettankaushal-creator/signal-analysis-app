from flask import Flask, request, jsonify, render_template_string
import os
import math
import base64
from io import BytesIO
import matplotlib
matplotlib.use('Agg')  # For server-side plotting
import matplotlib.pyplot as plt
import numpy as np

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Signal Analysis Tool - With Graphs</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .content {
            padding: 30px;
        }
        
        .upload-section {
            background: #f7f9fc;
            border-radius: 15px;
            padding: 30px;
            text-align: center;
            margin-bottom: 30px;
            border: 2px dashed #667eea;
        }
        
        .upload-section h3 {
            color: #333;
            margin-bottom: 10px;
        }
        
        .upload-section input {
            padding: 12px 24px;
            font-size: 16px;
            border: 1px solid #ddd;
            border-radius: 8px;
            margin: 15px;
            cursor: pointer;
        }
        
        .upload-section button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            font-size: 16px;
            border-radius: 8px;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .upload-section button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102,126,234,0.4);
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 40px;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .error {
            background: #fee;
            color: #c33;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
            display: none;
            text-align: center;
        }
        
        .results {
            display: none;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            transition: transform 0.2s;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-card h3 {
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 10px;
        }
        
        .stat-card .value {
            font-size: 1.8em;
            font-weight: bold;
        }
        
        .plot-container {
            background: #f7f9fc;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
        }
        
        .plot-container h3 {
            color: #333;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        
        .plot-container img {
            width: 100%;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .insights {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            margin-top: 20px;
        }
        
        .insights h3 {
            margin-bottom: 15px;
        }
        
        .insights ul {
            margin-left: 20px;
        }
        
        .insights li {
            margin: 10px 0;
            line-height: 1.5;
        }
        
        @media (max-width: 768px) {
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
            .header h1 {
                font-size: 1.8em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Advanced Signal Analysis Tool</h1>
            <p>Upload CSV file for statistical analysis, visualization & insights</p>
        </div>
        
        <div class="content">
            <div class="upload-section">
                <h3>📁 Upload Your Signal Data</h3>
                <p style="color: #666; margin-bottom: 15px;">CSV file with one number per line (time-series data)</p>
                <input type="file" id="fileInput" accept=".csv">
                <br>
                <button onclick="analyzeSignal()">🔍 Analyze & Visualize</button>
            </div>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Analyzing your signal and generating graphs...</p>
            </div>
            
            <div class="error" id="error"></div>
            
            <div class="results" id="results">
                <div class="stats-grid" id="stats"></div>
                
                <div class="plot-container">
                    <h3>📈 Time Domain Signal</h3>
                    <img id="timePlot" src="">
                </div>
                
                <div class="plot-container">
                    <h3>📊 Statistical Distribution (Histogram)</h3>
                    <img id="histPlot" src="">
                </div>
                
                <div class="plot-container">
                    <h3>⚡ Signal Trend Analysis</h3>
                    <img id="trendPlot" src="">
                </div>
                
                <div class="insights" id="insights">
                    <h3>💡 Key Insights</h3>
                    <ul id="insightsList"></ul>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        async function analyzeSignal() {
            const file = document.getElementById('fileInput').files[0];
            if (!file) {
                alert('Please select a CSV file first');
                return;
            }
            
            document.getElementById('loading').style.display = 'block';
            document.getElementById('results').style.display = 'none';
            document.getElementById('error').style.display = 'none';
            
            try {
                const text = await file.text();
                const lines = text.split('\\n');
                const numbers = [];
                
                for (let i = 0; i < lines.length; i++) {
                    const num = parseFloat(lines[i].trim());
                    if (!isNaN(num)) {
                        numbers.push(num);
                    }
                }
                
                if (numbers.length < 3) {
                    showError('Need at least 3 data points. Found: ' + numbers.length);
                    return;
                }
                
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({signal: numbers})
                });
                
                const result = await response.json();
                
                if (result.error) {
                    showError(result.error);
                } else {
                    displayResults(result);
                }
            } catch (err) {
                showError('Error: ' + err.message);
            }
            
            document.getElementById('loading').style.display = 'none';
        }
        
        function displayResults(data) {
            // Display statistics
            const statsHtml = `
                <div class="stat-card"><h3>📊 Samples</h3><div class="value">${data.length}</div></div>
                <div class="stat-card"><h3>📈 Mean</h3><div class="value">${data.stats.mean.toFixed(4)}</div></div>
                <div class="stat-card"><h3>📉 Std Dev</h3><div class="value">${data.stats.std.toFixed(4)}</div></div>
                <div class="stat-card"><h3>🔽 Minimum</h3><div class="value">${data.stats.min.toFixed(4)}</div></div>
                <div class="stat-card"><h3>🔼 Maximum</h3><div class="value">${data.stats.max.toFixed(4)}</div></div>
                <div class="stat-card"><h3>🎯 Range</h3><div class="value">${data.stats.range.toFixed(4)}</div></div>
                <div class="stat-card"><h3>📐 Median</h3><div class="value">${data.stats.median.toFixed(4)}</div></div>
                <div class="stat-card"><h3>📊 Skewness</h3><div class="value">${data.stats.skewness.toFixed(4)}</div></div>
            `;
            document.getElementById('stats').innerHTML = statsHtml;
            
            // Display plots
            document.getElementById('timePlot').src = 'data:image/png;base64,' + data.plots.time;
            document.getElementById('histPlot').src = 'data:image/png;base64,' + data.plots.histogram;
            document.getElementById('trendPlot').src = 'data:image/png;base64,' + data.plots.trend;
            
            // Display insights
            let insightsHtml = '';
            data.insights.forEach(insight => {
                insightsHtml += `<li>${insight}</li>`;
            });
            document.getElementById('insightsList').innerHTML = insightsHtml;
            
            document.getElementById('results').style.display = 'block';
        }
        
        function showError(msg) {
            const errorDiv = document.getElementById('error');
            errorDiv.innerHTML = '❌ ' + msg;
            errorDiv.style.display = 'block';
            setTimeout(() => {
                errorDiv.style.display = 'none';
            }, 5000);
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return HTML_TEMPLATE

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        signal = data.get('signal', [])
        
        if not signal or len(signal) == 0:
            return jsonify({'error': 'No signal data provided'}), 400
        
        # Calculate statistics
        n = len(signal)
        total = sum(signal)
        mean = total / n
        
        # Variance and standard deviation
        variance = sum((x - mean) ** 2 for x in signal) / n
        std = math.sqrt(variance)
        
        # Median
        sorted_signal = sorted(signal)
        if n % 2 == 0:
            median = (sorted_signal[n//2 - 1] + sorted_signal[n//2]) / 2
        else:
            median = sorted_signal[n//2]
        
        # Skewness (simplified)
        skewness = sum((x - mean) ** 3 for x in signal) / (n * (std ** 3)) if std > 0 else 0
        
        stats_data = {
            'mean': mean,
            'std': std,
            'min': min(signal),
            'max': max(signal),
            'range': max(signal) - min(signal),
            'median': median,
            'skewness': skewness
        }
        
        # Generate insights
        insights = generate_insights(signal, stats_data)
        
        # Generate plots
        plots = generate_plots(signal)
        
        return jsonify({
            'length': n,
            'stats': stats_data,
            'insights': insights,
            'plots': plots
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_insights(signal, stats):
    """Generate insights about the signal"""
    insights = []
    
    # Trend analysis
    first_third = signal[:len(signal)//3]
    last_third = signal[2*len(signal)//3:]
    
    if sum(last_third) / len(last_third) > sum(first_third) / len(first_third):
        insights.append("📈 Signal shows an UPWARD trend over time")
    else:
        insights.append("📉 Signal shows a DOWNWARD trend over time")
    
    # Volatility
    if stats['std'] / stats['mean'] > 0.5:
        insights.append("⚠️ Signal has HIGH volatility (values vary significantly)")
    else:
        insights.append("✅ Signal has LOW volatility (relatively stable)")
    
    # Skewness interpretation
    if stats['skewness'] > 0.5:
        insights.append("📊 Distribution is RIGHT-skewed (more small values)")
    elif stats['skewness'] < -0.5:
        insights.append("📊 Distribution is LEFT-skewed (more large values)")
    else:
        insights.append("📊 Distribution is approximately SYMMETRIC")
    
    # Range interpretation
    if stats['range'] / stats['mean'] > 2:
        insights.append("🎯 Signal has WIDE range - values spread across large scale")
    else:
        insights.append("🎯 Signal has NARROW range - values clustered together")
    
    # Data quality
    if len(signal) > 50:
        insights.append(f"📈 Good data size: {len(signal)} samples for reliable analysis")
    else:
        insights.append(f"⚠️ Consider more data points for better analysis (current: {len(signal)})")
    
    # Peak detection (simple)
    peaks = 0
    for i in range(1, len(signal)-1):
        if signal[i] > signal[i-1] and signal[i] > signal[i+1]:
            peaks += 1
    insights.append(f"⛰️ Found {peaks} peaks in the signal")
    
    return insights

def generate_plots(signal):
    """Generate matplotlib plots and return as base64"""
    plots = {}
    
    # Convert to numpy array for better handling
    signal_array = np.array(signal)
    n = len(signal)
    x = np.arange(n)
    
    # Plot 1: Time Domain Signal
    plt.figure(figsize=(14, 5))
    plt.plot(x, signal_array, 'b-', linewidth=1.5, label='Signal')
    plt.fill_between(x, signal_array, alpha=0.3)
    plt.xlabel('Sample Number', fontsize=12)
    plt.ylabel('Amplitude', fontsize=12)
    plt.title('Time Domain Signal', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    plots['time'] = base64.b64encode(buf.getvalue()).decode()
    plt.close()
    
    # Plot 2: Histogram (Distribution)
    plt.figure(figsize=(14, 5))
    plt.hist(signal_array, bins=20, color='skyblue', edgecolor='black', alpha=0.7)
    plt.xlabel('Value', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.title('Statistical Distribution (Histogram)', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    plots['histogram'] = base64.b64encode(buf.getvalue()).decode()
    plt.close()
    
    # Plot 3: Trend Analysis (with moving average)
    window = max(3, n // 20)  # Adaptive window size
    if window > 1:
        moving_avg = np.convolve(signal_array, np.ones(window)/window, mode='valid')
        ma_x = x[window-1:]
        
        plt.figure(figsize=(14, 5))
        plt.plot(x, signal_array, 'b-', linewidth=1, alpha=0.5, label='Original Signal')
        plt.plot(ma_x, moving_avg, 'r-', linewidth=2, label=f'Moving Average (window={window})')
        plt.xlabel('Sample Number', fontsize=12)
        plt.ylabel('Amplitude', fontsize=12)
        plt.title('Trend Analysis with Moving Average', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
    else:
        # Fallback if window too small
        plt.figure(figsize=(14, 5))
        plt.plot(x, signal_array, 'b-', linewidth=1.5, label='Signal')
        plt.xlabel('Sample Number', fontsize=12)
        plt.ylabel('Amplitude', fontsize=12)
        plt.title('Signal Trend', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
    
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    plots['trend'] = base64.b64encode(buf.getvalue()).decode()
    plt.close()
    
    return plots

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
