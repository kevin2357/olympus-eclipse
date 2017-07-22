'''
Created on Jul 19, 2017

@author: ktankersley
@see https://gist.github.com/mangelajo/6fa005ff3544fecdecfa
@see https://crispgm.com/page/olympus-wifi-api.html for link to pdf
@see https://github.com/hblasins/OlympusAir/blob/master/OlympusAirPi.ipynb - almost a general API, but OPC specific??
'''

import requests
import json
from collections import OrderedDict
import time

def pretty_print_req(req):
    """
    At this point it is completely built and ready
    to be fired; it is "prepared".

    However pay attention at the formatting used in 
    this function because it is programmed to be pretty 
    printed and may differ from the actual request.
    """
    print('{}\n{}\n{}\n\n{}'.format(
        '-----------START-----------',
        req.method + ' ' + req.url,
        '\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        req.body,
    ))


if __name__ == '__main__':
    headers = {'Host':'192.168.0.10', 'User-Agent':'OI.Share v2', 'Accept':'*/*', 'Accept-Language':'en-US', 'Accept-Encoding':'gzip, deflate', 'Connection':'keep-alive'}
    #proxies = { 'http':'http://127.0.0.1:8888', 'https':'http://127.0.0.1:8888' }
    proxies = {}
    
    print("Getting cam info...")
    resp = requests.get('http://192.168.0.10/get_caminfo.cgi', headers=headers)
    print(resp.text)
    
    #print("Getting command list")
    #resp = requests.get('http://192.168.0.10/get_commandlist.cgi', headers=headers)
    #print(resp.text)
     
    print("Getting connect mode")
    resp = requests.get('http://192.168.0.10/get_connectmode.cgi', headers=headers)
    print(resp.text)
    time.sleep(1)
    
    # set recording mode?
    resp = requests.get('http://192.168.0.10/switch_cammode.cgi?mode=shutter', headers=headers, proxies=proxies)
    print(resp.text)
    time.sleep(1)
     
    # Works! Takes a picture
    print("Trying to take picture")
    resp = requests.get('http://192.168.0.10/exec_shutter.cgi?com=1st2ndpush', headers=headers)
    print(resp.text)
    time.sleep(1)
    resp = requests.get('http://192.168.0.10/exec_shutter.cgi?com=2nd1strelease', headers=headers)
    print(resp.text)
    time.sleep(1)
    
    # does nothing - I assume this is a half-press?
#     print("Trying to take picture just 1st push/release")
#     resp = requests.get('http://192.168.0.10/exec_shutter.cgi?com=1stpush', headers=headers)
#     print(resp.text)
#     resp = requests.get('http://192.168.0.10/exec_shutter.cgi?com=1strelease', headers=headers)
#     print(resp.text)
    
    # does nothing - I assume this doesnt correspnd to a possible real world button press?
#     print("Trying to take picture just 2nd push/release")
#     resp = requests.get('http://192.168.0.10/exec_shutter.cgi?com=2ndpush', headers=headers)
#     print(resp.text)
#     resp = requests.get('http://192.168.0.10/exec_shutter.cgi?com=2ndrelease', headers=headers)
#     print(resp.text)

    # Maybe need to be in live view mode first?
    print("Switching to rec mode")
    #proxies = { 'http':'http://127.0.0.1:8888', 'https':'http://127.0.0.1:8888' }
    #proxies = {}
    resp = requests.get('http://192.168.0.10/switch_cammode.cgi?mode=rec&lvqty=0640x0480', headers=headers, proxies=proxies)
    print(resp.text)
    time.sleep(1)

    # Internal error - but works when I proxy it through Charles?? Ah, needs to be in live view mode first! Cant be in shutter mode for whatever reason
    print("Gettng list of properties")
    #proxies = { 'http':'http://127.0.0.1:8888', 'https':'http://127.0.0.1:8888' }
    resp = requests.get('http://192.168.0.10/get_camprop.cgi?com=desc&propname=desclist', headers=headers, proxies=proxies)
#     req = requests.Request('GET', 'http://192.168.0.10/get_camprop.cgi?com=desc&propname=desclist', headers=headers, proxies=proxies)
#     prepared = req.prepare()
#     pretty_print_req(prepared)
#     sess = requests.Session()
#     resp = sess.send(prepared)
    print(resp.text)
    time.sleep(1)

    # Now its working, in the live view mode
    print("Trying to set aperture f11")
    body = '<?xml version="1.0"?><set><value>11</value></set>'
    #proxies = { 'http':'http://127.0.0.1:8888', 'https':'http://127.0.0.1:8888' }
    resp = requests.post('http://192.168.0.10/set_camprop.cgi?com=set&propname=focalvalue', data=body, headers=headers, proxies=proxies)
    print(resp.text)
    time.sleep(1)

    # Now its working, in the live view mode
    print("Trying to set shutter speed to 1/8 sec")
    body = '<?xml version="1.0"?><set><value>8</value></set>'
    #proxies = { 'http':'http://127.0.0.1:8888', 'https':'http://127.0.0.1:8888' }
    resp = requests.post('http://192.168.0.10/set_camprop.cgi?com=set&propname=shutspeedvalue', data=body, headers=headers, proxies=proxies)
    print(resp.text)
    time.sleep(1)

    # Now its working, in the live view mode
    print("Trying to set ISO to 800")
    body = '<?xml version="1.0"?><set><value>800</value></set>'
    #proxies = { 'http':'http://127.0.0.1:8888', 'https':'http://127.0.0.1:8888' }
    resp = requests.post('http://192.168.0.10/set_camprop.cgi?com=set&propname=isospeedvalue', data=body, headers=headers, proxies=proxies)
    print(resp.text)
    time.sleep(1)

    
