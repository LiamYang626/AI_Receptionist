def detect_people(model, frame):
    results = model(frame)
    detections = []
    for result in results:
        for detection in result.boxes.data.tolist():
            x1, y1, x2, y2, confidence, class_id = detection
            if confidence > 0.5 and int(class_id) == 0:  # Only process people
                width = x2 - x1
                height = y2 - y1
                bbox = [x1, y1, width, height]
                detections.append((bbox, confidence, 'person'))
    return detections
