# 회원가입 화면!
import base64

from PyQt5.QtWidgets import QMainWindow, QLabel
from PyQt5.QtCore import QThread, pyqtSignal, QEvent
from PyQt5 import QtGui, QtCore
from PyQt5 import uic
import cv2
from PIL import Image
import io
import os

def clickable(widget): # QLabel 클릭 이벤트
    class Filter(QLabel):
        clicked = pyqtSignal()

        def eventFilter(self, obj, event):
        
            if obj == widget:
                if event.type() == QEvent.MouseButtonRelease:
                    if obj.rect().contains(event.pos()):
                        self.clicked.emit()
                        return True
            return False
    filter = Filter(widget)
    widget.installEventFilter(filter)
    return filter.clicked

class RegistrationWindow(QMainWindow) :
    def __init__(self, controller):
        super().__init__()
        uic.loadUi('GUI/RegistrationForm.ui', self)
        self.controller = controller

        self.current_face = None
        self.face_thread = FaceIdThread()
        self.camera_stat.setText("촬영 중인 얼굴 : None")

        self.dup_check_button.clicked.connect(self.dup_check)

        self.take_picture_button.clicked.connect(self.face_thread.face_id)
        
        self.camera_capture_button.clicked.connect(lambda: self.face_thread.face_id_save(self.current_face, user_number = self.number_input.text().strip()))
        self.register_button.clicked.connect(self.signup_function) # 회원가입 버튼 클릭 시
        self.pushButton.clicked.connect(self.back) # 뒤로가기 버튼. 이름 바꿀 것!
        self.face_thread.change_pixmap_signal.connect(self.update_camera_label)
        self.face_thread.change_front_pixmap_signal.connect(self.update_front_camera_label)
        self.face_thread.change_right_pixmap_signal.connect(self.update_right_camera_label)
        self.face_thread.change_left_pixmap_signal.connect(self.update_left_camera_label)

        clickable(self.std_face_front).connect(self.current_face_front)
        clickable(self.std_face_right).connect(self.current_face_right)
        clickable(self.std_face_left).connect(self.current_face_left)
        '''
        self.face_thread = FaceIdThread()
        self.face_thread.change_pixmap_signal.connect(self.update_camera_label)
        self.face_thread.start()
        '''

    def current_face_front(self):
        self.current_face = 'front'
        print('Front Clicked')
        self.camera_stat.setText("촬영할 얼굴 : Front")
        self.front_label.setStyleSheet("Color : red") #글자색 변환
        self.right_label.setStyleSheet("Color : black") #글자색 변환
        self.left_label.setStyleSheet("Color : black") #글자색 변환

    def current_face_right(self):
        self.current_face = 'right'
        print('Right Clicked')
        self.camera_stat.setText("촬영할 얼굴 : Right")
        self.front_label.setStyleSheet("Color : black") #글자색 변환
        self.right_label.setStyleSheet("Color : red") #글자색 변환
        self.left_label.setStyleSheet("Color : black") #글자색 변환

    def current_face_left(self):
        self.current_face = 'left'
        print('Left Clicked')
        self.camera_stat.setText("촬영할 얼굴 : Left")
        self.front_label.setStyleSheet("Color : black") #글자색 변환
        self.right_label.setStyleSheet("Color : black") #글자색 변환
        self.left_label.setStyleSheet("Color : red") #글자색 변환

    def update_camera_label(self, pixmap):
        self.camera_label.setPixmap(pixmap)

    def update_front_camera_label(self, pixmap):
        self.std_face_front.setPixmap(pixmap)

    def update_right_camera_label(self, pixmap):
        self.std_face_right.setPixmap(pixmap)

    def update_left_camera_label(self, pixmap):
        self.std_face_left.setPixmap(pixmap)
        
    def signup_function(self) :
        role = 'Student' if self.student_radio.isChecked() else ('Professor' if self.professor_radio.isChecked() else None)
        user_name = self.name_input.text().strip()
        user_number = self.number_input.text().strip()
        user_id = self.id_input.text().strip()
        user_password = self.password_input.text().strip()
        user_major = self.major_input.currentText()
        user_images = FaceIdThread().images
        print(len(user_images))

        if role == 'Professor' :
            if role and len(user_name) != 0 and len(user_number) != 0 and len(user_id) != 0 and len(user_password) != 0:
                self.registration_groupBox.setTitle("")
                self.controller.do_signup(role, user_name, user_number, user_id, user_password, user_major)

            else : 
                self.registration_groupBox.setTitle("Please fill in all inputs.")
                print("Please fill in all inputs.")

        elif role == 'Student' :
            if role and len(user_name) != 0 and len(user_number) != 0 and len(user_id) != 0 and len(user_password) != 0:
                self.registration_groupBox.setTitle("")
                self.controller.do_signup(role, user_name, user_number, user_id, user_password, user_major, user_images)

            else : 
                self.registration_groupBox.setTitle("Please fill in all inputs.")
                print("Please fill in all inputs.")


    def back(self) :
        self.controller.show_login(True)

    def dup_check(self):
        role = 'Student' if self.student_radio.isChecked() else ('Professor' if self.professor_radio.isChecked() else None)
        user_id = self.id_input.text()

        # 구분 체크, 아이디 입력 여부 체크
        if role and user_id.strip(): # 아이디에 입력한 공백을 제거 후에 남는 문자열이 있으면 true
            result = self.controller.dup_id_check(role, user_id)
            if result:
                self.dup_id_label.setText('사용가능')
            else:
                self.dup_id_label.setText('사용불가')
        else:
            self.dup_id_label.setText('구분/ID 입력')
    '''
    def face_id(self):
        self.face_thread.start_camera()

    def face_id_save(self):
        self.face_thread.capture_image()
    '''

