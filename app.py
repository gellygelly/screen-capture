import os
import cv2
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from datetime import datetime
import av
from PIL import Image
import pandas as pd

# 전역 변수
VIDEO_DIR = 'StreamlitRec/videos/'
IMAGE_DIR = 'StreamlitRec/images/'

is_recording = False
frames = []
save_interval = None
video_save_directory = None

def check_directory(directory_path, visible=True):
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        if visible:
            st.success(f"저장 경로: {directory_path}")
    else:
        if visible:
            st.success(f"저장 경로: {directory_path}")

# sidebar video file list
def show_files(directory_path, use_container_width=True):
    st.write('**파일 목록**')
    if os.path.exists(directory_path):
        files = os.listdir(directory_path)
        df = pd.DataFrame(files, columns=['File Name'])
        st.dataframe(df, use_container_width=use_container_width)
            # st.write(file)
    else:
        st.error('선택한 디렉토리를 찾을 수 없습니다.')


def start_recording():
    global is_recording
    is_recording = True
    print('start recoding', is_recording)


def save_video():
    global frames
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    width, height = frames[0].shape[1], frames[0].shape[0]
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d_%H-%M-%S")
    output_path = video_save_directory + f"{current_time}_output.mp4"
    out = cv2.VideoWriter(output_path, fourcc, 30, (width, height))

    for frame in frames:
        out.write(frame)

    out.release()
    frames = []


# 웹캠에 ROI 영역 표시
def video_frame_callback(video_frame: av.VideoFrame) -> av.VideoFrame:
    global frames, save_interval, video_save_directory
    # print('video_frame_callback', save_interval, is_recording)

    if is_recording:
        if save_interval is not None: 
            if len(frames) > save_interval:
                save_video()
            else:
                frames.append(video_frame.to_ndarray(format="bgr24"))
        else:
            frames.append(video_frame.to_ndarray(format="bgr24"))

    img = video_frame.to_ndarray(format='bgr24')
    cv2.rectangle(img, (1, 50), (50, 200), (255, 0, 0), 2) # ROI TODO 좌표 수정
    # cv2.rectangle(img, (1, 50), (50, 200), (255, 0, 0), 2) # chip guide bbox TODO 좌표 수정
    # cv2.rectangle(img, (1, 50), (50, 200), (255, 0, 0), 2) # card guide bbox TODO 좌표 수정
    img = av.VideoFrame.from_ndarray(img, format='bgr24')

    return img

def on_video_ended_callback():
    print('on_video_ended_callback')
    # if len(frames)>0:
    global frames
    print('save video:', len(frames))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    width, height = frames[0].shape[1], frames[0].shape[0]
    # out = cv2.VideoWriter(self.output_path, fourcc, 30.0, (640, 480))
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d_%H-%M-%S")
    output_path = video_save_directory + f"{current_time}_output.mp4"
    out = cv2.VideoWriter(output_path, fourcc, 30, (width, height))

    for frame in frames:
        out.write(frame)

    out.release()
    print('저장 완료:', len(frames), output_path, width, height)
    global is_recording
    is_recording = False
    frames = []

###########################################################################
# Streamlit App #
###########################################################################
    
