import io
import random
import picamera
import picamera.array
from PIL import Image
import numpy as np
import time
import os
import tweepy

TWITTER_API_KEY = ''
TWITTER_API_SECRET_KEY = ''
TWITTER_ACCESS_TOKEN = ''
TWITTER_ACCESS_TOKEN_SECRET = ''

auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET_KEY)
auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
twitter = tweepy.API(auth)

def post_to_twitter():
    print("Posting To Twitter")
    pic = twitter.media_upload('temp/animation.gif')
    twitter.update_status(status = 'Visitor Alert! ', media_ids = [pic.media_id_string] )
    
class MotionDetector(picamera.array.PiMotionAnalysis):
    def __init__(self, camera, size=None):
        super(MotionDetector, self).__init__(camera, size)
        self.detected = 0
        self.motion = False
        
    def analyse(self, a):
        a = np.sqrt(
            np.square(a['x'].astype(np.float)) +
            np.square(a['y'].astype(np.float))
            ).clip(0, 255).astype(np.uint8)

        vector_count = (a > 70).sum()
        if vector_count > 11:
            self.detected = time.time()
            self.motion = True
        else:
            self.motion = False
        return self.motion
    
if __name__ == "__main__":
    if not os.path.exists('./temp'):
        os.makedirs('./temp')


    with picamera.PiCamera(framerate=24) as camera:
        camera.resolution = (600, 480)
        ring_buffer = picamera.PiCameraCircularIO(camera, seconds=10, bitrate=1000000)
        detector = MotionDetector(camera)
        camera.start_recording(ring_buffer, motion_output=detector, format='h264', bitrate=1000000)
        print("Started Camera")
        try:
            while True:
                print("Main Loop")
                camera.wait_recording(1)
                if not detector.motion:
                    print("no motion")
                    continue

                print("motion detected! taking pictures")
                for i in range(20):
                    if time.time() - detector.detected > 2:
                        print("Motion Stopped")
                        break
                    
                    file_name = 'temp/image{0:04d}.jpg'.format(i)
                    print("Capturing {}".format(file_name))
                    camera.capture(file_name, use_video_port=True)
                    camera.wait_recording(.3)
                print("Making GIF")
                os.system('convert -delay 10 -loop 0 temp/image*.jpg temp/animation.gif')
                post_to_twitter()
                os.system('rm -rf temp/*')
        finally:
            camera.stop_recording()
