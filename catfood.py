import getpass
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
import urllib.request, urllib.parse, urllib.error
import ssl
import json
import time
import re
import os
import sys

# Email setting for notification
def Email(sender, password, recipient, emailsub, emailmsg, smtpsever, smtpport):
    try:
        msg = MIMEText(emailmsg, 'plain', 'utf-8')
        msg['From'] = formataddr(['Catfood Reminder', sender]) 
        msg['To'] = formataddr([recipient, recipient])  
        msg['Subject'] = emailsub 
        server = smtplib.SMTP_SSL(smtpsever, smtpport)
        server.login(sender, password)
        server.sendmail(sender,[recipient,],msg.as_string()) 
        server.quit()
        print('Succeed to send e-mail')
        return True
    except: 
        print('Failed to send e-mail')

def MacOsNotification(ostitle, osmsg):
    if sys.platform == 'darwin':
        os.system('osascript -e \'display notification "' + osmsg + '" sound name "default" with title "' + ostitle + '"\'')  

def GetDobanTopic(keywords):
    # Load saved topic data
    try: 
        with open('record.json', 'r') as record_file:
            record = json.load(record_file)
            record_topics = record['topics']
            lasttime = record['time'] 
        record_file.close()
    except: 
        record = dict()
        record_topics = dict() 
        lasttime = "2020-01-01 00:00:00"
    # Write new topic data
    with open('record.json', 'w') as record_file:
        # Request 1000pcs of topics from Douban
        info = []
        for i in range(0, 10):
            # Ignore SSL certificate errors
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            # Request data in JSON format
            count = 100
            start = i * count
            url = 'https://api.douban.com/v2/group/656297/topics?start=' + str(start) + '&count=' + str(count)
            header = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36 Edg/79.0.309.56'} 
            req = urllib.request.Request(url = url, headers = header) 
            nowtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            try:
                data = json.loads(urllib.request.urlopen(req, context = ctx).read())
            except:
                continue
            # Filtrate concerned topics
            for number in range(0, count):
                topic = data['topics'][number]
                content = topic['title'] + topic ['content']
                if topic['updated'] <= lasttime:
                    break
                if re.search(keywords, content, re.I|re.M|re.S) != None:
                    if topic['id'] not in record_topics.keys(): 
                        info.append(topic['updated'] + '\r\n' + topic['title'] + '\r\n' + topic['share_url'] + '\r\n' + '-' * 50)
                        print(topic['updated'] + '\n' + topic['title'] + '\n' + topic['share_url'] + '\n' + '-' * 50)
                    record_topics[topic['id']] = {'updated':topic['updated'], 'title':topic['title'], 'link':topic['share_url']}
            if number < (count - 1):
                break
        record['time'] = nowtime
        record['topics'] = record_topics
        json.dump(record, record_file, ensure_ascii = False)
        if len(info) == 0:
            print('No new message   ' + nowtime)
        else:
            message = str(len(info)) + ' new message(s)  ' + nowtime
            print(message)
            MacOsNotification('Catfood Reminder', message)
            Email(SenderAddress, Password, RecipientAddress, message, "\r\n".join(info), SMTPSever, SMTPPort)
    record_file.close()
    return

#Setup e-mail
while True:
    # Login in E-mail
    SenderAddress = input('Please input the sender\'s e-mail address: ')
    Password = getpass.getpass('Please input the sender\'s e-mail password: ')
    SMTPSever = input('Please input the sender\'s e-mail SMTP Sever address: ')
    SMTPPort = input('Please input the sender\'s e-mail SMTP Port: ')
    RecipientAddress = input('Please input the recipient\'s e-mail address: ')
    #Test E-mail
    testemail =  Email(SenderAddress, Password, RecipientAddress, 'TEST MESSAGE', 'THIS IS TEST TEXT', SMTPSever, SMTPPort)
    if testemail == True:
        print('Valid e-mail setting, start searching...')
        break
    else:
        print('Invalid e-mail setting is invalid, please retry')

# Search new topic every 10 min
while True:
    GetDobanTopic(r'(开车).*?(go)')     #change into your target keywords
    print('Next search will start in 10 min')
    time.sleep(600)
