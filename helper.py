import os


def search_for_timestamp(arr, timestamp):
    # set the initial low and high indexes
    low = 0
    high = len(arr) - 1
    next_biggest = None

    while low <= high:
        # calculate the middle index
        mid = (low + high) // 2

        # check if x is present at mid
        if arr[mid] == timestamp:
            return mid

        # if x is smaller, ignore right half
        elif arr[mid] > timestamp:
            high = mid - 1
            next_biggest = mid

        # if x is larger, ignore left half
        else:
            low = mid + 1

    # if x is not present in the array, return the index of the next biggest number
    if next_biggest is not None:
        return next_biggest
    else:
        return None


def get_frames(folder_path):
    file_list = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".jpg"):
            # extracting the timestamp
            filepath = filename.replace('.jpg', '')
            filepath = float(filepath)
            file_list.append(filepath)
    if len(file_list) == 0:
        return []
    else:
        return file_list


get_frames("outputFrames\\")
