## 데베 모듈들 관리
import sqlite3
import os
import pandas as pd
from PyQt5.QtWidgets import QMessageBox

class DatabaseController:
    def __init__(self):
        self.conn = None
        self.cur = None

    def open_conn(self):
        print("open_conn")
        self.conn = sqlite3.connect("database/Attendance_System.db")
        self.cur = self.conn.cursor()

    def close_conn(self):
        if self.conn:
            self.conn.close()
            print("Database Disconnected!")


    def check_dup_id(self, role, id):
        self.open_conn()
        query = ""
        if role == 'Student':
            query = 'SELECT COUNT(*) FROM STD_INFO_TB WHERE STD_ID =\'' + id + "\'"
        elif role == 'Professor':
            query = 'SELECT COUNT(*) FROM PRF_INFO_TB WHERE PRF_ID =\'' + id + "\'"

        self.cur.execute(query)
        result_id = self.cur.fetchone()
        if result_id[0] == 1:
            print("dup id")
            self.close_conn()
            return False
        else:
            print("correct id")
            self.close_conn()
            return True

    def check_login_db(self, role, id, password):
        self.open_conn()
        print("Database Connected!")

        query = ""
        db_role = 'STD' if role == 'Student' else ('PRF' if role == 'Professor' else None)

        query = f'SELECT * FROM {db_role}_INFO_TB WHERE {db_role}_ID =\'' + id + "\' AND " + f'{db_role}_PW =\'' + password + "\'"

        self.cur.execute(query)
        user_info = self.cur.fetchone()

        if user_info:
            print("Successfully logged in.")
            self.close_conn()
            return user_info  # 유저 정보(학번, 이름, 아이디, 비번, 얼굴) 넘겨주기
        else:
            print("Invalid input")
            self.close_conn()
            return None

    # 회원가입
    def add_user_info(self, role, user_name, user_number, user_id, user_password, user_major, user_images) :
        print(self, role, user_name, user_number, user_id, user_password, user_major)
        self.open_conn()
        print("Database Connected!")
        
        db_role = 'STD' if role == 'Student' else ('PRF' if role == 'Professor' else None)

        try:
            self.cur.execute(f'INSERT INTO {db_role}_INFO_TB ({db_role}_NAME, {db_role}_NUM_PK, {db_role}_ID, {db_role}_PW, {db_role}_MAJOR, {db_role}_FACE_F, {db_role}_FACE_R, {db_role}_FACE_L) VALUES (?,?,?,?,?,?,?,?)',
                             (user_name, user_number, user_id, user_password, user_major, user_images[0], user_images[1], user_images[2]))
            self.conn.commit()
            print('committed!')
            self.conn.close()
            return True
        
        except Exception as e:
            print('Error:', e)
            self.conn.rollback()  # 롤백 처리
            self.close_conn()
            return False


    def get_std_lect_table(self, logged_user_info):
        self.open_conn()
        std_num = logged_user_info[0]  # 학번

        self.cur.execute("select * from STD_REG_TB where STD_NUM_FK = ?", (str(std_num),))
        lect_list = self.cur.fetchall() # 수강정보(학번, 강의번호)

        lect_tb, prf_num = [], []
        for i in range(len(lect_list)):
            self.cur.execute("select * from PRF_LECT_TB where LECT_NUM_PK = ?", (lect_list[i][1],))
            lect_info = self.cur.fetchone()
            lect_tb.append((lect_info[0], lect_info[1]))
            prf_num.append(lect_info[2])

        for i in range(len(prf_num)):
            self.cur.execute("select PRF_NAME from PRF_INFO_TB where PRF_NUM_PK = ?", (prf_num[i], ))
            prf_name = self.cur.fetchone()
            lect_tb[i] = lect_tb[i] + prf_name

        self.close_conn()
        return lect_tb # 강의 리스트(강의번호, 강의명, 교수명)
    
    # 학생 - 수강중인 강좌 목록 불러오기
    def get_attnd_list(self, logged_user_info):
        self.open_conn()
        std_num = logged_user_info[0]  # 학번

        self.cur.execute("select * from STD_REG_TB where STD_NUM_FK = ?", (str(std_num),))
        lect_list = self.cur.fetchall()

        lect_name = []
        for i in range(len(lect_list)):
            self.cur.execute("select LECT_NAME from PRF_LECT_TB where LECT_NUM_PK = ?", (lect_list[i][1],))
            lect_names = self.cur.fetchone()
            lect_name.append(lect_names[0])

        self.close_conn()
        return lect_name

    # 학생 - 출결 목록
    def get_attnd_table(self, logged_user_info, lect_name):
        self.open_conn()
        std_num = logged_user_info[0]  # 학번

        self.cur.execute("select * from PRF_LECT_TB where LECT_NAME = ?", (lect_name,))
        lect_num = self.cur.fetchone() # 강좌 정보(강좌번호, 강좌명, 교번, 개설학과)

        self.cur.execute("select PRF_NAME from PRF_INFO_TB where PRF_NUM_PK = ?", (lect_num[2],))
        prf = self.cur.fetchone() # 교수명

        self.cur.execute("select * from ATTND_TB where STD_NUM_FK = ? and LECT_NUM_FK = ?", (str(std_num), lect_num[0], ))
        attnd = self.cur.fetchall() # 출결 정보(학번, 강좌번호, 출결날짜, 출결시간, 출결상태)
        attnd_frame = pd.DataFrame(attnd)

        lect_tb = (lect_num[0], prf[0], attnd_frame.iloc[:, 2:5]) # 강좌번호, 교수명, 출결테이블

        self.close_conn()
        return lect_tb
    
    # 학생 수강신청 UI - 모든 강의 조회
    def get_all_lect_list(self) :
        self.open_conn()
        self.cur.execute("""
            SELECT PRF_LECT_TB.*, PRF_INFO_TB.PRF_NAME
            FROM PRF_LECT_TB
            INNER JOIN PRF_INFO_TB ON PRF_LECT_TB.PRF_NUM_FK = PRF_INFO_TB.PRF_NUM_PK;
        """)

        result = self.cur.fetchall()
        self.close_conn()
        return result
    
    # logged user 교수가 보유한 강의 테이블
    def get_prf_lect_list(self, logged_user_info) :
        self.open_conn()
        prf_num = logged_user_info[0]

        self.cur.execute("select * from PRF_LECT_TB where PRF_NUM_FK = ?", (str(prf_num),))
        lect_list = self.cur.fetchall() # 강의정보(과목번호, 교과목명, 교번, 개설학과)
        self.close_conn()
        return lect_list
    
    # 교수 강의개설
    def open_prf_lect(self, logged_user_info, lectNum, lectMajor, lectName) :
        self.open_conn()
        
        try:
            self.cur.execute(f'INSERT INTO PRF_LECT_TB (LECT_NUM_PK, LECT_NAME, PRF_NUM_FK, LECT_MAJOR) VALUES (?,?,?,?)', (lectNum, lectName, logged_user_info[0], lectMajor))
            self.conn.commit()

            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle("강의개설 알림")
            msg_box.setText("강의개설이 정상적으로 처리되었습니다.")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()
            
            self.close_conn()
            return True
        
        except Exception as e:
            print('Error:', e)

            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("강의개설 알림")
            msg_box.setText("이미 존재하는 과목번호입니다.")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()

            self.conn.rollback()
            self.close_conn()
            return False
        
    # 교수 - 학생 출결 목록 불러오기
    def get_prf_attnd_list(self, selected_row_data) :
        self.open_conn()

        lect_num = selected_row_data[0]

        self.cur.execute("select * from ATTND_TB where LECT_NUM_FK = ?", (lect_num,))
        attnd_tb = self.cur.fetchall() # 강좌 정보(강좌번호, 강좌명, 교번)

        # attnd_tb는 LECT_NUM_FK가 lect_num인 모든 행을 포함하게 됨

        self.close_conn()
        return attnd_tb
        
    # 수강신청 처리 데이터베이스    
    def enroll_std_lect(self, logged_user_info, lect_num) :
        self.open_conn()
        std_num = logged_user_info[0]  # 학번

        # 중복 확인
        query = "SELECT * FROM STD_REG_TB WHERE STD_NUM_FK = ? AND LECT_NUM_FK = ?"
        self.cur.execute(query, (std_num, lect_num))
        existing = self.cur.fetchone()

        if existing:
            print("이미 수강 중인 강의입니다.")
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("수강신청 알림")
            msg_box.setText("이미 수강 중인 강의는 신청할 수 없습니다.")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()
        else:
            # 중복 아닐 시 데이터베이스에 저장함.
            try:
                query = "INSERT INTO STD_REG_TB (STD_NUM_FK, LECT_NUM_FK) VALUES (?, ?)"
                self.cur.execute(query, (std_num, lect_num))
                self.conn.commit()
                print("수강신청 완료")
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Information)
                msg_box.setWindowTitle("수강신청 알림")
                msg_box.setText("수강신청이 정상적으로 처리되었습니다.")
                msg_box.setStandardButtons(QMessageBox.Ok)
                msg_box.exec()
            except Exception as e:
                print("Error:", e)
                self.conn.rollback()  # 롤백 처리

        self.close_conn()

    def process_attnd(self, attnd_dic, first_image, lect_num) :
        self.open_conn()

        # 이미지 파일명을 _를 기준으로 분리
        parts = first_image.split('_')

        # 날짜 / 시간 분리
        date = parts[0]
        time_with_extension = parts[1]
        time = time_with_extension.split('.')[0].replace('-', ':')

        print("날짜:", date)
        print("시간:", time)

        self.cur.execute("SELECT STD_NUM_FK FROM STD_REG_TB WHERE LECT_NUM_FK = ?", (lect_num,))
        students_in_lecture = [row[0] for row in self.cur.fetchall()]

        # ATTND_TB에서 해당 수업의 출석 정보 초기화
        self.cur.execute("INSERT OR IGNORE INTO ATTND_TB (STD_NUM_FK, LECT_NUM_FK, ATTND_DATE, ATTND_TIME, ATTND_STAT) "
                        "SELECT STD_NUM_FK, ?, ?, ?, 0 FROM STD_REG_TB WHERE LECT_NUM_FK = ?", (lect_num, date, time, lect_num))

        for student_id, value in attnd_dic.items():
            int_student_id = int(student_id)
            if int_student_id in students_in_lecture:
                if value >= 48:
                    value = 48   # 48보다 크거나 같은 경우 1로 설정
                else:
                    value = 0  # 48보다 작은 경우 0으로 설정
                self.cur.execute(
                    "UPDATE ATTND_TB SET ATTND_STAT = ? WHERE LECT_NUM_FK = ? AND ATTND_DATE = ? AND STD_NUM_FK = ?",
                    (value, lect_num, date, int_student_id))
            else:
                print(f"Warning: 학생 {int_student_id}은(는) 수업에 등록되지 않았습니다. 출석 정보를 업데이트하지 않습니다.")

        self.conn.commit()
        self.close_conn()