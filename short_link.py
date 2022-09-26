from flask import Flask, request, abort, send_file, redirect
import mysql.connector
from flask_cors import CORS
from queries import get_affiliate_link_by_id, get_link_by_short_slug, add_short_link_visit
from datetime import datetime
import os
app = Flask(__name__)
CORS(app)

db = mysql.connector.connect(
    host=os.getenv('MYSQL_HOST'),
    user=os.getenv('MYSQL_USER'),
    passwd=os.getenv('MYSQL_PASS'),
    database=os.getenv('MYSQL_DB')
)

@app.get('/short')
def redirect_to_dramafy():
    return redirect('https://dramafy.com', code=302)

@app.get('/<short_key>')
@app.get('/<short_key>/<affiliate_id>')
def get_short_page(short_key, affiliate_id=None):
    
    db.ping(reconnect=True)
    cursor = db.cursor(prepared=True)
    cursor.execute('''SELECT old_long_slug AS url,
    id AS link_id
    FROM shortened_link
    WHERE short_slug = %s;
    ''', (short_key,))
    
    cursor_result = cursor.fetchall()
    redirect_url = cursor_result[0][0]
    res_array = [cursor_result[0][1]]

    af_id = affiliate_id if affiliate_id is not None else None
    res_array.append(af_id)

    url = request.values.get("url")
    referrer = request.headers.get('Referer')
    if referrer is not None:
        res_array.append(referrer)
    elif url is not None:
        res_array.append(url)
    else:
        res_array.append(None)

    res_array.append(datetime.utcnow())

    cursor.execute(add_short_link_visit, tuple(res_array))

    db.commit()
    db.close()

    return redirect(redirect_url, code=302)
