from PyQt5.QtWidgets import QMainWindow, QWidget, QLabel, QApplication
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, QEvent
from std_main_window import *
from prf_main_window import *

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

class MainWindow(QMainWindow):
    def __init__(self, controller, role, logged_user_info):
        super().__init__()
        uic.loadUi('GUI/MainPage.ui', self)
        self.controller = controller
        self.logged_user_info = logged_user_info

        if role == 'Student':
            self.setup_student_ui()
        elif role == 'Professor':
            self.setup_professor_ui()

        clickable(self.logoutLabel).connect(self.logout)
        clickable(self.exitLabel).connect(self.exit)

    def logout(self): # 로그아웃 버튼 클릭
        self.controller.do_logout()

    def exit(self):  # 종료 버튼 클릭
        #self.controller.close_window()
        self.close()
        
    # 학생 탭 화면 불러오기
    def setup_student_ui(self):
        self.mainTabWidget.addTab(Std_Home(self, self.logged_user_info), '학생 홈')
        self.mainTabWidget.addTab(Std_CourseInfo(self, self.logged_user_info), '출결조회')
        self.mainTabWidget.addTab(Std_Enrollment(self, self.logged_user_info), '수강신청')

    # 교수 탭 화면 불러오기
    def setup_professor_ui(self):
        self.mainTabWidget.addTab(Prf_Home(self, self.logged_user_info), '교수 홈')
        self.mainTabWidget.addTab(Prf_LectInfo(self, self.logged_user_info), '출결관리')
        #self.mainTabWidget.addTab(Prf_EditProfile(self, self.logged_user_info), '개인정보수정')
