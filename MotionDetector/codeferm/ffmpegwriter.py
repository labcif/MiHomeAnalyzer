"""
Created on Apr 12, 2017

@author: sgoldsmith

Copyright (c) Steven P. Goldsmith

All rights reserved.
"""

import numpy, ffmpeg
from . import writerbase


class ffmpegwriter(writerbase.writerbase):
    """Video writer based on ffmpeg-python.
    
    Encode single numpy image as video frame.

    """
    
    def __init__(self, fileName, vcodec, fps, frameWidth, frameHeight):
        self.process = (
            ffmpeg
            .input('pipe:', framerate='{}'.format(fps), format='rawvideo', pix_fmt='bgr24', s='{}x{}'.format(frameWidth, frameHeight))
            .output(fileName, vcodec=vcodec, pix_fmt='nv21', acodec='n', **{'b:v': 2000000})
            .global_args('-hide_banner', '-nostats', '-loglevel', 'panic')            
            .overwrite_output()
            .run_async(pipe_stdin=True)
        )
       
    
    def write(self, image):
        """ Convert raw image format to something ffmpeg understands """
        self.process.stdin.write(
            image
            .astype(numpy.uint8)
            .tobytes()
        )        
   
    def close(self):
        """Clean up resources"""
        self.process.stdin.close()
        self.process.wait()
