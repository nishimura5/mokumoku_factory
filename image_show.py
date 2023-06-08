import time
import cv2

def loop(que_in, que_out):
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if cap.isOpened() is False:
      raise IOError

    if isinstance(cap.get(cv2.CAP_PROP_CONVERT_RGB), float):
      cap.set(cv2.CAP_PROP_CONVERT_RGB, 0.0)
    else:
      cap.set(cv2.CAP_PROP_CONVERT_RGB, False)

    cap.set(cv2.CAP_PROP_BUFFERSIZE, 4)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    print('start')

    que_out.put('stand by')
    while True:
        ret, frame = cap.read()
        cv2.imshow('cap', frame)
        if cv2.waitKey(1) == ord('q'):
            break

        if que_in.qsize() > 1:
            print(que_in.get())
        que_out.put('GO')
    cap.release()
    cv2.destroyAllWindows()
