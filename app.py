from flask import Flask, request, jsonify, render_template_string
import os
import math
import base64
from io import BytesIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats as scipy_stats

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Signal Analysis & Prediction Tool</title>
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
            transition: transform 0.2s;
            margin: 5px;
        }
        
        .upload-section button:hover {
            transform: translateY(-2px);
        }
        
        .prediction-controls {
            margin-top: 20px;
            padding: 15px;
            background: #e8f0fe;
            border-radius: 10px;
        }
        
        .prediction-controls label {
            margin: 0 10px;
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
        }
        
        .results {
            display: none;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 15px;
            text-align: center;
        }
        
        .stat-card h3 {
            font-size: 0.85em;
            opacity: 0.9;
            margin-bottom: 8px;
        }
        
        .stat-card .value {
            font-size: 1.5em;
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
        }
        
        .plot-container img {
            width: 100%;
            border-radius: 10px;
        }
        
        .predictions-box {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
        }
        
        .prediction-values {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 15px;
        }
        
        .prediction-card {
            background: rgba(255,255,255,0.2);
            padding: 10px;
            border-radius: 8px;
            text-align: center;
            min-width: 70px;
        }
        
        .prediction-card small {
            font-size: 0.7em;
            opacity: 0.8;
        }
        
        .prediction-card strong {
            font-size: 1.1em;
        }
        
        .insights {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
        }
        
        .insights ul {
            margin-left: 20px;
            margin-top: 10px;
        }
        
        .insights li {
            margin: 8px 0;
        }
        
        @media (max-width: 768px) {
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔮 Signal Analysis & Prediction Tool</h1>
            <p>Upload CSV file for analysis, visualization & future predictions</p>
        </div>
        
        <div class="content">
            <div class="upload-section">
                <h3>📁 Upload Signal Data</h3>
                <p style="color: #666;">CSV file with one number per line</p>
                <input type="file" id="fileInput" accept=".csv">
                <br>
                <div class="prediction-controls">
                    <label>🔮 Prediction Steps:</label>
                    <select id="predictionSteps">
                        <option value="5">5 steps ahead</option>
                        <option value="10" selected>10 steps ahead</option>
                        <option value="15">15 steps ahead</option>
                        <option value="20">20 steps ahead</option>
                    </select>
                    <label>📊 Model:</label>
                    <select id="modelType">
                        <option value="linear">Linear Regression</option>
                        <option value="polynomial">Polynomial (2nd degree)</option>
                        <option value="exponential">Exponential Smoothing</option>
                    </select>
                </div>
                <button onclick="analyzeSignal()">🔍 Analyze & Predict</button>
            </div>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Analyzing signal and generating predictions...</p>
            </div>
            
            <div class="error" id="error"></div>
            
            <div class="results" id="results">
                <div class="stats-grid" id="stats"></div>
                
                <div class="plot-container">
                    <h3>📈 Signal with Future Predictions</h3>
                    <img id="predictionPlot" src="">
                </div>
                
                <div class="predictions-box">
                    <h3>🔮 Future Predictions</h3>
                    <div id="predictionValues" class="prediction-values"></div>
                    <div id="predictionStats" style="margin-top: 15px; font-size: 0.9em;"></div>
                </div>
                
                <div class="plot-container">
                    <h3>📊 Signal Distribution & Trend</h3>
                    <img id="trendPlot" src="">
                </div>
                
                <div class="insights" id="insights">
                    <h3>💡 Analysis & Prediction Insights</h3>
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
            
            const predictionSteps = parseInt(document.getElementById('predictionSteps').value);
            const modelType = document.getElementById('modelType').value;
            
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
                
                if (numbers.length < 5) {
                    showError('Need at least 5 data points. Found: ' + numbers.length);
                    return;
                }
                
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        signal: numbers,
                        prediction_steps: predictionSteps,
                        model_type: modelType
                    })
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
                <div class="stat-card"><h3>🔽 Min</h3><div class="value">${data.stats.min.toFixed(4)}</div></div>
                <div class="stat-card"><h3>🔼 Max</h3><div class="value">${data.stats.max.toFixed(4)}</div></div>
                <div class="stat-card"><h3>🎯 Range</h3><div class="value">${data.stats.range.toFixed(4)}</div></div>
                <div class="stat-card"><h3>📐 Median</h3><div class="value">${data.stats.median.toFixed(4)}</div></div>
                <div class="stat-card"><h3>📊 Trend</h3><div class="value">${data.trend_direction}</div></div>
            `;
            document.getElementById('stats').innerHTML = statsHtml;
            
            // Display predictions
            let predHtml = '';
            data.predictions.forEach((pred, i) => {
                predHtml += `
                    <div class="prediction-card">
                        <small>Step ${i+1}</small><br>
                        <strong>${pred.toFixed(4)}</strong>
                    </div>
                `;
            });
            document.getElementById('predictionValues').innerHTML = predHtml;
            
            const predStatsHtml = `
                📊 Predicted Range: ${data.prediction_stats.min_pred.toFixed(4)} - ${data.prediction_stats.max_pred.toFixed(4)} |
                📈 Average Prediction: ${data.prediction_stats.avg_pred.toFixed(4)} |
                📉 Expected Change: ${data.prediction_stats.change_percent > 0 ? '+' : ''}${data.prediction_stats.change_percent.toFixed(2)}%
            `;
            document.getElementById('predictionStats').innerHTML = predStatsHtml;
            
            // Display plots
            document.getElementById('predictionPlot').src = 'data:image/png;base64,' + data.plots.prediction;
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
        prediction_steps = data.get('prediction_steps', 10)
        model_type = data.get('model_type', 'linear')
        
        if not signal or len(signal) == 0:
            return jsonify({'error': 'No signal data provided'}), 400
        
        # Calculate statistics
        n = len(signal)
        mean = sum(signal) / n
        variance = sum((x - mean) ** 2 for x in signal) / n
        std = math.sqrt(variance)
        
        sorted_signal = sorted(signal)
        if n % 2 == 0:
            median = (sorted_signal[n//2 - 1] + sorted_signal[n//2]) / 2
        else:
            median = sorted_signal[n//2]
        
        stats_data = {
            'mean': mean,
            'std': std,
            'min': min(signal),
            'max': max(signal),
            'range': max(signal) - min(signal),
            'median': median
        }
        
        # Generate predictions
        predictions, model_used = generate_predictions(signal, prediction_steps, model_type)
        
        # Calculate prediction statistics
        pred_stats = {
            'min_pred': min(predictions),
            'max_pred': max(predictions),
            'avg_pred': sum(predictions) / len(predictions),
            'change_percent': ((predictions[-1] - signal[-1]) / signal[-1]) * 100 if signal[-1] != 0 else 0
        }
        
        # Determine trend direction
        first_third = sum(signal[:n//3]) / (n//3)
        last_third = sum(signal[2*n//3:]) / (n - 2*n//3)
        trend_direction = "UP 📈" if last_third > first_third else "DOWN 📉"
        
        # Generate insights
        insights = generate_insights(signal, predictions, stats_data, pred_stats, trend_direction, model_used)
        
        # Generate plots
        plots = generate_plots(signal, predictions, prediction_steps)
        
        return jsonify({
            'length': n,
            'stats': stats_data,
            'trend_direction': trend_direction,
            'predictions': predictions,
            'prediction_stats': pred_stats,
            'insights': insights,
            'plots': plots
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_predictions(signal, steps, model_type):
    """Generate future predictions using different models"""
    n = len(signal)
    x = np.arange(n)
    y = np.array(signal)
    
    if model_type == 'linear':
        # Linear Regression
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        future_x = np.arange(n, n + steps)
        predictions = p(future_x)
        model_used = "Linear Regression"
        
    elif model_type == 'polynomial':
        # Polynomial Regression (2nd degree)
        z = np.polyfit(x, y, 2)
        p = np.poly1d(z)
        future_x = np.arange(n, n + steps)
        predictions = p(future_x)
        model_used = "Polynomial (2nd degree)"
        
    else:  # exponential smoothing
        # Simple Exponential Smoothing
        alpha = 0.3
        smoothed = [y[0]]
        for i in range(1, n):
            smoothed.append(alpha * y[i] + (1 - alpha) * smoothed[-1])
        
        last_value = smoothed[-1]
        trend = (smoothed[-1] - smoothed[-2]) if len(smoothed) > 1 else 0
        predictions = [last_value + trend * (i + 1) for i in range(steps)]
        model_used = "Exponential Smoothing"
    
    # Ensure predictions are reasonable (not too extreme)
    predictions = np.clip(predictions, min(y) - 2 * np.std(y), max(y) + 2 * np.std(y))
    
    return predictions.tolist(), model_used

def generate_insights(signal, predictions, stats, pred_stats, trend, model):
    """Generate detailed insights"""
    insights = []
    
    # Trend insight
    insights.append(f"📈 Overall trend is {trend} based on historical data")
    
    # Prediction insight
    insights.append(f"🔮 Using {model}, next {len(predictions)} steps predicted")
    
    # Change prediction
    if pred_stats['change_percent'] > 5:
        insights.append(f"⚠️ Predicted significant increase of {pred_stats['change_percent']:.1f}%")
    elif pred_stats['change_percent'] < -5:
        insights.append(f"⚠️ Predicted significant decrease of {abs(pred_stats['change_percent']):.1f}%")
    else:
        insights.append(f"✅ Predicted relatively stable trend ({pred_stats['change_percent']:.1f}% change)")
    
    # Volatility insight
    if stats['std'] / stats['mean'] > 0.5:
        insights.append("⚠️ High volatility detected - predictions have higher uncertainty")
    else:
        insights.append("✅ Low volatility - predictions are more reliable")
    
    # Range insight
    pred_range = pred_stats['max_pred'] - pred_stats['min_pred']
    if pred_range > stats['range'] * 0.5:
        insights.append(f"📊 Predictions span wide range ({pred_range:.2f})")
    else:
        insights.append(f"📊 Predictions remain in narrow range ({pred_range:.2f})")
    
    # Confidence note
    if len(signal) < 20:
        insights.append("ℹ️ Limited data points - predictions may have higher uncertainty")
    else:
        insights.append(f"✅ Based on {len(signal)} data points - reasonable prediction confidence")
    
    # Final value prediction
    insights.append(f"🎯 Final predicted value: {predictions[-1]:.4f}")
    
    return insights

def generate_plots(signal, predictions, steps):
    """Generate matplotlib plots"""
    plots = {}
    
    n = len(signal)
    x_hist = np.arange(n)
    x_pred = np.arange(n, n + steps)
    
    # Convert to numpy arrays
    signal_array = np.array(signal)
    predictions_array = np.array(predictions)
    
    # Plot 1: Signal with Predictions
    plt.figure(figsize=(14, 6))
    plt.plot(x_hist, signal_array, 'b-', linewidth=1.5, label='Historical Signal', alpha=0.8)
    plt.plot(x_pred, predictions_array, 'r--', linewidth=2, label='Predictions', marker='o', markersize=4)
    plt.fill_between(x_pred, predictions_array - np.std(signal_array), 
                     predictions_array + np.std(signal_array), alpha=0.2, color='red', label='Confidence Band')
    plt.xlabel('Sample Number', fontsize=12)
    plt.ylabel('Amplitude', fontsize=12)
    plt.title(f'Signal Analysis with {steps}-Step Ahead Predictions', fontsize=14, fontweight='bold')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    plots['prediction'] = base64.b64encode(buf.getvalue()).decode()
    plt.close()
    
    # Plot 2: Trend Analysis with Moving Average
    window = max(3, n // 15)
    if window > 1:
        moving_avg = np.convolve(signal_array, np.ones(window)/window, mode='valid')
        ma_x = x_hist[window-1:]
        
        plt.figure(figsize=(14, 5))
        plt.plot(x_hist, signal_array, 'b-', linewidth=1, alpha=0.4, label='Original')
        plt.plot(ma_x, moving_avg, 'g-', linewidth=2, label=f'Moving Average (window={window})')
        plt.axhline(y=np.mean(signal_array), color='r', linestyle='--', alpha=0.5, label=f'Mean: {np.mean(signal_array):.3f}')
        plt.xlabel('Sample Number', fontsize=12)
        plt.ylabel('Amplitude', fontsize=12)
        plt.title('Trend Analysis with Moving Average', fontsize=14, fontweight='bold')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
    else:
        # Fallback
        plt.figure(figsize=(14, 5))
        plt.plot(x_hist, signal_array, 'b-', linewidth=1.5, label='Signal')
        plt.axhline(y=np.mean(signal_array), color='r', linestyle='--', alpha=0.5, label=f'Mean: {np.mean(signal_array):.3f}')
        plt.xlabel('Sample Number', fontsize=12)
        plt.ylabel('Amplitude', fontsize=12)
        plt.title('Signal Trend Analysis', fontsize=14, fontweight='bold')
        plt.legend()
        plt.grid(True, alpha=0.3)
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
