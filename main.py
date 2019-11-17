import cv2
from EasyContour import EasyContour

# Read the README.txt before trying to use this file, it will make your life a lot easier

# If this is true, it will run the pipeline, getting full performance, but you won't be able
# to have display output.
PIPELINE = False
# This can be a port number if it's an actual camera, or a video file
CAMERA_ID = ""
if PIPELINE:
    import multiprocessing
else:
    import multiprocessing.dummy as multiprocessing
cap = None


def get_video(inp):
    if inp == "stop":
        return "stop"
    ret, frame = cap.read()
    if not ret:
        return "stop"
    # Note: it may be better to do image processing here so that you won't have to wait
    # for memory transfer between processes
    return frame


def process_frame(inp):
    if inp == "stop":
        return "stop"
