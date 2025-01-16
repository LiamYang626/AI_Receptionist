from deep_sort_realtime.deepsort_tracker import DeepSort


def initialize_deepsort():
    return DeepSort(max_age=30, n_init=3, nms_max_overlap=1.0)


def track_objects(deepsort, detections, frame):
    return deepsort.update_tracks(detections, frame=frame)
