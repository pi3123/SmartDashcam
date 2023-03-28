from webcam_recorder import Webcam
from tqdm import tqdm
import time


def main():
    camera = Webcam(output_path='outputVideo\\', average_frame_size=80)
    # camera.clear_frames_stack()
    camera.start()

    for i in tqdm(range(1)):
        time.sleep(1)

    camera.stop()
    camera.get_x_minutes(5)


if __name__ == '__main__':
    main()
