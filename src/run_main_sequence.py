'''
Created on Jul 19, 2017

@author: ktankersley
@see https://gist.github.com/mangelajo/6fa005ff3544fecdecfa
@see https://crispgm.com/page/olympus-wifi-api.html for link to pdf
@see https://github.com/hblasins/OlympusAir/blob/master/OlympusAirPi.ipynb - almost a general API, but OPC specific??
'''

import requests
import json
import csv
from collections import OrderedDict
import time
from datetime import timedelta
import logging
import logging.config

class OlympusOmdEm1():
    def __init__(self, headers={'Host':'192.168.0.10', 'User-Agent':'OI.Share v2'}, proxies={} ):
        self.headers = headers
        self.proxies = proxies
        with open('conf/logging.conf') as logConfigFile:
            logging.config.dictConfig(json.load(logConfigFile))
        self.log = logging.getLogger('olympus-omd-em1-api-logger')
        self.log.info('Initialized camera proxy obj')
        self.currShutterSpeed = self.currFstop = self.currIsoSpeed = ''
        
    '''
        Handles forming the actual HTTP command for a given camera remote command, 
        making the HTTP call, checking the response codes, and logging the results.
    '''
    def callRemoteCommand(self, httpMethod, cgiScript, queryParams=OrderedDict(), postData='' ):
        fullUrl = 'http://{0}/{1}'.format(self.headers['Host'], cgiScript )
        resp = None
        if httpMethod in ['put','post', 'PUT', 'POST']:
            resp = requests.request(httpMethod,  fullUrl, headers=self.headers, params=queryParams, data=postData, proxies=self.proxies)
        else:
            resp = requests.request(httpMethod,  fullUrl, headers=self.headers, params=queryParams, proxies=self.proxies )
        
        self.log.info('Calling {0}'.format(resp.url) )
        time.sleep(0.05)
        
        if resp.status_code == requests.codes.ok:
            self.log.debug('Call to {0} returned success code {1}'.format(resp.url, resp.status_code) )
            self.log.debug('Returned response text: {0}'.format(resp.content) )
        else:
            self.log.error('Error! Call to {0} returned failure code {1}'.format(resp.url, resp.status_code) )
            self.log.error('Returned response text was: {0}'.format(resp.content) )
    
    '''
        Get camera info command, which should return an XML string with 'EM-1' as the main value.
        Mainly useful as a first command to issue the camera to wake it up.
    '''
    def getCameraInfo(self):
        self.log.info('Getting camera info')
        self.callRemoteCommand('GET', 'get_caminfo.cgi') 
        
    '''
        One of the most common use cases will be to vary the aperture/shutter/iso
        exposure parameters between shots, so have a single convenience method
        that can take all 3 in one call and make the 3 separate calls for us.
        Note that the camera has to be in record ('rec') mode to change these.
    '''
    def setExposureParams(self, fstop, shutterSpeed, isoSpeed):
        self.log.info('Switch to record mode and set fstop,shutterSpeed,isoSpeed={0},{1},{2}'.format(fstop, shutterSpeed, isoSpeed) )
        fstopPayload = '<?xml version="1.0"?><set><value>{0}</value></set>'.format(fstop)
        shutterSpeedPayload = '<?xml version="1.0"?><set><value>{0}</value></set>'.format(shutterSpeed)
        isoSpeedPayload = '<?xml version="1.0"?><set><value>{0}</value></set>'.format(isoSpeed)
        self.callRemoteCommand('GET', 'switch_cammode.cgi', queryParams=OrderedDict( [('mode','rec'), ('lvqty','0640x0480')] ) )
        time.sleep(0.05)
        self.callRemoteCommand('POST', 'set_camprop.cgi', queryParams=OrderedDict([('com','set'), ('propname','focalvalue')]), postData=fstopPayload)
        self.callRemoteCommand('POST', 'set_camprop.cgi', queryParams=OrderedDict([('com','set'), ('propname','shutspeedvalue')]), postData=shutterSpeedPayload)
        self.callRemoteCommand('POST', 'set_camprop.cgi', queryParams=OrderedDict([('com','set'), ('propname','isospeedvalue')]), postData=isoSpeedPayload)
        
        if shutterSpeed.endswith('"'):
            self.currExposureTime = float(shutterSpeed.replace('"', ''))
        else:
            self.currExposureTime = 1/float(shutterSpeed)
        self.currShutterSpeed = str(shutterSpeed)
        self.currFstop = float(fstop)
        self.currIsoSpeed = str(isoSpeed)
        
    '''
        Switch camera to 'shutter' mode and take an exposure. After exposure, sleep for a little while to
        allow the camera time to finish the exposure and then save the data to the card.
    '''
    def takeExposure(self):
        self.log.info('Switch to shutter mode, depress shutter fully, release shutter fully')
        self.callRemoteCommand('GET', 'switch_cammode.cgi', queryParams=OrderedDict([('mode','shutter')] ) )
        time.sleep(0.05)
        self.callRemoteCommand('GET', 'exec_shutter.cgi', queryParams=OrderedDict([('com','1st2ndpush')] ) )
        self.callRemoteCommand('GET', 'exec_shutter.cgi', queryParams=OrderedDict([('com','2nd1strelease')] ) )
        # For good measure, sleep for 25% longer than the exposure plus an extra quarter second to let exposure finish
        # and give camera time to write the data to its card
        sleepTime = 0.125 + 1.125 * self.currExposureTime
        self.log.info('Sleeping for {0} seconds while camera takes and saves exposure'.format(sleepTime) )
        time.sleep(sleepTime)
        
    '''
        Ideally, I could bracket my focus values here for each shot, but haven't 
        yet figured out how the camera deals with focus yet.
    '''
    def changeFocus(self, focalLength):
        # I'll need an android vm with oi.share and packet sniffer to figure out how to twiddle focus
        # TODO: Make any of this function work
        self.log.info('Switch to record mode and chage focal length to {0}'.format(focalLength) )
        self.callRemoteCommand('GET', 'switch_cammode.cgi', queryParams=OrderedDict( [('mode','rec'), ('lvqty','0640x0480')] ) )
        self.callRemoteCommand('GET', 'exec_takemisc.cgi', queryParams=OrderedDict([('com','newctrlzoom'),('ctrl','start'),('dir','fix'),('focallen',focalLength)])  )      
        
    '''
        Get list of what variables can be set and what valid values are. Set to record mode, since
        this is the mode you need to be in to get/set iso, shutter, aperture
    '''
    def getProperties(self):
        self.log.info('Switch to record mode and get list of valid properties and values' )
        self.callRemoteCommand('GET', 'switch_cammode.cgi', queryParams=OrderedDict( [('mode','rec'), ('lvqty','0640x0480')] ) )
        time.sleep(0.05)
        self.callRemoteCommand('GET', 'get_camprop.cgi', queryParams=OrderedDict([('com','desc'), ('propname','desclist')]) )

