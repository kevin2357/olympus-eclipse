'''
Created on Jul 19, 2017

@author: ktankersley
'''

import requests
import socket
import xmltodict
import json
import os
import datetime
from collections import OrderedDict
from datetime import date

#from PIL import Image
from io import StringIO

class OlympusCameraEvent:
    def __init__(self,appID,eventID,data):
        self.appID = appID
        self.eventID = eventID
        self.data = data
    
    def __str__(self):
        return 'appID: %i; eventID: %i; data: %s' % (self.appID, self.eventID, self.data)
    
class OlympusCameraFile:
    def __init__(self,paramList):
        self.directory = paramList[0]
        self.fileName = paramList[1]
        self.size = int(paramList[2])
        self.attr = int(paramList[3])
        self.date = int(paramList[4])
        self.time = int(paramList[5])
        
    def __repr__(self):
        return '(%s, %s, %i, %i, %s)' % (self.directory,self.fileName, self.size, self.attr, self.getDate().strftime('%Y-%m-%d_%H-%M-%S'))

    def __cmp__(self,other):
        if self.date > other.date:
            return 1
        elif self.date < other.date:
            return -1
        else:
            if self.time > other.time:
                return 1
            elif self.time < other.time:
                return -1
            else:
                return 0
    
    def getDate(self):
        
        day = int(self.date & 0x1f)
        month = int((self.date & 0x1e0) >> 5)
        year = int((self.date & 0xfe00) >> 9) + 1980
        
        sec = int(self.time & 0x1f)*2
        minutes = int((self.time & 0x7e) >> 5)
        hours = int((self.time & 0xf088) >> 11)
        
        
        return datetime.datetime(year,month,day,hours,minutes,sec)
        

