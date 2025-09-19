from flask import Flask, render_template, url_for, request, redirect
import csv
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from werkzeug.http import http_date

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)
print(__name__)


def _last_commit_datetime():
    """Latest git commit datetime (UTC). Fallback to server.py mtime."""
    try:
        ts = subprocess.check_output(
            ['git', 'log', '-1', '--format=%ct'],
            cwd=BASE_DIR
        ).decode().strip()
        return datetime.fromtimestamp(int(ts), tz=timezone.utc)
    except Exception:
        try:
            ts = (BASE_DIR / 'server.py').stat().st_mtime
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except Exception:
            return None

@app.context_processor
def inject_last_modified():
    dt = _last_commit_datetime()
    formatted = dt.astimezone().strftime('%b %d, %Y %I:%M %p') if dt else ''
    return {'SITE_LAST_MODIFIED': formatted}

@app.after_request
def add_last_modified_header(resp):
    dt = _last_commit_datetime()
    if dt:
        resp.headers['Last-Modified'] = http_date(dt.timestamp())
    return resp


@app.route('/')
def my_home():
    
    return render_template('index.html')

@app.route('/<string:page_name>')
def html_page(page_name):
    return render_template(page_name)


def write_to_file(data):
    with open('database.txt', mode='a') as database:
        email = data["email"]
        subject = data["subject"]
        message = data["message"]
        
        file = database.write(f'\n{email},{subject},{message}')

def write_to_csv(data):
    with open('database.csv', mode='a', newline='') as database2:
        email = data["email"]
        subject = data["subject"]
        message = data["message"]
        
        csv_writer = csv.writer(database2, delimiter=',', quotechar='"',quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow([email,subject,message])


@app.route('/submit_form', methods=['POST', 'GET'])
def submit_form():
    if request.method == 'POST':
        try:

            data = request.form.to_dict()
            write_to_csv(data)
            return redirect('/thankyou.html')
        except:
            return 'did not save to database'
    else:
        return 'something went wrong. Try again'
    

    

# @app.route('/components.html')
# def components():
#     return render_template('components.html')

 
# @app.route('/contact.html')
# def contact_jim():
#     return render_template('contact.html')

# @app.route('/works.html')
# def work():
#     return render_template('works.html')

# @app.route('/works')
# def works_jim():
#     return render_template('works.html')