class FaceIdThread(QThread):
    change_pixmap_signal = pyqtSignal(QtGui.QPixmap)
    change_front_pixmap_signal = pyqtSignal(QtGui.QPixmap)
    change_right_pixmap_signal = pyqtSignal(QtGui.QPixmap)
    change_left_pixmap_signal = pyqtSignal(QtGui.QPixmap)
    images = [0, 0, 0]

    def __init__(self):
        super().__init__()
        self.stopped = False
        self.cap = cv2.VideoCapture(0)

    def stop(self):
        self.stopped = True

    def run(self):
        self.start_camera()

        while not self.stopped:
            ret, self.frame = self.cap.read()
            if ret:
                img = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
                h, w, c = img.shape
                qImg = QtGui.QImage(img.data, w, h, w * c, QtGui.QImage.Format_RGB888)
                pixmap = QtGui.QPixmap.fromImage(qImg)

                p = pixmap.scaled(int(w * 400 / h), 400, QtCore.Qt.IgnoreAspectRatio)
                self.change_pixmap_signal.emit(p)

    def start_camera(self):
        self.stopped = False
        self.cap = cv2.VideoCapture(0)

    def face_id_save(self, current_face, user_number):
        buffer = io.BytesIO()

        print(f"user_number: {user_number}")
        print(f"current_face: {current_face}")

        if len(user_number) == 0 or current_face is None:
            print("user_number or current_face is None")
            return

        else :
            if self.cap.isOpened():
                img = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
                h, w, c = img.shape
                qImg = QtGui.QImage(img.data, w, h, w * c, QtGui.QImage.Format_RGB888)
                pixmap = QtGui.QPixmap.fromImage(qImg)
                p = pixmap.scaled(int(w * 80 / h), 80, QtCore.Qt.KeepAspectRatio)

                print(user_number)

                save_directory = 'face_recog/knn_examples/train/'+user_number + '/'
                os.makedirs(save_directory, exist_ok=True)  # 디렉토리만 생성
                cv2.imwrite(os.path.join(save_directory, current_face+'.jpg'), self.frame) 
                with open(save_directory+current_face+'.jpg', 'rb') as f:
                    img_str = f.read()

                if current_face == 'front':
                    self.change_front_pixmap_signal.emit(p)
                    self.images[0] = img_str
                elif current_face == 'right':
                    self.change_right_pixmap_signal.emit(p)
                    self.images[1] = img_str
                elif current_face == 'left':
                    self.change_left_pixmap_signal.emit(p)
                    self.images[2] = img_str

                print('captured')
                self.cap.release()
                self.stop()

    def face_id(self):
        self.start_camera()
        self.start()

    '''
    def face_id_save(self):
        self.capture_image()
    '''