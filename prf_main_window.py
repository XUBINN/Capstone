from PyQt5.QtWidgets import QWidget, QTableWidgetItem
from PyQt5 import uic
from database.database_manager import DatabaseController
import time
import datetime
import schedule
import face_recog.face_recognition_knn_custom
import cv2
import os

class Prf_Home(QWidget):
    def __init__(self, parent, logged_user_info):
        super().__init__(parent)
        uic.loadUi('GUI/Prf_Home.ui', self)
        self.editInfoButton.clicked.connect(self.showEditProfile)
        self.openLectButton.clicked.connect(self.showOpenLect)
        self.logged_user_info = logged_user_info
        self.initUI()

    def initUI(self):
        prf_number = self.logged_user_info[0]
        prf_name = self.logged_user_info[1]
        prf_id = self.logged_user_info[2]
        prf_major = self.logged_user_info[4]

        self.nameValueLabel.setText(str(prf_name))
        self.idValueLabel.setText(str(prf_id))
        self.professorNumberValueLabel.setText(str(prf_number))
        self.majorValueLabel.setText(str(prf_major))

    def showEditProfile(self):
        self.editProfileWindow = Prf_EditProfile(None, self.logged_user_info)
        self.editProfileWindow.show()

    def showOpenLect(self):
        self.openLectWindow = Prf_OpenLect(None, self.logged_user_info)
        self.openLectWindow.show()

class Prf_LectInfo(QWidget):
    def __init__(self, parent, logged_user_info):
        super().__init__(parent)
        uic.loadUi('GUI/Prf_LectInfo.ui', self)
        self.database_controller = DatabaseController()
        self.logged_user_info = logged_user_info

        self.selected_row_data = None

        self.checkAttndButton.clicked.connect(lambda: self.showCheckAttnd())
        self.AttndButton.clicked.connect(lambda: self.showAttnd())

        self.initUI()
    
    def initUI(self):
        lect_tb = self.database_controller.get_prf_lect_list(self.logged_user_info)

        row = len(lect_tb)
        self.lect_table.setRowCount(row) # 테이블위젯 행 수 설정
        for i in range(row):                 # 강의 테이블
            self.lect_table.setItem(i, 0, QTableWidgetItem(lect_tb[i][0]))  # 강좌 번호
            self.lect_table.setItem(i, 1, QTableWidgetItem(lect_tb[i][1]))  # 강좌 이름

            self.lect_table.setItem(i, 3, QTableWidgetItem(lect_tb[i][3]))  # 강좌 교수
        print("lect_tb : ", lect_tb)
        #self.lect_table.cellClicked.connect(self.get_lect_attnd(row))
        self.lect_table.cellClicked.connect(lambda row, col: self.get_lect_attnd(row))

    def get_lect_attnd(self, row):
        self.selected_row_data = []
        for col in range(self.lect_table.columnCount()):
            item = self.lect_table.item(row, col)
            if item is not None:
                self.selected_row_data.append(item.text())
            else:
                self.selected_row_data.append("")  # 아이템이 None이면 빈 문자열을 추가
        print('item, row : ', item, row)

    def showCheckAttnd(self):
        self.CheckAttndWindow = Prf_CheckAttnd(None, self.logged_user_info, self.selected_row_data)
        self.CheckAttndWindow.show()
        print('selected_row_data : ', self.selected_row_data)


    def showAttnd(self) :
        lect_num = self.selected_row_data[0]
        # 저장할 디렉토리를 생성하고 현재 시간을 저장할 폴더명으로 사용
        output_directory = 'attnd_dir/' + lect_num + '/' + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '/org'
        #output_directory = 'attnd_dir/' + lect_num + '/' + datetime.datetime.now().strftime('%Y-%m-%d') + '/org'
        attnd_directory = 'attnd_dir/' + lect_num + '/'  + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '/attnd'
        os.makedirs(output_directory, exist_ok=True)
        os.makedirs(attnd_directory, exist_ok=True)
        # 웹캠 열기
        cap = cv2.VideoCapture(0)  # 웹캠 번호 (0은 기본 웹캠을 나타냄)

        # 총 저장할 시간 : 60(1분)
        total_time = 1

        # 1초마다 이미지 저장
        for i in range(total_time):
            # 현재 시간을 문자열로 변환하여 파일명으로 사용
            current_time = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            
            # 프레임 읽기
            ret, frame = cap.read()
            
            if ret:
                # 이미지 저장
                image_filename = os.path.join(output_directory, f'{current_time}.jpg')
                cv2.imwrite(image_filename, frame)
                
                # 1초 대기
                time.sleep(1)
            else:
                print("웹캠에서 프레임을 읽을 수 없습니다.")
                break

        # 웹캠과 윈도우 창 닫기
        cap.release()
        cv2.destroyAllWindows()        
        attnd_dic = face_recog.face_recognition_knn_custom.FaceRecognition(output_directory, attnd_directory, lect_num)

        print(attnd_dic)

