import cv2
import math
import numpy as np
from EasyContour import EasyContour

# Read the README.txt before trying to use this file, it will make your life a lot easier

# If this is true, it will run the pipeline, getting full performance, but you won't be able
# to have display output.
PIPELINE = False
# This can be a port number if it's an actual camera, or a video file
CAMERA_ID = "camera1_feed.mkv"
# This changes if it will display some debug windows
DISPLAY = True
RGB_BOUNDS = (np.array([0, 100, 0]), np.array([100, 255, 100]))
MATRIX = None
DISTORTION = None
TARGET_DIMENSIONS = EasyContour(((1, 2), (3, 4), (5, 6), (7, 8)))
TARGET_DIMENSIONS = TARGET_DIMENSIONS.format([["x", "y", 0], ["x", "y", 0]], np.float32)
if PIPELINE:
    import multiprocessing
else:
    import multiprocessing.dummy as multiprocessing
cap = None
img_org = None


def compute_output_values(rotation_vec, translation_vec):
    # From ligerbots 2019 vision code

    # Compute the necessary output distance and angles
    x = translation_vec[0][0] + 0
    z = 0 * translation_vec[1][0] + 1 * translation_vec[2][0]

    # distance in the horizontal plane between robot center and target
    robot_distance = math.sqrt(x**2 + z**2)

    # horizontal angle between robot center line and target
    robot_to_target_angle = math.atan2(x, z)

    rot, _ = cv2.Rodrigues(rotation_vec)
    rot_inv = rot.transpose()

    # version if there is not offset for the camera (VERY slightly faster)
    # pzero_world = numpy.matmul(rot_inv, -tvec)

    # version if camera is offset
    pzero_world = np.matmul(rot_inv, 0 - translation_vec)

    other_angle = math.atan2(pzero_world[0][0], pzero_world[2][0])

    return robot_distance, robot_to_target_angle, other_angle


def get_video(inp):
    global img_org
    if inp == "stop":
        return "stop"
    elif inp is None:
        return None
    ret, frame = cap.read()
    if not ret:
        return "stop"
    if not PIPELINE:
        if DISPLAY:
            cv2.imshow("Original image", frame)
    # Note: it may be better to do image processing here so that you won't have to wait
    # for memory transfer between processes
    if not PIPELINE:
        if DISPLAY:
            img_org = frame.copy()
    return frame


def process_frame(inp):
    if inp == "stop":
        return "stop"
    elif inp is None:
        return None
    frame = cv2.inRange(inp, RGB_BOUNDS[0], RGB_BOUNDS[1])
    if not PIPELINE:
        if DISPLAY:
            cv2.imshow("In range", frame)
    # Change RETER_EXTERNAL to RETER_TREE if you are getting spotty detection
    contours = cv2.findContours(frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = contours[1]
    if not PIPELINE:
        if DISPLAY:
            cv2.drawContours(img_org, contours, -1, (255, 0, 0), 3)
            cv2.imshow("Contours", img_org)
    easy_contours = []
    for cnt in contours:
        if len(cnt) > 5:
            easy_contours.append(EasyContour(cnt))
    return contours


def filtering_and_solving(inp):
    if inp == "stop":
        return "stop"
    elif inp is None:
        return None
    # This is where you put your code.  Inp is a list of EasyContour objects.
    corners = EasyContour(((1, 2), (3, 4), (5, 6), (7, 8)))
    solvepnp_formatted = corners.format([["x", "y"], ["x", "y"]], np.float32)
    # got_output, rotation_vector, translation_vector = cv2.solvePnP(TARGET_DIMENSIONS, solvepnp_formatted,
    #                                                                MATRIX, DISTORTION)
    # if not got_output:
    #     print("Solvepnp failed")
    #     return "stop"
    # distance, angle1, angle2 = compute_output_values(rotation_vector, translation_vector)
    # return distance, angle1, angle2
    return None


def work_function(input_queue, output_queue, function, camera=False):
    if camera:
        global cap
        cap = cv2.VideoCapture(CAMERA_ID)
    while True:
        returned = function(input_queue.get())
        if returned == "stop":
            print("%s thread exiting" % function)
            exit()
        output_queue.put(returned)


if __name__ == '__main__':
    queues = [multiprocessing.Queue(), multiprocessing.Queue(), multiprocessing.Queue(), multiprocessing.Queue()]
    processes = [multiprocessing.Process(target=work_function, args=(queues[0], queues[1], get_video, True)),
                 multiprocessing.Process(target=work_function, args=(queues[1], queues[2], process_frame)),
                 multiprocessing.Process(target=work_function, args=(queues[2], queues[3], filtering_and_solving))]
    for i in range(3):
        queues[0].put(None)
    for p in processes:
        p.start()
    while True:
        queues[0].put(0)
        gotten = queues[-1].get()
        if gotten == "stop":
            exit()
