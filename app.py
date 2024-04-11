from flask import Flask, render_template, request, redirect, url_for
import os
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)

# Function to generate plot
def generate_plot(df, graph_type):
    plt.figure(figsize=(10, 6))
    if graph_type == 'line':
        df.plot(kind='line')
    elif graph_type == 'bar':
        df.plot(kind='bar')
    elif graph_type == 'scatter':
        df.plot(kind='scatter', x='x', y='y')
    plt.xlabel('X Axis')
    plt.ylabel('Y Axis')
    plt.title('Plot')
    plt.grid(True)
    plt.tight_layout()
    # Save plot to bytes buffer
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    # Encode plot to base64 string
    plot_data = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    return plot_data

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if a file is uploaded
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        # Check if file is selected
        if file.filename == '':
            return redirect(request.url)
        # Check if file is CSV
        if not file.filename.endswith('.csv'):
            return render_template('index.html', error='Please upload a CSV file.')
        # Read CSV file
        df = pd.read_csv(file)
        # Get graph type
        graph_type = request.form.get('graph_type')
        # Generate plot
        plot_data = generate_plot(df, graph_type)
        return render_template('index.html', plot_data=plot_data)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

