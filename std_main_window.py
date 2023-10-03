from PyQt5.QtWidgets import QWidget, QTableWidgetItem
from PyQt5 import uic
from PyQt5.QtGui import QPixmap
from database.database_manager import DatabaseController
import base64

class Std_Home(QWidget):
    def __init__(self, parent, logged_user_info):
        super().__init__(parent)
        uic.loadUi('GUI/Std_Home.ui', self)
        self.editInfoButton.clicked.connect(self.showEditProfile)
        self.logged_user_info = logged_user_info
        self.initUI()

    def initUI(self):
        std_number = self.logged_user_info[0]
        std_name = self.logged_user_info[1]
        std_id = self.logged_user_info[2]
        std_major = self.logged_user_info[4]
        std_face_id = self.logged_user_info[5]
        print("std_face_id:", std_face_id)

        print("Data Type:", type(std_face_id))

        self.nameValueLabel.setText(str(std_name))
        self.idValueLabel.setText(str(std_id))
        self.studentNumberValueLabel.setText(str(std_number))
        #self.faceId.setText(str(std_face_id))
        self.majorValueLabel.setText(str(std_major))

        '''
        # 이미지 데이터를 QPixmap으로 변환
        pixmap = self.loadImageFromData(std_face_id)
        # QLabel에 QPixmap 설정
        self.faceId.setPixmap(pixmap)
        '''

    def showEditProfile(self):
        self.editProfileWindow = Std_EditProfile(None, self.logged_user_info)
        self.editProfileWindow.show()

    def loadImageFromData(self, image_data):
        # base64 디코딩을 통해 이미지 데이터를 bytes로 변환
        image_bytes = base64.b64decode(image_data)

        # bytes를 QPixmap으로 변환
        pixmap = QPixmap()
        pixmap.loadFromData(image_bytes)

        return pixmap
    
class Std_CourseInfo(QWidget): # 수강 정보
    def __init__(self, parent, logged_user_info):
        super().__init__(parent)
        uic.loadUi('GUI/Std_CourseInfo.ui', self)
        self.database_controller = DatabaseController()
        self.checkAttndButton.clicked.connect(self.showCheckAttnd)
        self.logged_user_info = logged_user_info
        self.initUI()

    def initUI(self):
        lect_tb = self.database_controller.get_std_lect_table(self.logged_user_info)

        row = len(lect_tb)
        self.lect_table.setRowCount(row)
        for i in range(row):                 # 강의 테이블
            self.lect_table.setItem(i, 0, QTableWidgetItem(lect_tb[i][0]))  # 강좌 번호
            self.lect_table.setItem(i, 1, QTableWidgetItem(lect_tb[i][1]))  # 강좌 이름
            self.lect_table.setItem(i, 2, QTableWidgetItem(lect_tb[i][2]))  # 강좌 교수

    def showCheckAttnd(self):
        self.CheckAttndWindow = Std_CheckAttnd(None, self.logged_user_info)
        self.CheckAttndWindow.show()

# 개설된 전체 강좌 조회
# & 테이블위젯 클릭한 상태에서 수강신청 버튼 누르면 수강신청 가능.
class Std_Enrollment(QWidget):
    def __init__(self, parent, logged_user_info):
        super().__init__(parent)
        uic.loadUi('GUI/Std_Enrollment.ui', self)
        self.database_controller = DatabaseController()
        self.logged_user_info = logged_user_info

        self.selected_row_data = None
        
        self.EnrollmentButton.clicked.connect(lambda: self.Enrollment())
        self.initUI()

    def initUI(self) :
        all_lect = self.database_controller.get_all_lect_list()

        self.lect_table.setRowCount(len(all_lect)) # 시간 되면 강의 시간도 추가
        for row_index, (lect_num, lect_name, _, major, prf_name) in enumerate(all_lect):
            self.lect_table.setItem(row_index, 0, QTableWidgetItem(lect_num))  # 과목번호
            self.lect_table.setItem(row_index, 1, QTableWidgetItem(lect_name))  # 교과목명
            self.lect_table.setItem(row_index, 2, QTableWidgetItem(prf_name))  # 담당교수
            #self.lect_table.setItem(row_index, 3, QTableWidgetItem()  # 강의시간
            self.lect_table.setItem(row_index, 4, QTableWidgetItem(major))  # 개설학과

        self.lect_table.cellClicked.connect(self.get_enroll_lect)

    def get_enroll_lect(self, row):
        self.selected_row_data = []
        item = self.lect_table.item(row, 0) # 클릭한 행에서 0번째 값 (과목번호)
        self.selected_row_data.append(item.text())
        
    def Enrollment(self):
        if self.selected_row_data:
            lect_num = self.selected_row_data[0] # 과목번호 가져오기
            self.database_controller.enroll_std_lect(self.logged_user_info, lect_num)
            print("selected lect_num:", lect_num)
        else:
            print("No lect selected.")

class Std_EditProfile(QWidget):
    def __init__(self, parent, logged_user_info):
        super().__init__(parent)
        uic.loadUi('GUI/Std_EditProfile.ui', self)
        self.logged_user_info = logged_user_info
        self.initUI()
        self.show()

    def initUI(self):
        std_number = self.logged_user_info[0]
        std_name = self.logged_user_info[1]
        std_id = self.logged_user_info[2]
        #std_face_id = self.logged_user_info[4]
        std_major = self.logged_user_info[5]

        self.nameValueLabel.setText(str(std_name))
        self.idValueLabel.setText(str(std_id))
        self.studentNumberValueLabel.setText(str(std_number))
        #self.faceId.setText(str(std_face_id))
        self.majorValueLabel.setText(str(std_major))

class Std_CheckAttnd(QWidget): # 출결조회
    def __init__(self, parent, logged_user_info):
        super().__init__(parent)
        uic.loadUi('GUI/Std_CheckAttnd.ui', self)
        self.database_controller = DatabaseController()
        self.logged_user_info = logged_user_info

        attnd_list = self.database_controller.get_attnd_list(logged_user_info)
        self.lect_combo.addItems(attnd_list)

        self.lect_combo.currentTextChanged.connect(self.initUI)
        self.show()

    def initUI(self):
        attnd_name = self.lect_combo.currentText()
        if(attnd_name!="---강좌 선택---") :
            attnd_tb = self.database_controller.get_attnd_table(self.logged_user_info, attnd_name)

            attnd_table = attnd_tb[2]
            row = len(attnd_table)
            self.lect_table.setRowCount(row)

            self.lect_num.setText(attnd_tb[0])    # 강좌번호
            self.lect_prf.setText(attnd_tb[1])    # 교수명

            self.lect_table.setRowCount(row)

            for i in range(row):                 # 출결 테이블
                self.lect_table.setItem(i, 0, QTableWidgetItem(attnd_table.iloc[i, 0]))  # 강좌 날짜
                self.lect_table.setItem(i, 1, QTableWidgetItem(attnd_table.iloc[i, 1]))  # 강좌 시간
                if 1 == attnd_table.iloc[i, 2]:                                          # 출결
                    self.lect_table.setItem(i, 2, QTableWidgetItem('O'))
                elif 0 == attnd_table.iloc[i, 2]:
                    self.lect_table.setItem(i, 2, QTableWidgetItem('X'))
            
        else :
            print("강좌를 선택하세요.")

