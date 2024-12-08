from flask import *
import sqlite3

app = Flask(__name__)
app.debug = True

###### 데이터베이스 연결 ######

# 데이터베이스 연결 전 테스트를 위한 메모리 내 데이터 저장하기
connect = sqlite3.connect('test.db')
connect.execute("PRAGMA foreign_keys = ON;")
Cursor = connect.cursor()

# 테이블 생성 쿼리 (chatGPT의 도움을 받았습니다)
createUserTable =  """
    CREATE TABLE IF NOT EXISTS TestUsers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    track VARCHAR(32) NOT NULL,
    plan VARCHAR(10) NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    pw VARCHAR(255) NOT NULL,
    date DATETIME DEFAULT CURRENT_TIMESTAMP
    );
"""
createPostTable = """
    CREATE TABLE IF NOT EXISTS CheckList (
    post_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    text VARCHAR(500) NOT NULL,
    del_state INTEGER NOT NULL,
    date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES TestUsers (id) ON DELETE CASCADE
    );
"""
Cursor.execute(createUserTable)
Cursor.execute(createPostTable)

# 변경 사항 저장 및 연결 닫기
connect.commit()
connect.close()


##### 어플리케이션 로직 #####

# 로그인 없이 기본 페이지에 접근했을 때
@app.route('/')
def index():
    cookie = request.cookies.get('user_id')
    if cookie:
        connect = sqlite3.connect('test.db')
        connect.row_factory = sqlite3.Row
        Cursor = connect.cursor()
        selectUserInfo = f"""
            SELECT * FROM TestUsers WHERE 
            id={cookie};
        """
        selectList = f"""
            SELECT post_id, text FROM CheckList WHERE
            user_id={cookie};
        """
        Cursor.execute(selectUserInfo)
        userData = Cursor.fetchone()
        track = userData['track']
        name = userData['name']
        Cursor.execute(selectList)
        checkLists = Cursor.fetchall()
        connect.commit()
        connect.close()


        return render_template('index.html', loginState=True ,track=track, name=name, checkLists=checkLists)
    else:
        return render_template('index.html')


# 하위 경로에 접근했을 때 라우팅 관리
@app.route('/<path:subpath>', methods=['GET'])
def pathRouting(subpath):
    if subpath not in ['login', 'join', 'checkList', 'exit']:
        notFound = """
        <h1>404 Not Found</h1>
        <h3>/{{ path }}에 대한 페이지를 찾을 수 없습니다.</h3>
        <a href="/">메인 페이지로 이동하기</a>
        """
        return render_template_string(notFound, path=subpath)


# 로그인 요청 처리
@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        loginData = request.form.to_dict()
        connect = sqlite3.connect('test.db')
        connect.row_factory = sqlite3.Row
        Cursor = connect.cursor()
        selectQuery = f"""
            SELECT * FROM TestUsers where 
            email='{loginData['email']}' 
            and pw='{loginData['pw']}';
        """
        Cursor.execute(selectQuery)
        row = Cursor.fetchone()
        connect.commit()
        connect.close()
        if row:
            res = make_response(redirect('/'))
            res.set_cookie(key='user_id', value=f'{row['id']}')
            return res
        else:
            message = """
                <script>
                    let check = confirm('이메일 또는 패스워드를 다시 한 번 확인해 주세요');
                    if (check) {
                        location.href='/login/';
                    }
                </script>
            """
            return render_template_string(message)
    return render_template('login.html')

# 회원가입 요청 처리
@app.route('/join/', methods=['GET', 'POST'])
def join():
    if request.method == 'POST':
        joinData = request.form.to_dict()
        insertQuery = f"""
            INSERT INTO TestUsers (
            track,
            plan,
            name,
            email,
            pw
            ) VALUES (
            '{joinData['track']}',
            '{joinData['plan']}',
            '{joinData['name']}',
            '{joinData['email']}',
            '{joinData['pw']}'
            );
        """
        connect = sqlite3.connect('test.db')
        Cursor = connect.cursor()
        Cursor.execute(insertQuery)
        connect.commit()
        connect.close()
        return redirect('/login')
    return render_template('join.html')


# 체크리스트 작성 처리
@app.route('/checkList/', methods=['GET', 'POST'])
def postCheckList():
    userid = request.cookies.get('user_id') # 쿠키로 전달된 유저 식별 정보 가져오기
    selectQuery = f"""
        SELECT post_id, text FROM CheckList WHERE
        user_id = {userid};
    """
    if not userid: # 쿠키가 발급되지 않은 경우, 로그인 페이지로 리디렉션
        message = """
            <script>
              let check = confirm('해당 기능은 로그인 후 이용하실 수 있습니다');
              if (check) {
                location.href='/login/';
              }
            </script>
        """
        return render_template_string(message)
    
    if request.method == 'POST':
        postData = request.form.to_dict()
        if 'text' in postData:  # '+' 버튼을 눌러 체크리스트를 추가한 경우
            if postData['text'] == '':  # 체크리스트의 값이 빈 문자열인 경우 데이터를 저장하지 않음
                return redirect('/checkList/')
        if 'delete' in postData: # 'X' 버튼을 눌러 체크리스트 삭제 요청을 보낸 경우
            deleteQuery = f"""
                DELETE FROM CheckList
                WHERE post_id={postData['delete']};
            """
            connect = sqlite3.connect('test.db')
            Cursor = connect.cursor()
            Cursor.execute(deleteQuery)
            connect.commit()
            connect.close()
            return redirect('/checkList/')
        # 체크리스트를 가져와 입력 폼 밑에 출력하기
        insertQuery = f"""
        INSERT INTO CheckList (
        user_id,
        text,
        del_state
        ) VALUES (
        {userid},
        '{postData['text']}',
        0
        );
        """
        connect = sqlite3.connect('test.db')
        connect.row_factory = sqlite3.Row
        Cursor = connect.cursor()
        Cursor.execute(insertQuery)
        Cursor.execute(selectQuery)
        checkLists = Cursor.fetchall()
        connect.commit()
        connect.close()
        return render_template('checkList.html', loginState=True, checkLists=checkLists)
    connect = sqlite3.connect('test.db')
    connect.row_factory = sqlite3.Row
    Cursor = connect.cursor()
    Cursor.execute(selectQuery)
    checkLists = Cursor.fetchall()
    connect.commit()
    connect.close()
    return render_template('checkList.html', loginState=True, checkLists=checkLists)


# 로그아웃 처리
@app.route('/logOut/', methods=['GET'])
def logOut():
    message = """
        <script>
          let check = confirm("로그아웃 되었습니다");
          if (check) {
            location.href='/';
          }
        </script>
    """
    res = make_response(render_template_string(message))
    res.delete_cookie('user_id')
    return res

# 회원 탈퇴 처리
@app.route('/exit/', methods=['GET', 'POST'])
def exit():
    if request.method == 'POST':       
        userData = request.form.to_dict()
        deleteQuery = f"""
            DELETE FROM TestUsers WHERE email='{userData['email']}' and pw='{userData['pw']}';
        """
        connect = sqlite3.connect('test.db')
        Cursor = connect.cursor()
        Cursor.execute(deleteQuery)
        connect.commit()
        connect.close()
        message = """
            <script>
                let check = confirm("정상적으로 탈퇴 처리 되었습니다");
                if (check) {
                    location.href='/';
                }
            </script>
        """
        res = make_response(render_template_string(message))
        res.delete_cookie('user_id')
        return res
    return render_template('exit.html', loginState=True)

if __name__ == '__main__':
    app.run()
