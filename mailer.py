import smtplib
import json
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import requests
import time
import sys
import getopt
from datetime import datetime
#12myE1PKaSH8ovXKGqR6c64rxrSq415DBg cold wallet
wallet = '3LKm65Yw4QwmnM2TSf8Yny7pE2HJEefwjt'
interval = 2 * 60
btc_delta = 250
xrp_delta = 0.1

def sender(subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = "noreply@proil.moscow"
        msg['To'] = 'ericovva@yandex.ru'
        msg['Subject'] = "Python email"
        server = smtplib.SMTP_SSL('smtp.yandex.ru:465')
        server.login("noreply@proil.moscow", "")
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        text = msg.as_string()
        server.sendmail('noreply@proil.moscow', 'ericovva@yandex.ru', text)
        server.close()
    except Exception as e:
        print >>sys.stderr, 'SENDMAIL ERROR {}'.format(e.message)

#main
try:
    opts, args = getopt.getopt(sys.argv[1:], 't', ['time='])
    for opt, arg in opts:
        if opt in ('-t', '--time'):
            interval = int(arg)
except getopt.GetoptError:
    print('--time, -t  default 120')


btc = None
xrp = None
fail_count = 0
while True:
    print >>sys.stderr, datetime.now()
    try:
        url = 'https://api.nicehash.com/api?method=stats.provider.workers&addr={}'.format(wallet)
        r = requests.get(url)
        print >>sys.stderr, 'NH request status {}'.format(str(r.status_code))
        data = json.loads(r.content)
        workers = data.get('result').get('workers')

        if int(r.status_code) != 200:
            raise ValueError('Status code {}'.format(r.status_code))

        if not len(workers): #or not (float(workers[0][1]['a']) > 0):
            fail_count+=1
            print >>sys.stderr, 'Miner was stopped {}!'.format(fail_count)
        else:
            fail_count = 0

        if fail_count > 2:
            print >>sys.stderr, 'Miner was stoped!'
            sender('Miner stopped', 'Miner was stopped, please check')
            fail_count = 0

    except Exception as e:
        print >>sys.stderr, 'Get request to NH fail!'
        if e.message != 'No JSON object could be decoded':
            sender('Script fail', e.message)
        print >>sys.stderr, e

    try:
        url = 'https://api.exmo.com/v1/ticker/'
        r = requests.get(url)
        print >>sys.stderr, 'Exmo request status {}'.format(str(r.status_code))
        data = json.loads(r.content)
        btc_usd = float(data.get('BTC_USD').get('buy_price'))
        xrp_usd = float(data.get('XRP_USD').get('buy_price'))

        if int(r.status_code) != 200:
            raise ValueError('Status code {}'.format(r.status_code))

        if btc and (btc_usd > btc + btc_delta or btc_usd < btc - btc_delta):
            mes = 'Change {}$.\nNew price {}$. Old price {}$'.format(str(btc_usd - btc), str(btc_usd), str(btc))
            print >>sys.stderr, mes
            sender('BTC CHANGED', mes)
            btc = btc_usd

        if xrp and (xrp_usd > xrp + xrp_delta or xrp_usd < xrp - xrp_delta):
            mes = 'Change {}$.\nNew price {}$. Old price {}$.'.format(str(xrp_usd - xrp), str(xrp_usd), str(xrp))
            print >>sys.stderr, mes
            sender('XRP CHANGED', mes)
            xrp = xrp_usd

        if not btc:
            btc = btc_usd
        if not xrp:
            xrp = xrp_usd

        print >>sys.stderr, 'O: {} {} \nN: {} {}'.format(str(btc), str(xrp), str(btc_usd), str(xrp_usd))


    except Exception as e:
        print >>sys.stderr, 'Get request to EXMO fail!'
        print >>sys.stderr, e
            
    time.sleep(interval)