#     print("Trying to set shutter mode to see if settings changed")
#     resp = requests.get('http://192.168.0.10/switch_cammode.cgi?mode=shutter', headers=headers)
#     print(resp.text)
    

    # None of this necessary?
#     print ('Camera live view start:')
#     params = OrderedDict([('com','startliveview'),('port',65001)])
#     req = requests.get('http://192.168.0.10/exec_takemisc.cgi',headers=headers,params=params)
#     if req.status_code == 200:
#         print ('OK')
#     else:
#         print ('Failed')
# 
#     print("Trying to take picture")
#     resp = requests.get('http://192.168.0.10/exec_takemotion.cgi?com=newstarttake',headers=headers)
#     if req.status_code == 200:
#         print ('OK')    
#     else:
#         print ('Failed, TCP/IP error %i' % req.status_code)
#     print(resp.text)
#     
#     print ('Camera live view stop:')
#     params = OrderedDict([('com','stopliveview')])
#     req = requests.get('http://192.168.0.10/exec_takemisc.cgi',headers=headers,params=params)
#     if req.status_code == 200:
#         print ('OK')
#     else:
#         print ('Failed')

    print("Trying to take picture")
    resp = requests.get('http://192.168.0.10/switch_cammode.cgi?mode=shutter', headers=headers)
    print(resp.text)
    time.sleep(1)
    resp = requests.get('http://192.168.0.10/exec_shutter.cgi?com=1st2ndpush', headers=headers, proxies=proxies)
    print(resp.text)
    time.sleep(1)
    resp = requests.get('http://192.168.0.10/exec_shutter.cgi?com=2nd1strelease', headers=headers, proxies=proxies)
    print(resp.text)
    time.sleep(1)
    
    # Still trying to take picture
#     resp = requests.get('http://192.168.0.10/switch_cammode.cgi?mode=shutter', headers=headers)
#     print(resp.text)
#     resp = requests.get('http://192.168.0.10/exec_takemotion.cgi?com=starttake', headers=headers, proxies=proxies)
#     print(resp.text)
#     resp = requests.get('http://192.168.0.10/exec_takemotion.cgi?com=endtake', headers=headers, proxies=proxies)
#     print(resp.text)


    # Take second exposure
    print("Switch to rec mode")
    resp = requests.get('http://192.168.0.10/switch_cammode.cgi?mode=rec&lvqty=0640x0480', headers=headers, proxies=proxies)
    print(resp.text)
    time.sleep(1)

    # Now its working, in the live view mode
    print("Trying to set aperture f8")
    body = '<?xml version="1.0"?><set><value>8</value></set>'
    #proxies = { 'http':'http://127.0.0.1:8888', 'https':'http://127.0.0.1:8888' }
    resp = requests.post('http://192.168.0.10/set_camprop.cgi?com=set&propname=focalvalue', data=body, headers=headers, proxies=proxies)
    print(resp.text)
    time.sleep(1)

    # Now its working, in the live view mode
    print("Trying to set shutter speed to 1/20 sec")
    body = '<?xml version="1.0"?><set><value>20</value></set>'
    #proxies = { 'http':'http://127.0.0.1:8888', 'https':'http://127.0.0.1:8888' }
    resp = requests.post('http://192.168.0.10/set_camprop.cgi?com=set&propname=shutspeedvalue', data=body, headers=headers, proxies=proxies)
    print(resp.text)
    time.sleep(1)

    # Now its working, in the live view mode
    print("Trying to set ISO to 640")
    body = '<?xml version="1.0"?><set><value>640</value></set>'
    #proxies = { 'http':'http://127.0.0.1:8888', 'https':'http://127.0.0.1:8888' }
    resp = requests.post('http://192.168.0.10/set_camprop.cgi?com=set&propname=isospeedvalue', data=body, headers=headers, proxies=proxies)
    print(resp.text)
    time.sleep(1)
    
    time.sleep(1)
    print("Trying to take second exposure")
    resp = requests.get('http://192.168.0.10/switch_cammode.cgi?mode=shutter', headers=headers)
    print(resp.text)
    time.sleep(1)
    resp = requests.get('http://192.168.0.10/exec_shutter.cgi?com=1st2ndpush', headers=headers, proxies=proxies)
    print(resp.text)
    time.sleep(1)
    resp = requests.get('http://192.168.0.10/exec_shutter.cgi?com=2nd1strelease', headers=headers, proxies=proxies)
    print(resp.text)
    time.sleep(1)
    
    # Try setting focus?
    print("Trying to set focus")
    #proxies = { 'http':'http://127.0.0.1:8888', 'https':'http://127.0.0.1:8888' }
    resp = requests.post('http://192.168.0.10/exec_takemisc.cgi?move=widemove', headers=headers, proxies=proxies)
    print(resp.text)
    time.sleep(1)
    
    time.sleep(1)
    print("Trying to take second exposure")
    resp = requests.get('http://192.168.0.10/switch_cammode.cgi?mode=shutter', headers=headers)
    print(resp.text)
    time.sleep(1)
    resp = requests.get('http://192.168.0.10/exec_shutter.cgi?com=1st2ndpush', headers=headers, proxies=proxies)
    print(resp.text)
    time.sleep(1)
    resp = requests.get('http://192.168.0.10/exec_shutter.cgi?com=2nd1strelease', headers=headers, proxies=proxies)
    print(resp.text)
    time.sleep(1)