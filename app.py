from flask import Flask, request, render_template, send_file
import pandas as pd

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    # Ensure a file and update type are provided
    if 'file' not in request.files or not request.form.get('update_type'):
        return "Please upload a file and choose an update type."

    # Get the uploaded file
    uploaded_file = request.files['file']
    update_type = request.form.get('update_type')
    find_text = request.form.get('find')
    replace_text = request.form.get('replace')
    change_note = request.form.get('change_note') == 'yes'
    note_replacement = request.form.get('note_replacement')
    extended_properties = request.form.getlist('extended_properties')

    if uploaded_file.filename != '':
        # Load the CSV file into a pandas DataFrame
        data = pd.read_csv(uploaded_file)

        # Handle different update types
        if update_type in ['titles', 'titles_descriptions', 'all']:
            # Update Titles
            if 'Item_Title' in data.columns:
                data['Formatted_Title'] = data['Item_Title'].str.replace(
                    find_text, replace_text, regex=False
                )

        if update_type in ['descriptions', 'titles_descriptions', 'all']:
            # Update Descriptions
            if 'Description' in data.columns and change_note:
                # Replace 'please note' or set it to blank if no replacement text is provided
                data['Formatted_Description'] = data['Description'].str.replace(
                    r'please note:.*', note_replacement if note_replacement else '', regex=True
                )

        if update_type in ['extended_properties', 'all']:
            # Update Extended Properties
            for prop in extended_properties:
                if prop in data.columns:
                    data[f'Formatted_{prop}'] = data[prop].str.replace(
                        find_text, replace_text, regex=False
                    )

        if update_type in ['prices', 'all']:
            # Update Prices (example logic: increase by 10%)
            if 'Price' in data.columns:
                data['Updated_Price'] = data['Price'] * 1.1

        # Save the processed file
        output_file = "formatted_listings.csv"
        data.to_csv(output_file, index=False)

        return send_file(output_file, as_attachment=True)

    return "No file uploaded."

if __name__ == '__main__':
    app.run(debug=True)
