from flask import Flask, render_template, request, jsonify
import numpy as np
from scipy.signal import butter, filtfilt
import base64
from io import BytesIO
import matplotlib.pyplot as plt

app = Flask(__name__)

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Signal Analysis Tool</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    </head>
    <body>
        <h1>📊 Signal Analysis & Prediction</h1>
        <input type="file" id="fileInput" accept=".csv">
        <button onclick="analyzeSignal()">Analyze</button>
        <div id="plot"></div>
        
        <script>
            async function analyzeSignal() {
                const file = document.getElementById('fileInput').files[0];
                const text = await file.text();
                const data = text.split('\\n').map(Number).filter(x => !isNaN(x));
                
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({signal_data: data})
                });
                const result = await response.json();
                
                const trace1 = {x: [...Array(data.length).keys()], y: data, name: 'Original'};
                const trace2 = {x: [...Array(result.filtered_signal.length).keys()], y: result.filtered_signal, name: 'Filtered'};
                Plotly.newPlot('plot', [trace1, trace2]);
            }
        </script>
    </body>
    </html>
    '''

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json['signal_data']
    signal = np.array(data)
    
    # Low-pass filter
    b, a = butter(4, 0.3, btype='low')
    filtered = filtfilt(b, a, signal)
    
    return jsonify({
        'filtered_signal': filtered.tolist()
    })

if __name__ == '__main__':
    app.run(debug=True)