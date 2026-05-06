from flask import Flask, request, jsonify, render_template_string
import numpy as np
from scipy.signal import butter, filtfilt, find_peaks
from scipy.fft import fft, fftfreq
from scipy import stats
import base64
from io import BytesIO
import matplotlib
matplotlib.use('Agg')  # For server-side plotting
import matplotlib.pyplot as plt
import os
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)

# HTML Template with Graphs
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Advanced Signal Analysis Tool</title>
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
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
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
        
        .upload-section input {
            padding: 12px 24px;
            font-size: 16px;
            border: 1px solid #ddd;
            border-radius: 8px;
            margin: 10px;
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
        }
        
        .upload-section button:hover {
            transform: translateY(-2px);
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
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .stat-card h3 {
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 10px;
        }
        
        .stat-card .value {
            font-size: 2em;
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
        
        .predictions {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            margin-top: 20px;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Advanced Signal Analysis & Prediction Tool</h1>
            <p>Upload CSV file for real-time signal processing, visualization and prediction</p>
        </div>
        
        <div class="content">
            <div class="upload-section">
                <h3>📁 Upload Your Signal Data</h3>
                <p>CSV file with one number per line (time-series data)</p>
                <input type="file" id="fileInput" accept=".csv">
                <br>
                <button onclick="analyzeSignal()">🔍 Analyze & Predict</button>
            </div>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Analyzing your signal...</p>
            </div>
            
            <div class="error" id="error"></div>
            
            <div class="results" id="results">
                <div class="stats-grid" id="stats"></div>
                
                <div class="plot-container">
                    <h3>📈 Original Signal</h3>
                    <img id="originalPlot" src="">
                </div>
                
                <div class="plot-container">
                    <h3>🔍 Frequency Spectrum (FFT)</h3>
                    <img id="spectrumPlot" src="">
                </div>
                
                <div class="plot-container">
                    <h3>⚡ Filtered Signal (Noise Removed)</h3>
                    <img id="filteredPlot" src="">
                </div>
                
                <div class="predictions" id="predictions">
                    <h3>🔮 Future Predictions (Next 10 Steps)</h3>
                    <div id="predictionValues"></div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        async function analyzeSignal() {
            const file = document.getElementById('fileInput').files[0];
            if (!file) {
                showError('Please select a CSV file first');
                return;
            }
            
            document.getElementById('loading').style.display = 'block';
            document.getElementById('results').style.display = 'none';
            document.getElementById('error').style.display = 'none';
            
            const text = await file.text();
            const numbers = text.split('\\n')
                .map(x => parseFloat(x.trim()))
                .filter(x => !isNaN(x));
            
            if (numbers.length < 5) {
                showError('Need at least 5 data points');
                document.getElementById('loading').style.display = 'none';
                return;
            }
            
            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({signal: numbers})
                });
                
                const result = await response.json();
                
                if (result.error) {
                    showError(result.error);
                } else {
                    displayResults(result);
                }
            } catch (err) {
                showError('Error connecting to server: ' + err.message);
            }
            
            document.getElementById('loading').style.display = 'none';
        }
        
        function displayResults(data) {
            // Display statistics
            const statsHtml = `
                <div class="stat-card"><h3>📊 Samples</h3><div class="value">${data.length}</div></div>
                <div class="stat-card"><h3>📈 Mean</h3><div class="value">${data.stats.mean.toFixed(4)}</div></div>
                <div class="stat-card"><h3>📉 Std Dev</h3><div class="value">${data.stats.std.toFixed(4)}</div></div>
                <div class="stat-card"><h3>🎯 Min</h3><div class="value">${data.stats.min.toFixed(4)}</div></div>
                <div class="stat-card"><h3>🚀 Max</h3><div class="value">${data.stats.max.toFixed(4)}</div></div>
                <div class="stat-card"><h3>📐 Range</h3><div class="value">${data.stats.range.toFixed(4)}</div></div>
                <div class="stat-card"><h3>⚡ Skewness</h3><div class="value">${data.stats.skewness.toFixed(4)}</div></div>
                <div class="stat-card"><h3>🎵 Dominant Freq</h3><div class="value">${data.dominant_freq.toFixed(2)} Hz</div></div>
            `;
            document.getElementById('stats').innerHTML = statsHtml;
            
            // Display plots
            document.getElementById('originalPlot').src = 'data:image/png;base64,' + data.plots.original;
            document.getElementById('spectrumPlot').src = 'data:image/png;base64,' + data.plots.spectrum;
            document.getElementById('filteredPlot').src = 'data:image/png;base64,' + data.plots.filtered;
            
            // Display predictions
            let predHtml = '<div style="display: flex; gap: 10px; flex-wrap: wrap; margin-top: 15px;">';
            data.predictions.forEach((pred, i) => {
                predHtml += `<div style="background: rgba(255,255,255,0.2); padding: 10px; border-radius: 8px; text-align: center;">
                                <small>Step ${i+1}</small><br>
                                <strong>${pred.toFixed(4)}</strong>
                             </div>`;
            });
            predHtml += '</div>';
            document.getElementById('predictionValues').innerHTML = predHtml;
            
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
        signal = np.array(data.get('signal', []))
        
        if len(signal) == 0:
            return jsonify({'error': 'No signal data provided'}), 400
        
        # Statistical Features
        stats_data = {
            'mean': float(np.mean(signal)),
            'std': float(np.std(signal)),
            'min': float(np.min(signal)),
            'max': float(np.max(signal)),
            'range': float(np.max(signal) - np.min(signal)),
            'skewness': float(stats.skew(signal)),
            'kurtosis': float(stats.kurtosis(signal))
        }
        
        # Frequency Domain Analysis
        n = len(signal)
        fft_vals = fft(signal)
        freqs = fftfreq(n, 1)
        magnitude = np.abs(fft_vals)
        
        # Find dominant frequency (excluding DC)
        pos_mask = freqs > 0
        if np.any(pos_mask):
            dominant_freq = freqs[pos_mask][np.argmax(magnitude[pos_mask])]
        else:
            dominant_freq = 0
        
        # Prediction (simple AR model)
        predictions = predict_future(signal, n_steps=10)
        
        # Filtered signal (moving average)
        window = min(5, len(signal)//4)
        if window < 1:
            window = 1
        filtered = np.convolve(signal, np.ones(window)/window, mode='same')
        
        # Generate plots
        plots = generate_plots(signal, filtered, freqs, magnitude, n)
        
        return jsonify({
            'length': len(signal),
            'stats': stats_data,
            'dominant_freq': float(abs(dominant_freq)),
            'predictions': predictions,
            'plots': plots
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def predict_future(signal, n_steps=10):
    """Simple linear extrapolation for prediction"""
    if len(signal) < 3:
        return signal[-1] * np.ones(n_steps)
    
    # Use last 10 points for trend
    last_points = signal[-min(10, len(signal)):]
    x = np.arange(len(last_points))
    z = np.polyfit(x, last_points, 1)
    p = np.poly1d(z)
    
    # Predict next steps
    future_x = np.arange(len(last_points), len(last_points) + n_steps)
    predictions = p(future_x)
    
    # Add small random noise for realism
    noise = np.random.normal(0, np.std(signal) * 0.05, n_steps)
    predictions = predictions + noise
    
    return predictions.tolist()

def generate_plots(signal, filtered, freqs, magnitude, n):
    """Generate base64 encoded plots"""
    plots = {}
    
    # Plot 1: Original Signal
    plt.figure(figsize=(12, 4))
    plt.plot(signal, 'b-', linewidth=1.5, label='Original Signal')
    plt.xlabel('Sample Number')
    plt.ylabel('Amplitude')
    plt.title('Original Time Domain Signal')
    plt.grid(True, alpha=0.3)
    plt.legend()
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    plots['original'] = base64.b64encode(buf.getvalue()).decode()
    plt.close()
    
    # Plot 2: Frequency Spectrum
    plt.figure(figsize=(12, 4))
    half = n // 2
    plt.stem(freqs[:half], magnitude[:half], basefmt=" ", markerfmt=' ', linefmt='r-')
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Magnitude')
    plt.title('Frequency Spectrum (FFT)')
    plt.grid(True, alpha=0.3)
    plt.xlim(0, 0.5)
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    plots['spectrum'] = base64.b64encode(buf.getvalue()).decode()
    plt.close()
    
    # Plot 3: Filtered Signal
    plt.figure(figsize=(12, 4))
    plt.plot(signal, 'b-', alpha=0.5, linewidth=1, label='Original')
    plt.plot(filtered, 'r-', linewidth=2, label='Filtered (Noise Removed)')
    plt.xlabel('Sample Number')
    plt.ylabel('Amplitude')
    plt.title('Original vs Filtered Signal')
    plt.grid(True, alpha=0.3)
    plt.legend()
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    plots['filtered'] = base64.b64encode(buf.getvalue()).decode()
    plt.close()
    
    return plots

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
