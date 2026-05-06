from flask import Flask, jsonify, request, render_template_string
import os
import numpy as np

app = Flask(__name__)

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Signal Analysis Tool</title>
    <style>
        body { font-family: Arial; margin: 40px; }
        input, button { padding: 10px; margin: 5px; }
        .result { border: 1px solid #ccc; padding: 15px; margin-top: 20px; }
    </style>
</head>
<body>
    <h1>📊 Signal Analysis Tool</h1>
    <p>Upload a CSV file with numbers (one per line)</p>
    
    <input type="file" id="fileInput" accept=".csv">
    <br><br>
    <button onclick="analyze()">Analyze Signal</button>
    
    <div id="result" class="result"></div>
    
    <script>
        async function analyze() {
            const file = document.getElementById('fileInput').files[0];
            if (!file) {
                alert('Please select a CSV file');
                return;
            }
            
            const text = await file.text();
            const numbers = text.split('\\n')
                .map(x => parseFloat(x))
                .filter(x => !isNaN(x));
            
            if (numbers.length === 0) {
                alert('No valid numbers found');
                return;
            }
            
            document.getElementById('result').innerHTML = 'Processing...';
            
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({signal: numbers})
            });
            
            const result = await response.json();
            
            document.getElementById('result').innerHTML = `
                <h3>Analysis Results:</h3>
                <p>📈 Signal Length: ${result.length} samples</p>
                <p>📊 Mean: ${result.mean.toFixed(4)}</p>
                <p>📉 Standard Deviation: ${result.std.toFixed(4)}</p>
                <p>🔽 Minimum: ${result.min.toFixed(4)}</p>
                <p>🔼 Maximum: ${result.max.toFixed(4)}</p>
                <p>🎯 Range: ${result.range.toFixed(4)}</p>
            `;
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return HTML

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        signal = data.get('signal', [])
        
        if not signal:
            return jsonify({'error': 'No signal data'}), 400
        
        arr = np.array(signal)
        
        result = {
            'length': len(signal),
            'mean': float(np.mean(arr)),
            'std': float(np.std(arr)),
            'min': float(np.min(arr)),
            'max': float(np.max(arr)),
            'range': float(np.max(arr) - np.min(arr))
        }
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return {'status': 'healthy'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