def main():
    global save_interval, is_recording, video_save_directory
    ## Setting 
    with st.sidebar:
        st.write('동영상 녹화 설정')
        # 녹화중일 때 저장 주기 선택 불가 설정
        if 'disable_selectbox' not in st.session_state:
            st.session_state.disable_selectbox = False

        if is_recording:
            st.session_state.disable_selectbox = True
        else:
            st.session_state.disable_selectbox = False
        
        # 동영상 저장 주기 select box
        save_interval_selectbox = st.sidebar.selectbox(
            label="동영상 자동 저장 주기",
            options=('자동 저장 안 함', 'test', '5 mins', '10 mins', '15 mins', '30 mins', '1 hours', '4 hours'),
            placeholder='동영상 자동 저장 주기를 선택하세요.',
            disabled=st.session_state.disable_selectbox)
        
        if save_interval_selectbox == '자동 저장 안 함':
            save_interval = None
        elif save_interval_selectbox == 'test': # 2초
            save_interval = 2*30 # 30fps
        elif save_interval_selectbox == '5 mins':
            save_interval = 300*30 # sec * 30fps
        elif save_interval_selectbox == '10 mins':
            save_interval = 600*30
        elif save_interval_selectbox == '15 mins':
            save_interval = 900*30
        elif save_interval_selectbox == '30 mins':
            save_interval = 1800*30
        elif save_interval_selectbox =='1 hours': # 1 hours
            save_interval = 3600*30
        elif save_interval_selectbox =='4 hours':
            save_interval = 3600*30*4
        

        # 녹화 동영상 저장 디렉토리 선택
        now = datetime.now()
        today_folder = now.strftime("%Y%m%d")
        video_save_directory = VIDEO_DIR + today_folder+'/'
        # video_save_directory = st.text_input("녹화 파일을 저장할 디렉토리 경로를 입력하세요:", value='C:/records/')
        check_directory(video_save_directory)
        
        st.divider()

        # 녹화한 동영상 파일 리스트
        show_files(video_save_directory, use_container_width=False)

    ## Main Page
    st.title("Screen Capture For YOLOv9 Labeling")

    st.header('1. 동영상 녹화', divider='orange')
    st.write('**사용법**')
    st.write('1. "START" 버튼을 클릭하여 카메라 화면이 정상적으로 잘 나오는지 확인해 주세요.')
    st.write('2. 빨간색 박스 영역에 테이블의 칩, 카드를 올려두는 영역이 포함되도록 카메라 위치를 조정해 주세요.')
    st.write('3. 동영상 자동 저장 주기를 선택해 주세요. "자동 저장 안 함"을 선택할 시, 수동으로 STOP 버튼을 눌러야 동영상이 저장됩니다.')
    st.write('4. 녹화 파일을 저장할 디렉토리 경로를 입력해주세요.')
    st.write('5. "녹화 시작" 버튼을 누를 시 녹화를 시작할 수 있습니다.')
    st.write('6. "STOP" 버튼을 누르면 즉시 녹화가 종료됩니다.')

    st.divider()
    st.write('**카메라 셋팅**')

    # video stream
    webrtc_ctx = webrtc_streamer(
        key="livecam",
        rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
        },
        mode=WebRtcMode.SENDRECV,
        video_frame_callback=video_frame_callback,
        on_video_ended=on_video_ended_callback,
        sendback_audio=False,
        async_processing=True,)

    st.divider()

    st.write('**녹화**')
    col1, col2 = st.columns(2)

    with col1:
        if st.button("녹화 시작"):
            st.session_state.disable_selectbox = True
            start_recording()
    
    with col2:
        if is_recording == True:
            st.success("녹화가 시작되었습니다.")
        else: 
            st.info("녹화 시작 버튼을 눌러 녹화를 시작하세요.")

    st.write('\n')
            
    st.header('2. 동영상 프레임 추출', divider='orange')

    #프레임 추출 간격 선택
    st.write('\n')
    frame_extraction_interval = st.select_slider(
    "프레임 추출 간격 선택(단위: n프레임 마다)",
    options=[
        "10",
        "15",
        "30",
        "60"
    ],)

    date_folder_list = os.listdir(VIDEO_DIR)
    video_files_df = []
    
    for date_folder in date_folder_list:
        video_files = os.listdir(VIDEO_DIR+date_folder)
        if len(video_files) != 0:
            for video_file in video_files:
                check_directory(IMAGE_DIR + date_folder +'/' + video_file, visible=False)
                the_number_of_files = len(os.listdir(IMAGE_DIR + date_folder +'/' + video_file))
                is_file_exists = 'O' if the_number_of_files > 0 else 'X'
                
                video_files_df.append([date_folder, video_file, is_file_exists, the_number_of_files])
        else:
            video_files_df.append([date_folder, None, None, None])

    st.write('**파일 목록**')
    columns = ['Date', 'File name', 'Frame Extraction Status', 'File Counts']
    df = pd.DataFrame(video_files_df, columns=columns)
    event = st.dataframe(data=df, on_select="rerun", selection_mode="multi-row")
    
    if st.button('동영상 프레임 추출 시작'):
        if len(event.selection['rows']):
            rows = event.selection['rows']
            process_bar = st.progress(0)
            for idx, row in enumerate(rows):
                date_folder = df.iloc[row]['Date']
                video_file_name = df.iloc[row]['File name']
                try:
                    video_path = VIDEO_DIR + date_folder + '/' + video_file_name
                    cap = cv2.VideoCapture(video_path)
                    current_frame = 0
                    process_bar.progress((idx+1) / len(rows), text='Operation in progress. Please wait.')
                    st.info(f'동영상 프레임 추출이 시작되었습니다. {video_path}')
                    while cap.isOpened():
                        success, frame = cap.read()
                        if success:
                            if current_frame % int(frame_extraction_interval[0]) == 0: 
                                cvt_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                image = Image.fromarray(cvt_frame) # numpy to PIL Image
                                image_directory =  IMAGE_DIR + date_folder +'/' + video_file_name
                                image_path = image_directory +'/'+ video_file_name + "_" + str(current_frame) + ".jpg"
                                with open(image_path, mode='wb') as f:
                                    image.save(f) 
                        else:
                            break
                        current_frame += 1
                    cap.release()
                except TypeError:
                    st.error('동영상 파일이 존재하지 않습니다.')
        else: 
            st.error('프레임 추출을 진행할 비디오 파일을 체크해주세요.')

################################################################

if __name__ == '__main__':
    main()