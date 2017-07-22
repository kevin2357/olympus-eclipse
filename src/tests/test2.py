'''
Created on Jul 19, 2017

@author: ktankersley
'''

import me.kevintankersley.imaging
from me.kevintankersley.imaging.CameraAPI import OlympusCamera

if __name__ == '__main__':
    cam = OlympusCamera()
    cam.commInterface('wifi')
    tst = cam.getState()
    print('Test getting camera state returned: %s', tst)