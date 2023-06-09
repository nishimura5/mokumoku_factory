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
    print('start')

    ## 出力する動画の設定
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = 10
    fmt = cv2.VideoWriter_fourcc(*'MP4V')
    out = cv2.VideoWriter('./dst.mp4', fmt, fps, (width, height))

    print(width, height, fps)

    que_out.put('stand by')
    now_time = time.time()
    while True:
        ret, frame = cap.read()

        out.write(frame)
        if que_in.qsize() > 0:
            got_msg = que_in.get()
            if got_msg == 'QUIT':
                break
            elif got_msg == 'A':
                pict = cv2.imread('./img/a.jpg')
                cv2.imshow('cap', pict)
                cv2.waitKey(1)

        fps = 1 / (time.time() - now_time)
        fps_str = f"fps:{fps:.1f}"
        now_time = time.time()
        que_out.put(fps_str)

    print('break')
    cap.release()
    out.release()
    que_out.put('QUIT')
#    cv2.destroyAllWindows()
