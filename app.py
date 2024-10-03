from flask import Flask, render_template, request, redirect, url_for, session, send_file
import boto3
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Initialize DynamoDB client
dynamodb = boto3.client()

# DynamoDB table name
TABLE_NAME = 'Users'

# Function to register a new user
def register_user(username, password):
    # Hash the password
    password_hash = generate_password_hash(password)
    # Add the user to DynamoDB table
    response = dynamodb.put_item(
        TableName=TABLE_NAME,
        Item={
            'users': {'S': username},
            'Username': {'S': username},
            'PasswordHash': {'S': password_hash}
        }
    )
    return response

# Function to authenticate a user during login
def authenticate_user(username, password):
    # Get the user from DynamoDB
    response = dynamodb.get_item(
        TableName=TABLE_NAME,
        Key={
            'users': {'S': username}
        }
    )
    if 'Item' in response:
        stored_password_hash = response['Item']['PasswordHash']['S']
        # Check if the provided password matches the stored hash
        if check_password_hash(stored_password_hash, password):
            return True
    return False

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if authenticate_user(username, password):
            session['username'] = username
            print("User logged in. Session:", session)
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        register_user(username, password)
        return render_template('register.html', message='Registration successful. Please login.')
    return render_template('register.html')

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

@app.route('/download_plot')
def download_plot():
    # Get plot data from query parameters
    plot_data = request.args.get('plot_data')
    # Decode plot data from base64
    plot_bytes = base64.b64decode(plot_data)
    # Create a BytesIO buffer
    buffer = BytesIO(plot_bytes)
    # Return the plot as a file attachment
    return send_file(buffer, as_attachment=True, mimetype='image/png', download_name='plot.png')

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
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
        return render_template('index.html', plot_data=plot_data)  # Replace plot_data with your actual data
    else:
        return render_template('index.html')
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