class OlympusCamera:
    
    #headers = {'User-Agent':'OlympusCameraKit'}
    headers = {'Host':'192.168.0.10', 'User-Agent':'OI.Share v2', 'Accept':'*/*', 'Accept-Language':'en-US', 'Accept-Encoding':'gzip, deflate', 'Connection':'keep-alive'}
    proxies = None
    
    def __init__(self, evPort=65000, lvPort=65001, debug_proxies=None):
        self.proxies = debug_proxies
        #headers = {'User-Agent':'OlympusCameraKit'}
        self.headers = {'Host':'192.168.0.10', 'User-Agent':'OI.Share v2', 'Accept':'*/*', 'Accept-Language':'en-US', 'Accept-Encoding':'gzip, deflate', 'Connection':'keep-alive'}
        req = requests.get('http://192.168.0.10/get_connectmode.cgi',headers=self.headers, proxies=self.proxies)
    
        if req.status_code == 200: #and (xmltodict.parse(req.text)['connectmode'] == 'OPC'):
            print('Camera init: OK, %s' % xmltodict.parse(req.text)['connectmode'] )
        else:
            print( 'Camera init: Failed')
            
        print('Putting camera in play mode')
        resp = requests.get('http://192.168.0.10/switch_cammode.cgi?mode=rec',headers=self.headers, proxies=self.proxies)
        if resp.status_code == 200: #and (xmltodict.parse(req.text)['connectmode'] == 'OPC'):
            print('Play mode switch: OK'  )
        else:
            print( 'Play mode switch: Failed')
        
        print ('Establishing camera event notification:')
        params={'port':evPort}
        req = requests.get('http://192.168.0.10/start_pushevent.cgi',headers=self.headers,params=params, proxies=self.proxies)
        print(req.text)
        print(req.status_code)
        if req.status_code == 200:
            print('OK')
        else:
            print('Failed')
        
       
        # Establish an event socket. Keep trying untill you succeed
        print('Establishing event socket, port %i: ' % evPort,)
        
      
        self.eventSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.eventSocket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.eventSocket.settimeout(10)
        
        self.eventSocket.connect(('192.168.0.10',evPort))
    
        # soc.bind(('',evPort))
        self.eventPort = evPort   
        self.lvPort = lvPort
        
        
        

        
    def disconnect(self):        
        print('Disconnecting camera:',)
        req = requests.get('http://192.168.0.10/stop_pushevent.cgi',headers=self.headers)
        if req.status_code == 200:
            print('OK')
        else:
            print('Failed')
        
        self.eventSocket.close()
             
            
            
            
            
            
    def commInterface(self,interface='wifi'):
        print('Camera communication mode change to %s:' % interface)
        params = {'path':interface}
        
        req = requests.get('http://192.168.0.10/switch_commpath.cgi',headers = self.headers, params = params)
        if req.status_code == 200:
            print('OK')
        else:
            print('Failed')
        
        
        
        
        
    def getState(self):
        req = requests.get('http://192.168.0.10/get_state.cgi',headers=self.headers)

        if req.status_code == 200:
            return xmltodict.parse(req.text)['response']
        else:
            return []

        
        
        
        
    def switchMode(self,mode_params):
        print('Camera mode change to %s:' % json.dumps(mode_params) )
        #params = {'mode':mode}
        req = requests.get('http://192.168.0.10/switch_cameramode.cgi',headers=self.headers,params=mode_params)
        
        if req.status_code == 200 and xmltodict.parse(req.text)['result'] == 'OK':
            print('OK')
        else:
            print('Failed %i' % req.status_code)
        
        
        selected, event = self.waitForEvent([201])
        for (i,j) in zip(selected,event):
            print (i, j)
        
    
    
    
    def getFilesList(self,dirName='/DCIM/100OLYMP'):
        params = {'DIR':dirName}
        req = requests.get('http://192.168.0.10/get_imglist.cgi',headers=self.headers,params=params)
        
        if req.status_code == 404:
            print ('Not found')
            return None
        
        filesList = []
        for l in req.text.splitlines()[1:]:
            filesList.append(OlympusCameraFile(l.split(',')))
        
        return filesList
    
    
    
    
    
        

    def getFile(self,path):
        req = requests.get('http://192.168.0.10' + path,headers=self.headers)
        
        
        return req
    
    
    def getLatestFile(self):
        
        fList = self.getFilesList()
        fList.sort(reverse = True)
        
        
        f1Name, f1Format = fList[0].fileName.split('.')
        f1 = self.getFile(fList[0].directory + '/' + fList[0].fileName)
        
        f2Name, f2Format = fList[1].fileName.split('.')
        
        if f2Name == f1Name and f1Format != f2Format :
            f2 = self.getFile(fList[1].directory + '/' + fList[1].fileName)
        
            if f1Format == 'JPG' and f2Format == 'ORF':
                return f1.content, f2.content
            elif f1Format == 'ORF' and f2Format == 'JPG':
                return f2.content, f1.content
        
        return f1.content, None
    
    
    
    
    def getResizedFile(self, path, size):
        headers = {'User-Agent':'OlympusCameraKit'}
        params = {'DIR':path,'size':size}
        
        
        req = requests.get('http://192.168.0.10/get_resizeimg.cgi',headers=headers, proxies=self.proxies, params=params)
        print(req.status_code)
        
        return req
    
    
    
    
    
    
    def setZoom(self, focalLength):
        
        print ('Camera zoom set to %i:' % focalLength)
        params = OrderedDict([('com','newctrlzoom'),('ctrl','start'),('dir','fix'),('focallen',focalLength)])
        
        req = requests.get('http://192.168.0.10/exec_takemisc.cgi',headers=self.headers,params=params)
        
        if req.status_code == 200 and (xmltodict.parse(req.text)['result'] == 'OK'):
            print('OK') 
        else:
            print('Failed')
            return
            
        selected, event = self.waitForEvent([122])

   
            
            
            
            
    def getEventNotifications(self,sock):
        
        i = 0
        
        buff = sock.recv(1024)
        eventList = []
        while i < len(buff)-1:
            appID = ord(buff[i+0])
            event = ord(buff[i+1])
            length = ord(buff[i+2])*256 + ord(buff[i+3])
            data = buff[(i+4):(i+4+length)]
                
            event = OlympusCameraEvent(appID,event,data)
            # print event
            i = i+4+length
            eventList.append(event)
        
        return eventList
    
    def findEvent(self,eventList,eventID):
        sel = [None] * len(eventID)
        found = [False] * len(eventID)
         
        for e in eventList:
            # print e 
            if e.eventID in eventID:
                found = [True if e.eventID == j else False for j in eventID]
                sel = [e if e.eventID == j else None for j in eventID]
            
        return found, sel
    
    def waitForEvent(self,eventID,mode = 'AND'):
        
        found = [False]*len(eventID)
        event = [None]*len(eventID)
        # print found
        
        
        i=0
        while i < 10:
 
            try:
                eventList = self.getEventNotifications(self.eventSocket)
                tmpFound, tmpEvent = self.findEvent(eventList,eventID)
                # print i, found, tmpFound, tmpEvent
                event = [i if j else k for (i,j,k) in zip(tmpEvent,tmpFound,event)]
                found = [i or j for (i,j) in zip(tmpFound,found)]                                          
                
                # print found, tmpFound == True
                if mode == 'AND':
                    if all(found):
                        return found, event
                else:
                    if any(found):
                        return found, event
                
            except socket.timeout as err:
                print('Timeout')
            
            i = i+1
        
        return found, event
            
        
    def getProperty(self,propName):
   
        print('Camera property %s read' % propName)
        params=OrderedDict([('com','desc'),('propname',propName)])
        req = requests.get('http://192.168.0.10/get_camprop.cgi',headers=self.headers,params=params)
        
        if req.status_code == 200:
            state = xmltodict.parse(req.text)['desc']['value']
            allowedStates = xmltodict.parse(req.text)['desc']['enum']
            print ('%s (%s): OK' % (state,allowedStates))
            return state
        else:
            print (': Fail')
        
 
    def setProperty(self, propName, propVal):
        
        # We need to get the property first. Setting a property to a value that is equal to the old value does not always
        # work.
        currentVal = self.getProperty(propName)
        print ('Camera property %s change to %s:' % (propName,propVal)) 
        if currentVal != propVal:
            
            params = OrderedDict([('com','set'),('propname',propName)])
            payload = '<?xml version="1.0"?><set><value>%s</value></set>\n' % (propVal)
        
            req = requests.post('http://192.168.0.10/set_camprop.cgi',headers=self.headers,params=params,data=payload)
    
            if req.status_code == 200:
                print ('OK')
            else:
                print ('Fail')

            
            selected, event = self.waitForEvent([206])
            for (i,j) in zip(selected,event):
                print (i,j)
        else:
            print  ('Not needed')
        
        
        
        
        
        
    def startPreview(self,resolution = '0320x0240'):
        
        
        print ('Establishing liveview socket %i:' % self.lvPort,)    
        self.lvSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) #UDP
        self.lvSocket.bind(('',self.lvPort))
        self.lvSocket.settimeout(20)
        print ('OK') 
            
        
        
        
        print ('Camera live view resolution change to %s:' % resolution)
        params = OrderedDict([('com','changelvqty'),('lvqty',resolution)])
        req = requests.get('http://192.168.0.10/exec_takemisc.cgi',headers=self.headers,params=params)
        if req.status_code == 200 and (xmltodict.parse(req.text)['result'] == 'OK'):
            print ('OK')
        else:
            print ('Failed TCP/IP error %i, response %s' % (req.status_code,req.text))
            return False
        
        
        
        print ('Camera live view start:')
        params = OrderedDict([('com','startliveview'),('port',self.lvPort)])
        req = requests.get('http://192.168.0.10/exec_takemisc.cgi',headers=self.headers,params=params)
        if req.status_code == 200:
            print ('OK')
        else:
            print ('Failed')
            return False
        
        
        data = self.lvSocket.recvfrom(128)
        if len(data) > 0:
            return True
        else:
            return False
        
            
        
    def takePicture(self):
        print ('Camera picture acquisition:')
        params = OrderedDict([('com','newstarttake')])
        req = requests.get('http://192.168.0.10/exec_takemotion.cgi',headers=self.headers,params=params)
                
        if req.status_code == 200:
            print ('OK')    
        else:
            print ('Failed, TCP/IP error %i' % req.status_code)
        
        
        eventIDs = [101,107] 
        ind, event = self.waitForEvent([101,107])
        for (i,j,k) in zip(eventIDs,ind,event):
            print (i,j,k)
        
        
    def stopPreview(self):
        print ('Camera live view stop:',)
        params = OrderedDict([('com','stopliveview')])
        req = requests.get('http://192.168.0.10/exec_takemisc.cgi',headers=self.headers,params=params)
        
        if req.status_code == 200:
            print ('OK')
        else:
            print ('Failed')
        
        
        self.lvSocket.close()