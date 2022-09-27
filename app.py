from flask import Flask, request, abort, send_file, redirect
import mysql.connector
from flask_cors import CORS
from queries import get_affiliate_link_by_id, get_link_by_short_slug, add_short_link_visit
from datetime import datetime
import os
from threading import Thread
import ipinfo
import logging
app = Flask(__name__)
CORS(app)

db_config = {
        'host': os.getenv('MYSQL_HOST'),
        'user': os.getenv('MYSQL_USER'),
        'passwd': os.getenv('MYSQL_PASS'),
        'database': os.getenv('MYSQL_DB')
        }

handler = ipinfo.getHandler(access_token='ef2cfa1114110a')

def process_data(affiliate_id, link_id, url, referrer, ip):
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor(prepared=True)
    res_array = [link_id]
    name_arr = ['link_id']
    
    af_id = affiliate_id if affiliate_id is not None else None
    res_array.append(af_id)
    name_arr.append('affiliate_id')

    if referrer is not None:
        res_array.append(referrer)
    elif url is not None:
        res_array.append(url)
    else:
        res_array.append(None)
    name_arr.append('referrer')

    res_array.append(datetime.utcnow())
    name_arr.append('datetime')
    if ip is not None:
        res_array.append(ip)
        name_arr.append('ip_address')
    loc_details = ['city', 'region', 'country', 'timezone', 'loc', 'postal']
    details = handler.getDetails(ip)
    for ld in loc_details:
        try:
            det = details.__getattr__(ld)
            if det is not None:
                res_array.append(det)
                name_arr.append(ld)
        except AttributeError as e:
            logging.info('ip didn\'t return a {}'.format(ld))

    name_str = add_short_link_visit.format(', '.join(name_arr), ', '.join(['%s' for n in name_arr]))
    cursor.execute(name_str, tuple(res_array))

    db.commit()
    db.close()

@app.route('/short', methods=['GET'])
def redirect_to_dramafy():
    return redirect('https://dramafy.com', code=302)

@app.route('/<short_key>', methods=['GET'])
@app.route('/<short_key>/<affiliate_id>', methods=['GET'])
def get_short_page(short_key, affiliate_id=None):
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor(prepared=True)
    print(short_key)
    cursor.execute('''SELECT old_long_slug AS url,
    id AS link_id
    FROM shortened_link
    WHERE short_slug = %s;
    ''', (short_key,))

    ip = ''
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        ip = request.environ['REMOTE_ADDR']
    else:
        ip = request.environ['HTTP_X_FORWARDED_FOR']

    url = request.values.get("url")
    referrer = request.headers.get('Referer')
    
    cursor_result = cursor.fetchall()
    redirect_url = cursor_result[0][0]
    db.close()

    Thread(target=process_data(affiliate_id=affiliate_id, link_id=cursor_result[0][1], referrer=referrer, url=url, ip=ip)).start()
    return redirect(redirect_url, code=302)

if __name__ == '__main__':
    app.run()