from io import BytesIO
import json
import socket
import sys
import base64
import logging
import argparse
import configparser
import time
import os
import pickle
import cv2
from queue import PriorityQueue
from threading import Thread
import numpy as np


BASE_DIR = os.path.dirname(__file__)

conf_parser = configparser.ConfigParser()
conf_parser.read(os.path.join(BASE_DIR, 'drone.ini'))

DRONE_ID        = conf_parser['drone'].getint('ID')
DRONE_NAME      = conf_parser['drone']['NAME']
DRONE_TYPE      = conf_parser['drone']['TYPE']

DRONE_IP        = conf_parser['network']['IP']
DRONE_PORT      = conf_parser['network'].getint('VIDEO_PORT')

HOST_IP         = conf_parser['server']['IP']
HOST_PORT       = conf_parser['server'].getint('PORT')

VIDEO_CAMERA    = conf_parser['video'].get('CAMERA_INDEX')
VIDEO_CAMERA    = int(VIDEO_CAMERA) if VIDEO_CAMERA.isnumeric() else str(VIDEO_CAMERA)
VIDEO_QUALITY   = conf_parser['video'].getint('JPEG_QUALITY')
VIDEO_WIDTH     = conf_parser['video'].getint('WIDTH')
VIDEO_HEIGHT    = conf_parser['video'].getint('HEIGHT')
VIDEO_FPS       = conf_parser['video'].getfloat('FPS')
VIDEO_GRAYSCALE = conf_parser['video'].getboolean('GRAYSCALE')
VIDEO_HEATMAP   = conf_parser['video'].getboolean('HEATMAP')
MOTION_DETECTION   = conf_parser['video'].getboolean('MOTION_DETECTION')


BUFFER_SIZE = 65536

logger = logging.getLogger()

logging.basicConfig(#filename=f'./logs/{int(time.time())}-log.log', filemode='w',
    format="[%(asctime)s] - [%(levelname)s] - %(message)s", level=logging.DEBUG,
)
logger.info('client started successfully')

