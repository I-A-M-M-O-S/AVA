# Pylon observations derived from one source image.
# header.stamp equals the source-image measurement stamp, not callback receipt
# time. header.frame_id names the REP-103 vehicle frame in which every bearing
# and optional range is expressed (normally base_link). An empty observations
# array is a valid, explicit "no detections" result for that image.

std_msgs/Header header
PylonObservation[] observations
