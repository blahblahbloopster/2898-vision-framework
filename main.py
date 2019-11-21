import logging
import time

import cv2
import sys
import math
import numpy as np
from EasyContour import EasyContour

# Read the README.md before trying to use this file, it will make your life a lot easier

# If this is true, it will run the pipeline, getting full performance, but you won't be able
# to have display output.
PIPELINE = False
# This can be a port number if it's an actual camera, or a video file
CAMERA_ID = "camera1_feed.mp4"
# This changes if it will display some debug windows
DISPLAY = False
RGB_BOUNDS = (np.array([0, 100, 0]), np.array([200, 255, 200]))
MATRIX = None
DISTORTION = None
TARGET_DIMENSIONS = EasyContour(((1, 2), (3, 4), (5, 6), (7, 8)))
TARGET_DIMENSIONS = TARGET_DIMENSIONS.format([["x", "y", 0], ["x", "y", 0]], np.float32)
if "--benchmark" in sys.argv:
    DISPLAY = False
    # PIPELINE = False
    loops = 20
else:
    loops = 0

if PIPELINE:
    import multiprocessing
else:
    import multiprocessing.dummy as multiprocessing
cap = None
img_org = None
STOP = -1
times_dict = {}
times_record = {}
frame_count = 0


def time_it(name, starting=True):
    if starting:
        times_dict[name] = time.monotonic()
    else:
        if name in times_record:
            times_record[name]["total"] += time.monotonic() - times_dict[name]
        else:
            times_record[name] = {"total": time.monotonic() - times_dict[name],
                                  "calls": 1}


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
    global loops
    global cap
    global frame_count
    if inp is STOP:
        return STOP
    elif inp is None:
        return None
    time_it("read")
    ret, frame = cap.read()
    time_it("read", False)
    # print(cap)
    frame_count += 1
    # if frame_count >= cap.get(cv2.CAP_PROP_FRAME_COUNT) and loops > 0:
    if (not ret) and loops > 0:
        loops -= 1
        print("Looping... (%s loops left)" % loops)
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        frame_count = 0
        ret, frame = cap.read()
    if not ret:
        return STOP
    # if not ret:
    #     if loops > 0:
    #         loops -= 1
    #         # del cap
    #         # cap = None
    #         # cap.release()
    #         # cap2 = cv2.VideoCapture(CAMERA_ID)
    #         # cap.set(cv2.CAP_PROP_POS_FRAMES, 1)
    #         print("Looping")
    #         # cap.open(CAMERA_ID)
    #         # ret, frame = cap2.read()
    #     else:
    #         return STOP
    if not PIPELINE:
        if DISPLAY:
            cv2.imshow("Original image", frame)
    if not PIPELINE:
        if DISPLAY:
            img_org = frame.copy()
    time_it("thresh")
    frame = cv2.inRange(frame, RGB_BOUNDS[0], RGB_BOUNDS[1])
    time_it("thresh", False)
    return frame


def process_frame(inp):
    if inp is STOP:
        return STOP
    elif inp is None:
        return None
    if not PIPELINE:
        if DISPLAY:
            cv2.imshow("In range", inp)
    # Change RETER_EXTERNAL to RETER_TREE if you are getting spotty detection
    time_it("contours")
    contours = cv2.findContours(inp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = contours[1]
    time_it("contours", False)
    if not PIPELINE:
        if DISPLAY:
            cv2.drawContours(img_org, contours, -1, (255, 0, 0), 3)
            cv2.imshow("Contours", img_org)
    time_it("easy")
    easy_contours = []
    for cnt in contours:
        if len(cnt) > 5:
            easy_contours.append(EasyContour(cnt))
    time_it("easy", False)
    return easy_contours


def filtering_and_solving(inp):
    if inp is STOP:
        return STOP
    elif inp is None:
        return None
    # This is where you put your code.  Inp is a list of EasyContour objects.
    time_it("solvepnp")
    corners = EasyContour(((1, 2), (3, 4), (5, 6), (7, 8)))
    solvepnp_formatted = corners.format([["x", "y"], ["x", "y"]], np.float32)
    time_it("solvepnp", False)
    # got_output, rotation_vector, translation_vector = cv2.solvePnP(TARGET_DIMENSIONS, solvepnp_formatted,
    #                                                                MATRIX, DISTORTION)
    # if not got_output:
    #     print("Solvepnp failed")
    #     return "stop"
    # distance, angle1, angle2 = compute_output_values(rotation_vector, translation_vector)
    # return distance, angle1, angle2
    return None


def work_function(input_queue, output_queue, function, times_queue, camera=False):
    if camera:
        global cap
        cap = cv2.VideoCapture(CAMERA_ID)
    while True:
        returned = function(input_queue.get())
        if returned is STOP:
            print("%s thread exiting" % function)
            output_queue.put(STOP)
            times_queue.put(times_record)
            exit()
        output_queue.put(returned)


if __name__ == '__main__':
    times_q = multiprocessing.Queue()
    queues = [multiprocessing.Queue(), multiprocessing.Queue(), multiprocessing.Queue(), multiprocessing.Queue()]
    processes = [multiprocessing.Process(
        target=work_function, args=(queues[0], queues[1], get_video, times_q, True)),
                 multiprocessing.Process(
                     target=work_function, args=(queues[1], queues[2], process_frame, times_q)),
                 multiprocessing.Process(
                     target=work_function, args=(queues[2], queues[3], filtering_and_solving, times_q))]
    for i in range(5):
        queues[0].put(None)
    for p in processes:
        p.start()
    reps = 0
    start = time.time()
    begin = time.time()
    while True:
        reps += 1
        if reps >= 100:
            elapsed = time.time() - start
            print("Avg FPS: %s, avg time per frame: %s" % (reps / elapsed, elapsed / reps))
            reps = 0
            start = time.time()
        queues[0].put(0)
        gotten = queues[-1].get()
        if gotten is STOP:
            break
        if DISPLAY:
            if cv2.waitKey(5) & 0xFF == ord("q"):
                break
    total_time = time.time() - begin
    time.sleep(0.1)
    all_times = {}
    while times_q.qsize() > 0:
        all_times.update(times_q.get())
    sorted_times = sorted(all_times.items(), key=lambda x: x[1]["total"], reverse=True)
    print("Total time: %s" % total_time)
    print("Time tracked: %s" % (sum(map(lambda x: x[1]["total"], sorted_times)) / total_time * 100), end="%\n")
    for i in sorted_times:
        print(str(i[0]).ljust(25, " ") + str(i[1]["total"]))
    # print(all_times.values())
