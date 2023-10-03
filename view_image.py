### 테스트용 - 데베 저장한 이미지 확인

import sqlite3

conn = None
cur = None

print("open_conn")
conn = sqlite3.connect("database/Attendance_System.db")
cur = conn.cursor()

cur.execute(f'SELECT * FROM STD_INFO_TB WHERE STD_ID=?', ('hong',))
user_info = cur.fetchone()

img = user_info[6] # 5:front, 6:right, 7:left
with open('front_image.jpeg', 'wb') as f:
    f.write(img)

conn.close()
print("Database Disconnected!")