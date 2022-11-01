from flask import Flask, render_template ,redirect, request, session, jsonify
import mysql.connector
from flask_bcrypt import Bcrypt
from mysql.connector import pooling
from password import *

#密碼加密初始化
bcrypt = Bcrypt()

#session key
app =Flask(__name__)
app.secret_key= secret_key()
app.config['JSON_AS_ASCII'] = False

poolname ="mysqlpool"
poolsize = 5
connectionpool = mysql.connector.pooling.MySQLConnectionPool(
pool_name =poolname,pool_size=poolsize, pool_reset_session=True, host='localhost',user='root',password=mySqlPassword())


#將 .get_connection() 存入 conn
def conn():
    #connection pool 連線資料
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

def loginHandle(username, password, c, cursor):
    if (username == None or password == None):
        return False
    try:
        sql = "SELECT password FROM member where username = %s"
        user = (username,)
        result = executeSql (cursor, sql, user)
        hashed_password =result[0]
        check_password = bcrypt.check_password_hash(hashed_password, password)
        if ((f"{check_password}") != "True"):
            return False 
        return result
    except Exception as e:
        print ("資料庫執行有誤：", e)
        return  False 

#首頁
@app.route("/")
def index():       
	return render_template("register.html")

#處理註冊
@app.route("/signup",methods=["POST"])
def signup():  
    nickname = request.form["nickname"]
    username = request.form["username"]
    password = request.form["password"]
    if (not nickname or not username or not password):
        return redirect("/error?message=欄位不得爲空")

    try:
        c = conn()  #呼叫連線程式
        cursor = selectDb(c)
        sql = "SELECT username FROM member where username = %s"
        user = (username,)
        result = executeSql (cursor, sql, user)
        if (result):   
            return redirect("/error?message=帳號已被註冊")
        hashed_password = bcrypt.generate_password_hash(password=password)
        sql = "Insert into member (name, username, password ) values (%s, %s, %s)"
        userInfo = (nickname, username, hashed_password)
        executeSql (cursor, sql, userInfo)
        c.commit()
        return redirect("/") 
        
    except Exception as e:
        print ("處理註冊出現問題：", e)

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
        if (result == [] or result == None):
            return redirect("/error?message=查無此帳號")
    except:
        return redirect("/error?message=帳號或密碼錯誤")
    
    try:
        user_id = result[0]
        hashed_password = result[3]
        check_password = bcrypt.check_password_hash(hashed_password, password)
        if ((f"{check_password}") != "True"):
            return redirect("/error?message=密碼錯誤")
        session['username'] = username
        session['password'] = password
        session['user_id'] = user_id                
        return redirect("/member")

    except:
        return redirect("/error?message=帳號或密碼錯誤")

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
    c = conn()
    cursor = selectDb(c)
    result = loginHandle(username, password, c, cursor)
    if not result:
        return redirect("/")

    try:    
        #取姓名、帳號、時間、內文
        sql = "select member.name, member.username, message.content, message.time from member inner join message on member.id = message.member_id order by message.time desc"
        cursor.execute(sql)
        result = cursor.fetchall()
        return render_template("index.html", username=username, result=result)          
            
    except Exception as e:
        print ("資料庫執行有誤：", e)
        return redirect("/")

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
    c = conn()
    cursor = selectDb(c)
    result = loginHandle(username, password, c, cursor)
    if not result:
        return redirect("/")

    try:
        user_id = session.get('user_id')
        content = request.form["content"]
        sql = "Insert into message (member_id, content) values (%s, %s)"
        user_content = (user_id, content)    
        cursor.execute(sql, user_content) 
        c.commit() 
        return redirect("/member")

    except Exception as e:
        print ("發送訊息出現問題：", e)
        return redirect("/")
    finally:
        close(c, cursor) 

#api頁面：user 的資訊
@app.route("/api/member")
def api_member():
    username = session.get('username')
    password = session.get('password')
    c = conn()
    cursor = selectDb(c)
    dataNull = {'data': None}
    result = loginHandle(username, password, c, cursor)
    if not result:
        return dataNull

    #GET username 並製作 api
    try:
        getUsername = (request.args.get('username'),)
        sql = "select id, name from member where username = %s" 
        result = executeSql (cursor, sql, getUsername)
        if not result:
            return dataNull
        data = {
            "id":result[0],
            "name":result[1],
            "username": getUsername
        }
        member = jsonify({
            "data": data
        })
        return member

    except Exception as e:
        print ("user api 出現問題：", e)
    finally:
        close(c, cursor) 


#api頁面：回覆patch資料更新狀態
@app.route("/api/member",methods=["PATCH"] )
def name_edit():
    #登入驗證
    username = session.get('username')
    password = session.get('password')
    c = conn()
    cursor = selectDb(c)
    okMessage =jsonify({"ok":True})
    errMessage =jsonify({"error":True})
    result = loginHandle(username, password, c, cursor)
    if not result:
        return errMessage

    try:
        #取得 PATCH 的資料並更新
        data = request.json
        newName = data['name']
        if not newName:
            return errMessage

        sql = "update member set name = %s where username= %s"
        user_info =(newName, username)
        result = executeSql (cursor, sql, user_info)
        rowcount = cursor.rowcount
        c.commit()

        if(rowcount == 1):
            return okMessage
        else:
            return errMessage
            
    except Exception as e:
        print ("更新 user name api 出現問題：",e)
        return errMessage
    finally:
        close(c, cursor) 


if __name__=="__main__": #如果以主程式進行
	app.run(port=3000) #立刻啟動伺服器
