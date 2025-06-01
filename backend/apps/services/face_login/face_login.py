from ..add_cam.add_cam import get_all_cameras
import hnswlib
import threading

def face_login():
    # --- Camera Configuration ---
    camera_urls = get_all_cameras()
    print("camera_urls:",camera_urls)
    camera_frames = {}  # { cam_id: latest_frame }
    camera_locks = {}   # { cam_id: threading.Lock() }
    last_detection_time = {}  # { cam_id: timestamp }

    # --- Face Index ---
    hnsw_index = hnswlib.Index(space='l2', dim=128)
    user_id_map = {}
    index_initialized = False
    index_lock = threading.Lock()

    # --- Camera Thread Function ---
    def capture_camera(cam_id, url):
        cap = None
        while True:
            if cap is None or not cap.isOpened():
                cap = cv2.VideoCapture(url)
                if not cap.isOpened():
                    print(f"[ERROR] Failed to open {cam_id}")
                    time.sleep(5)
                    continue

            ret, frame = cap.read()
            if not ret:
                print(f"[WARNING] No frame from {cam_id}")
                time.sleep(2)
                continue

            with camera_locks[cam_id]:
                camera_frames[cam_id] = frame

            time.sleep(1)  # lower frame grab rate

    # --- Start Threads ---
    def start_all_camera_threads():
        for cam_id, url in camera_urls.items():
            camera_frames[cam_id] = None
            camera_locks[cam_id] = threading.Lock()
            last_detection_time[cam_id] = 0
            threading.Thread(target=capture_camera, args=(cam_id, url), daemon=True).start()

    # --- Build Face Index ---
    def build_index(db: Session):
        global index_initialized, user_id_map, hnsw_index
        with index_lock:
            # Optional: Only active users
            users = db.query(User).filter(User.is_active == True).limit(100_000).all()

            vectors, ids = [], []
            user_id_map.clear()

            for user in users:
                try:
                    enc = np.array(json.loads(user.face_encoding))
                    if enc.shape == (128,):
                        vectors.append(enc)
                        ids.append(user.id)
                        user_id_map[user.id] = user
                except Exception as e:
                    print(f"[build_index] Error for user {user.id}: {e}")

            if vectors:
                hnsw_index.init_index(max_elements=1_500_000, ef_construction=200, M=48)
                hnsw_index.add_items(np.array(vectors), ids)
                hnsw_index.set_ef(100)
                index_initialized = True
                print(f"[INDEX] Built for {len(vectors)} users.")
            else:
                print("[INDEX] No valid users.")
                index_initialized = False

#    data = get_all_cameras()
#    print("data-in-face-login:",data)
#    return get_all_cameras()
