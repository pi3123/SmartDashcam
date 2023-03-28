from queue import Queue
import cv2
import time
import os
import threading
from tqdm import tqdm
from datetime import datetime
import helper


class Webcam:
    def __init__(self, output_path, width=1920, height=1080, fps=30.0,
                 max_video_duration_minutes=30, max_memory=1024 * 1024, quality=20):
        # Capture module setup
        self._capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # get rid of the cv2.CAP_DSHOW when running on rpi3
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self._capture.set(cv2.CAP_PROP_FPS, fps)
        self._capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))

        # paths
        self.frames_output_path = "outputFrames\\"
        self.video_output_path = output_path

        # parameters for saving video
        self.WIDTH = width
        self.HEIGHT = height
        self.FPS = fps
        self.quality = quality

        # Queue and threading setup
        self._stop_event = threading.Event()  # when set, the thread will stop
        self._thread = None

        # Loop recording parameters
        self._max_frames_stored = max_video_duration_minutes * fps * 60
        self.timestamps = helper.get_frames(self.frames_output_path)
        print(self.timestamps)


    def start(self):
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._record, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread.join()
        self._capture.release()

    def restart(self):
        print("Restarting dashcam...")
        self.stop()
        self.clear_frames_stack()
        self.start()

    def clear_frames_stack(self):
        # get all frames path
        frames = []
        for filename in os.listdir(self.frames_output_path):
            filepath = os.path.join(self.frames_output_path, filename)
            if os.path.isfile(filepath):
                frames.append(filepath)

        # delete all frames
        looper = tqdm(frames)
        looper.set_description("Clearing frames stack")
        for frame in looper:
            os.remove(frame)

        # clear the timestamp stack
        self.timestamps = []

    def _record(self):
        while not self._stop_event.is_set():
            ret, frame = self._capture.read()
            if not ret:
                raise Exception("No frame captured")

            # Generate filename for the frame
            timestamp = datetime.now().timestamp()
            frame_filename = os.path.join(self.frames_output_path, str(timestamp)) + ".jpg"

            # Add timestamp to queue
            self.timestamps.append(timestamp)

            # saving frame as JPEG file
            video_writer = threading.Thread(target=cv2.imwrite, args=(frame_filename, frame,
                                                                      [cv2.IMWRITE_JPEG_QUALITY, self.quality]))
            video_writer.start()

            # Removing overflowing frames
            if len(self.timestamps) >= self._max_frames_stored + 1:
                to_remove = self.timestamps.pop(0)
                frame_to_remove = self.frames_output_path + to_remove + ".jpg"

                os.remove(frame_to_remove)

    def get_x_minutes(self, Xminutes, wait_for_future_frames=False):
        if wait_for_future_frames:
            with tqdm(range(int(Xminutes / 2 * 60))) as pbar:
                pbar.set_description("Waiting for future frames")
                for _ in pbar:
                    time.sleep(1)

        if len(self.timestamps) < self.FPS * 60 * Xminutes:
            timestamps_to_return = self.timestamps
        else:

            end_timestamp = datetime.now().timestamp()
            start_timestamp = end_timestamp - (Xminutes * 60)  # X minutes before the current time

            start_index = helper.search_for_timestamp(self.timestamps, start_timestamp)
            if start_index is None:
                raise Exception("Start time invalid")

            end_index = helper.search_for_timestamp(self.timestamps, end_timestamp)
            if end_index is None:
                end_index = len(self.timestamps) - 1

            timestamps_to_return = self.timestamps[start_index:end_index + 1]

        # generate filename for 5-minute video
        filename = str(datetime.fromtimestamp(timestamps_to_return[0]))
        filename = filename.replace(" ", "-")
        filename = filename.replace(":", "-")
        filename = os.path.join(self.video_output_path, filename)

        # start video making thread
        videoPbar = tqdm(total=len(timestamps_to_return), desc="Reading video frames", position=0)
        videoMaker = threading.Thread(target=self.get_video, args=(timestamps_to_return, filename + ".mp4", videoPbar))
        videoMaker.start()

        # # wait for the threads to finish
        videoMaker.join()

    def get_video(self, timestampsToReturn, fileName, pbar, bitrate=80000):
        if len(timestampsToReturn) == 0:
            raise Exception("No frames to return")

        # generating video
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        output = cv2.VideoWriter(fileName, fourcc, self.FPS, (self.WIDTH, self.HEIGHT))

        frame_queue = Queue()

        def read_frames():

            for timestamp in timestampsToReturn:
                filename = self.frames_output_path + str(timestamp) + ".jpg"
                Frame = cv2.imread(filename)

                # TODO: Memory management

                frame_queue.put(Frame)

                pbar.update(1)
            frame_queue.put(None)

        def write_frames():
            while True:
                Frame = frame_queue.get()
                if Frame is None:
                    break

                encoded_frame, _ = cv2.imencode('.jpg', Frame, [cv2.IMWRITE_JPEG_QUALITY, bitrate])
                output.write(Frame)

            output.release()

        # use two threads for reading and writing frames
        read_thread = threading.Thread(target=read_frames)
        write_thread = threading.Thread(target=write_frames)

        # start the threads
        read_thread.start()
        write_thread.start()

        # # wait for the threads to finish
        write_thread.join()
        read_thread.join()


if __name__ == "__main__":
    camera = Webcam(output_path='outputVideo\\', average_frame_size=70, width=1920, height=1080)
    camera.clear_frames_stack()
    camera.start()

    timer = 1  # seconds
    for i in tqdm(range(timer), desc="Recording"):
        time.sleep(1)
    camera.stop()

    camera.get_x_minutes(10)
