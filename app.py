from flask import Flask, request, jsonify, render_template_string
import os
import math

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Signal Analysis Tool</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        h1 {
            color: #667eea;
            text-align: center;
        }
        .upload-area {
            text-align: center;
            padding: 20px;
            border: 2px dashed #667eea;
            border-radius: 10px;
            margin: 20px 0;
        }
        input, button {
            padding: 10px 20px;
            margin: 10px;
            font-size: 16px;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
        }
        button:hover {
            transform: translateY(-2px);
        }
        .result {
            margin-top: 20px;
            padding: 20px;
            background: #f7f9fc;
            border-radius: 10px;
            display: none;
        }
        .stat {
            display: inline-block;
            width: 45%;
            margin: 5px;
            padding: 10px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        .error {
            background: #fee;
            color: #c33;
            padding: 10px;
            border-radius: 8px;
            display: none;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Signal Analysis Tool</h1>
        <p style="text-align: center">Upload a CSV file with numerical data (one value per line)</p>
        
        <div class="upload-area">
            <input type="file" id="fileInput" accept=".csv">
            <br>
            <button onclick="analyzeSignal()">🔍 Analyze Signal</button>
        </div>
        
        <div class="loading" id="loading">
            <div>⏳ Processing your signal...</div>
        </div>
        
        <div class="error" id="error"></div>
        
        <div class="result" id="result">
            <h3>📈 Analysis Results:</h3>
            <div id="stats"></div>
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
            document.getElementById('result').style.display = 'none';
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
            const statsHtml = `
                <div class="stat">📊 <strong>Samples:</strong> ${data.length}</div>
                <div class="stat">📈 <strong>Mean:</strong> ${data.mean.toFixed(4)}</div>
                <div class="stat">📉 <strong>Std Dev:</strong> ${data.std.toFixed(4)}</div>
                <div class="stat">🔽 <strong>Minimum:</strong> ${data.min.toFixed(4)}</div>
                <div class="stat">🔼 <strong>Maximum:</strong> ${data.max.toFixed(4)}</div>
                <div class="stat">🎯 <strong>Range:</strong> ${data.range.toFixed(4)}</div>
                <div class="stat">📐 <strong>Median:</strong> ${data.median.toFixed(4)}</div>
                <div class="stat">📊 <strong>Sum:</strong> ${data.sum.toFixed(4)}</div>
            `;
            
            document.getElementById('stats').innerHTML = statsHtml;
            document.getElementById('result').style.display = 'block';
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
        
        # Calculate statistics without numpy
        n = len(signal)
        total = sum(signal)
        mean = total / n
        
        # Standard deviation
        variance = sum((x - mean) ** 2 for x in signal) / n
        std = math.sqrt(variance)
        
        # Median
        sorted_signal = sorted(signal)
        if n % 2 == 0:
            median = (sorted_signal[n//2 - 1] + sorted_signal[n//2]) / 2
        else:
            median = sorted_signal[n//2]
        
        result = {
            'length': n,
            'mean': mean,
            'std': std,
            'min': min(signal),
            'max': max(signal),
            'range': max(signal) - min(signal),
            'median': median,
            'sum': total
        }
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