class Prf_EditProfile(QWidget):
    def __init__(self, parent, logged_user_info):
        super().__init__(parent)
        uic.loadUi('GUI/Prf_EditProfile.ui', self)
        self.logged_user_info = logged_user_info
        self.initUI()
        self.show()

    def initUI(self):
        prf_number = self.logged_user_info[0]
        prf_name = self.logged_user_info[1]
        prf_id = self.logged_user_info[2]
        prf_major = self.logged_user_info[4]

        self.nameValueLabel.setText(str(prf_name))
        self.idValueLabel.setText(str(prf_id))
        self.professorNumberValueLabel.setText(str(prf_number))
        self.majorValueLabel.setText(str(prf_major))

class Prf_OpenLect(QWidget):
    def __init__(self, parent, logged_user_info):
        super().__init__(parent)
        uic.loadUi('GUI/Prf_OpenLect.ui', self)
        self.database_controller = DatabaseController()
        self.logged_user_info = logged_user_info
        self.applyButton.clicked.connect(lambda: self.open_lect())

    def open_lect(self) :
        lectNum = self.lectNumValue.text().strip()
        lectMajor = self.lectMajorValue.currentText()
        lectName = self.lectNameValue.text().strip()
        if len(lectNum) != 0 and len(lectName) != 0:
            self.database_controller.open_prf_lect(self.logged_user_info, lectNum, lectMajor, lectName)
            self.close()
        else :
            #self.error.setText("Please input all fields.")
            print("Please input all fields.")

class Prf_CheckAttnd(QWidget): # 출결조회
    def __init__(self, parent, logged_user_info, selected_row_data):
        super().__init__(parent)
        uic.loadUi('GUI/Prf_CheckAttnd.ui', self)
        self.database_controller = DatabaseController()

        self.logged_user_info = logged_user_info
        self.selected_row_data = selected_row_data

        self.attnd_list = self.database_controller.get_prf_attnd_list(self.selected_row_data)
        print(self.attnd_list)
        print(logged_user_info)
        self.initUI()

    def initUI(self):
        self.lect_num.setText(self.selected_row_data[0])
        self.lect_name.setText(self.selected_row_data[1])
        self.lect_prf_name.setText(self.logged_user_info[1])
        self.lect_major.setText(self.selected_row_data[3])

        row = len(self.attnd_list)
        self.lect_table.setRowCount(row) # 테이블위젯 행 수 설정

        for i in range(row):                 # 출결 테이블
            self.lect_table.setItem(i, 0, QTableWidgetItem(str(self.attnd_list[i][0])))  # 학번
            self.lect_table.setItem(i, 1, QTableWidgetItem(str(self.attnd_list[i][2])))  # 출결 날짜
            self.lect_table.setItem(i, 2, QTableWidgetItem(str(self.attnd_list[i][3])))  # 출결 시간
            if 1 == self.attnd_list[i][4] : # 출결 상태
                self.lect_table.setItem(i, 3, QTableWidgetItem('O'))
            elif 0 == self.attnd_list[i][4] :
                self.lect_table.setItem(i, 3, QTableWidgetItem('X'))