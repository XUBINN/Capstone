# 로그인 화면! (로그인, 회원가입)

from PyQt5.QtWidgets import QMainWindow
from PyQt5 import uic

class LoginWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        uic.loadUi('GUI/LoginForm.ui', self)
        self.controller = controller

        self.loginButton.clicked.connect(self.login)
        self.registerLinkButton.clicked.connect(self.open_signup)

    def login(self): # 로그인 버튼 클릭
        id = self.idInput.text().strip()
        password = self.passwordInput.text().strip()
   
        role = 'Student' if self.studentRadioButton.isChecked() else ('Professor' if self.professorRadioButton.isChecked() else None)
        if role and len(id) != 0 and len(password) != 0:
            self.controller.do_login(role, id, password)
        else :
            self.error.setText("Please input all fields.")

    def open_signup(self): # 회원가입 버튼 클릭
        #print("Registration Button")
        self.controller.show_signup()