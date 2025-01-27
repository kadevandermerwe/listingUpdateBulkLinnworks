import pandas as pd
from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

@app.route('/')

def home():
    return render_template('vehicle.html')

@app.route('/vehicle_query', methods=['GET'])

def vehicle_query():

    api_url = 'https://www.carqueryapi.com/api/0.3/'


    
    params = {
        "cmd": "getMakes"# Command to retrieve all makes
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    # Get the data from the API
    response = requests.get(api_url, params=params, headers=headers)

    print("Raw response text:", response.text)
    print("Response status code:", response.status_code)

    try:
        data = response.json()
        makes = data.get("Makes", ["make_display"])  # Extract the 'Makes' list
        df = pd.DataFrame(makes)
        df.to_csv('makes.csv', index=False)
        
        pd.read_csv('makes.csv')
        print(df['make_display'].tolist())

        for index, row in df.iterrows():
           makes = row['make_display']


        return jsonify(df.to_dict(orient='records')), response.status_code
    except requests.exceptions.JSONDecodeError:
        return jsonify({"error": "Failed to fetch data"}), response.status_code
    


if __name__ == '__main__':
    app.run(debug=True)