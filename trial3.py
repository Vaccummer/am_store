import MySQLdb

# 连接数据库
conn = MySQLdb.connect(
    host='localhost',
    user='root',
    password='1984',
)
crusor = conn.cursor()
crusor._