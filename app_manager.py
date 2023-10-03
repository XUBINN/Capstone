# 모듈들 관리하는 곳!!

from login_window import LoginWindow
from main_window import MainWindow
from register_window import RegistrationWindow
from database.database_manager import DatabaseController

class AppController:
    def __init__(self):
        self.login_window = LoginWindow(self)
        self.main_window = None
        self.register_window = RegistrationWindow(self)
        self.database_controller = DatabaseController()


    def show_login(self, from_signup=False): # from_signup : 회원가입 창에서 넘어왔는지
            self.login_window = LoginWindow(self) # 다른 창에서 로그인 창으로 넘어갈 때 로그인 창 초기화
            self.login_window.show()
            if from_signup:
                self.register_window.hide()


    def do_login(self, role, id, password):
        logged_user_info = self.database_controller.check_login_db(role, id, password)

        if logged_user_info:
            print("Valid input")
            self.main_window = MainWindow(self, role, logged_user_info)
            self.main_window.show()
            self.login_window.hide()
        else:
            self.login_window.error.setText("Invalid input")
            print("Invalid input")        


    def do_logout(self):
        print("Logout!!")
        self.login_window = LoginWindow(self) 
        self.login_window.show()
        self.main_window.hide()


    def show_signup(self) :
        print("Registration Form")
        self.register_window = RegistrationWindow(self)
        self.register_window.show()
        self.login_window.hide()


    def do_signup(self, role, user_name, user_number, user_id, user_password, user_major, user_images) :
        signed_user_info = self.database_controller.add_user_info(role, user_name, user_number, user_id, user_password, user_major, user_images)
        if signed_user_info :
            print("show_login")
            self.login_window.show()
            self.register_window.hide()


    def dup_id_check(self, role, id):
        if self.database_controller.check_dup_id(role, id):
            return True
        else:
            return False