def loadExposurePlan():
    exposurePlan = []
    with open('conf/main_exposure_sequence.csv') as planFile:
        planReader = csv.DictReader(planFile)
        for exposure in planReader:
            exposurePlan.append(exposure)
    return exposurePlan

if __name__ == '__main__':
    
    startTime = time.time()
    headers = {'Host':'192.168.0.10', 'User-Agent':'OI.Share v2', 'Accept':'*/*', 'Accept-Language':'en-US', 'Accept-Encoding':'gzip, deflate', 'Connection':'keep-alive'}
    #proxies = { 'http':'http://127.0.0.1:8888', 'https':'http://127.0.0.1:8888' }
    proxies = {}
    exposurePlan= loadExposurePlan()
    olycam = OlympusOmdEm1(headers, proxies)
    olycam.log.info('Running exposure plan: ' + json.dumps(exposurePlan) )
    
    # Wake up camera
    olycam.getCameraInfo()
    #olycam.getProperties()
    
    for nextExposure in exposurePlan:
        olycam.setExposureParams(fstop=nextExposure['fstop'], shutterSpeed=nextExposure['shutter'], isoSpeed=nextExposure['iso'])
        olycam.takeExposure()
    
    endTime = time.time()
    elapsedSeconds = endTime - startTime
    olycam.log.info('Done with exposure sequence, final time was ' + str(timedelta(seconds=elapsedSeconds)) )
    