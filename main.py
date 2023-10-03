# 얘를 실행하시오.

from PyQt5.QtWidgets import QApplication
from app_manager import AppController
import sys

if __name__ == '__main__':
    app = QApplication(sys.argv)
    controller = AppController()
    controller.show_login()
    sys.exit(app.exec_())