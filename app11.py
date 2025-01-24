from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <form action="/upload" method="post" enctype="multipart/form-data">
        <label for="file">Upload CSV:</label>
        <input type="file" name="file" required>
        <br><br>
        <label for="find">Find:</label>
        <input type="text" name="find" required>
        <br><br>
        <label for="replace">Replace:</label>
        <input type="text" name="replace" required>
        <br><br>
        <button type="submit">Submit</button>
    </form>
    '''

@app.route('/upload', methods=['POST'])
def upload():
    print("Request received at /upload!")
    if 'file' in request.files:
        print(f"File uploaded: {request.files['file'].filename}")
    if 'find' in request.form:
        print(f"Find: {request.form['find']}")
    if 'replace' in request.form:
        print(f"Replace: {request.form['replace']}")
    return "File and inputs received successfully!"

if __name__ == '__main__':
    app.run(debug=True)
