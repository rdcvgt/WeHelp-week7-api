from flask import Flask, render_template ,redirect, request, session
import mysql.connector
from flask_bcrypt import Bcrypt
from mysql.connector import pooling
from password import *
import json

#將 .get_connection() 存入 conn
def conn():
    #connection pool 連線資料
    poolname ="mysqlpool"
    poolsize = 5
    connectionpool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name =poolname,pool_size=poolsize, pool_reset_session=True, host='localhost',user='root',password=mySqlPassword())
    try:
        c = connectionpool.get_connection()
        return c
    except Exception as e:
        print ("connection error", e)

# #選擇資料庫
def selectDb(c):
    cursor = c.cursor()
    cursor.execute("USE website;") 
    return cursor

#執行 sql 指令
def executeSql (cursor, sql, data=""):
    if data == "":
        cursor.execute(sql)
    else:
        cursor.execute(sql, data)
    result = cursor.fetchone()
    return result

#關閉連線與 cursor
def close(c, cursor):
    cursor.close()
    c.close()  

#密碼加密初始化
bcrypt = Bcrypt()

#session key
app =Flask(__name__)
app.secret_key= secret_key()


#首頁
@app.route("/")
def index():       
	return render_template("register.html")

#處理註冊
@app.route("/signup",methods=["POST"])
def signup():  
    try:
        c = conn()  #呼叫連線程式
        cursor = selectDb(c)
        nickname = request.form["nickname"]
        username = request.form["username"]
        password = request.form["password"]
        sql = "SELECT username FROM member where username = %s"
        user = (username,)
        result = executeSql (cursor, sql, user)
        if (not nickname or not username or not password):
            return redirect("/error?message=欄位不得爲空")
        if (result):   
            return redirect("/error?message=帳號已被註冊")
        else:
            hashed_password = bcrypt.generate_password_hash(password=password)
            sql = "Insert into member (name, username, password ) values (%s, %s, %s)"
            userInfo = (nickname, username, hashed_password)
            executeSql (cursor, sql, userInfo)
            c.commit()
            return redirect("/") 
    except Exception as e:
        print (e)
    finally:
        close(c, cursor)


#處理登入
@app.route("/login",methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    if (not username or not password):
        return redirect("/error?message=欄位不得爲空")

    try:
        c = conn()
        cursor = selectDb(c)
        sql = "SELECT * FROM member where username = %s"
        user = (username,)
        result = executeSql (cursor, sql, user)
        if (result != []):
            user_id = result[0]
            hashed_password = result[3]
            check_password = bcrypt.check_password_hash(hashed_password, password)
            if ((f"{check_password}") == "True"):
                session['username'] = username
                session['password'] = password
                session['user_id'] = user_id                
                return redirect("/member")
        return redirect("/error?message=帳號或密碼錯誤")

    except Exception as e:
        print (e)
    finally:
        close(c, cursor)        
    

#錯誤頁面
@app.route("/error")
def error():
    err = request.args.get("message", "出現錯誤")
    return render_template("loginFail.html", message = err)
	
#會員頁
@app.route("/member")
def member():
    username = session.get('username')
    password = session.get('password')

    try:
        c = conn()
        cursor = selectDb(c)
        if (username!= None and password != None):
            sql = "SELECT password FROM member where username = %s"
            user = (username,)
            result = executeSql (cursor, sql, user)
            hashed_password =result[0]
            check_password = bcrypt.check_password_hash(hashed_password, password)

            if ((f"{check_password}") == "True"):
                #取姓名、帳號、時間、內文
                sql = "select member.name, member.username, message.content, message.time from member inner join message on member.id = message.member_id order by message.time desc"
                cursor.execute(sql)
                result = cursor.fetchall()
                return render_template("index.html", username=username, result=result) 
        return redirect("/")

    except Exception as e:
        print (e)
    finally:
        close(c, cursor)        

#處理登出
@app.route("/signout")
def signout():
    session.clear()
    return redirect("/")

#處理訊息   #必須登入驗證：
@app.route("/message",methods=["POST"])
def message():
    username = session.get('username')
    password = session.get('password')

    try:
        c = conn()
        cursor = selectDb(c)
        if (username!= None and password != None):
            user_id = session.get('user_id')
            #插入 message 資料表
            content = request.form["content"]
            sql = "Insert into message (member_id, content) values (%s, %s)"
            user_content = (user_id, content)    
            cursor.execute(sql, user_content) 
            c.commit() 
            return redirect("/member")
        return redirect("/")

    except Exception as e:
        print (e)
    finally:
        close(c, cursor) 

#api頁面：user 的資訊
@app.route("/api/member")
def api_member():
    username = session.get('username')
    password = session.get('password')
    dataNull = {'data': None}

    try:
        c = conn()
        cursor = selectDb(c)
        if (username!= None and password != None):
            #從網址取得 username 取得 user 其他資訊
            getUsername = (request.args.get('username'),)
            sql = "select id, name from member where username = %s" 
            result = executeSql (cursor, sql, getUsername)
            if (result):
                data = {
                    "id":result[0],
                    "name":result[1],
                    "username": getUsername
                }
                member = json.dumps({
                    "data": data
                },ensure_ascii=False)
                return member
        return  dataNull

    except Exception as e:
        print (e)
    finally:
        close(c, cursor) 

#api頁面：回覆patch資料更新狀態
@app.route("/api/member",methods=["PATCH"] )
def name_edit():
    username = session.get('username')
    password = session.get('password')

    try:
        c = conn()
        cursor = selectDb(c)
        if (username!= None and password != None):
            #取得 PATCH 的資料並更新
            data = request.json
            newName = data['name']
            sql = "update member set name = %s where username= %s"
            user_info =(newName, username)
            result = executeSql (cursor, sql, user_info)
            rowcount = cursor.rowcount
            c.commit()

            okMessage ={"ok":True}
            errMessage ={"error":True}
            if(rowcount == 1):
                return okMessage
            else:
                return errMessage

        return errMessage
    except Exception as e:
        print (e)
    finally:
        close(c, cursor) 


if __name__=="__main__": #如果以主程式進行
	app.run(port=3000) #立刻啟動伺服器