class VideoStreamThread(Thread):
    def __init__(self, ip, port, camera, *a, grayscale=False, heatmap=False, apply_motion_detection=False, **kw):
        Thread.__init__(self, *a, **kw)

        self.ip = ip
        self.port = port
        self.camera = camera
        self.grayscale = grayscale
        self.heatmap = heatmap
        self.consecutive_frame = 4
        self.apply_motion_detection = apply_motion_detection

        self.__receiver_ip = None
        self.__receiver_port = None
        self.__q = PriorityQueue(25)
        
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,BUFFER_SIZE)
        self.client_socket.connect((self.ip, self.port))

    def _create_video_cap(self):
        """_create_video_cap is the method responsible for create
            video cap obj and connect cv2 to the camera """

        cap = cv2.VideoCapture(self.camera)
        self.__fps = cap.get(cv2.CAP_PROP_FPS)
        cap.set(cv2.CAP_PROP_FPS, self.__fps)

        logger.info('camera hooked up successfully')

        return cap

    def _send_data(self, frame):
        
        _, jpeg = cv2.imencode('.jpeg', frame, [cv2.IMWRITE_JPEG_QUALITY, VIDEO_QUALITY])
        buffer = jpeg.tobytes()

        message = self._pack_message(buffer=buffer)

        try:
            self.client_socket.sendto(message, (self.__receiver_ip, self.__receiver_port))
        except OSError as e:
            logger.error(str(e))
            

    @staticmethod
    def _pack_message(buffer):
        """
            _pack_message repsonsible for packing the buffer from the camera into a base64 bytearrey
            :TODO add to the buffer bytes the drone id
            @param: buffer : bytearray 
        """
        # p = pickle.dumps(buffer)
        message = base64.b64encode(buffer)
        print("BUFFER => {:.2f}KB\tBASE64 => {:.2f}KB\t"\
            .format(sys.getsizeof(buffer)/1024., sys.getsizeof(message)/1024.), end='\r')

        return message

    def _wait_till_ready(self):
        self.client_socket.sendto(b'client', (self.ip, self.port))

        while True:
            data = self.client_socket.recv(1024).decode()

            if data.strip() == 'ready':
                logger.info('checked in with server, waiting')
                break

        data = self.client_socket.recv(1024).decode()

        ip, sport, _ = data.split(' ')
        sport = int(sport)

        self.__receiver_ip = ip
        self.__receiver_port = sport

        logger.info("got new connection from {}:{}".format(self.__receiver_ip, self.__receiver_port))

    def get_background(self):
        # we will randomly select 50 frames for the calculating the median
        frame_indices = self.cap.get(cv2.CAP_PROP_FRAME_COUNT) * np.random.uniform(size=50)
        # we will store the frames in array
        frames = []
        for idx in frame_indices:
            
            # set the frame id to read that particular frame
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = self.cap.read()
            frame = cv2.resize(frame, (VIDEO_WIDTH, VIDEO_HEIGHT))
            frames.append(frame)
        # calculate the median
        median_frame = np.median(frames, axis=0).astype(np.uint8)
        # print(median_frame)
        return median_frame

    def run(self):
        logger.info('Stream started successfully')
        
        self._wait_till_ready()

        self.cap = self._create_video_cap()
        if self.apply_motion_detection:

            background = self.get_background()
            # convert the background model to grayscale format
            background = cv2.cvtColor(background, cv2.COLOR_BGR2GRAY)

            frame_count = 0

        try:
            while self.cap.isOpened():
                ret, frame = self.cap.read()

                if ret:
                    
                    # frame = imutils.resize(frame, width=VIDEO_WIDTH)
                    frame = cv2.resize(frame, (VIDEO_WIDTH, VIDEO_HEIGHT))
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    # print(gray.shape, background.shape)


                    # frame = cv2.flip(frame, 1)
                    if self.grayscale:
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    # if self.heatmap:
                    #     frame = cv2.applyColorMap(frame, cv2.COLORMAP_HOT)

                    if not self.apply_motion_detection: 
                        self._send_data(frame)
                        if isinstance(self.camera, str):
                            time.sleep(1./VIDEO_FPS)
                        continue

                    frame_count += 1
                    
                    if frame_count % self.consecutive_frame == 0 or frame_count == 1:
                        frame_diff_list = []
                    # find the difference between current frame and base frame
                    frame_diff = cv2.absdiff(gray, background)
                    # thresholding to convert the frame to binary
                    ret, thres = cv2.threshold(frame_diff, 50, 255, cv2.THRESH_BINARY)
                    # dilate the frame a bit to get some more white area...
                    # ... makes the detection of contours a bit easier
                    dilate_frame = cv2.dilate(thres, None, iterations=2)
                    # append the final result into the `frame_diff_list`
                    frame_diff_list.append(dilate_frame)
                    # if we have reached `self.consecutive_frame` number of frames
                    if len(frame_diff_list) == self.consecutive_frame:
                        # add all the frames in the `frame_diff_list`
                        sum_frames = sum(frame_diff_list)

                            # find the contours around the white segmented areas
                        contours, hierarchy = cv2.findContours(sum_frames, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                        
                        for contour in contours:
                            
                            if cv2.contourArea(contour) < 800:
                                continue
                            (x, y, w, h) = cv2.boundingRect(contour)
                            # draw the bounding boxes
                            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

                        self._send_data(gray)

                    
                    if isinstance(self.camera, str):
                        time.sleep(1./VIDEO_FPS)

                else:
                    self.cap = cv2.VideoCapture(self.camera) #self.camera)

        except KeyboardInterrupt as e:
            self.cap.release()
            # break

    def __del__(self):
        self.cap.release()
        self.client_socket.close()



def main():
    sample_video = './vid.mp4'

    vs = VideoStreamThread(ip=HOST_IP, port=HOST_PORT, camera=VIDEO_CAMERA, grayscale=VIDEO_GRAYSCALE, heatmap=VIDEO_HEATMAP, apply_motion_detection=MOTION_DETECTION)

    logger.info('created a new video stream thread')
    logger.info('created a new video stream with IP {}: PORT {}: CAMEAR {}: GRAYSCALE {}' \
        .format(DRONE_IP, DRONE_PORT, sample_video, VIDEO_GRAYSCALE))
    
    vs.start()
    logger.info('started the video stream thread')


if __name__ == '__main__':
    main()
