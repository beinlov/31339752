import pymysql
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
# from typing import Dict
from collections import defaultdict

import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

app = FastAPI()

discriptions = {
    'b2':"蠕虫程序刚运行，首次请求验证C2有效性",
    'a0':"上传文件前请求，疑似建议服务器新建目录",
    'a1':"询问文件名是否可以删除",
    'a4':"POST文件",
    'a5':"蠕虫查命令列表，随后就用sid作为a3的param1参数来查询可以下载的命令文件名称列表",
    'a3':"客户端用param1查命令文件列表，然后客户端会再访问a7",
    'a7':"客户端下载文件后，客户端会再访问a6，可能是让服务器确认",
    'a6':"客户端a7下载后，用a6提示已经保存完成的",
    'a8':"询问文件名是否可以删除",
    'a9':"蠕虫查命令列表，下一步客户端会用b0来下载",
    'b0':"下载",
    'b1':"确认下载"
}

#join on clean
#join write log flush前， on clean不行，逻辑不通
def parse(line):
    properties = line.split(',')
    time, ip, status = properties[0], properties[1], properties[2]
    disc = ''
    if len(properties) >= 4:
        url = properties[-1]
        #逻辑可能有问题嗷，也可以用&分隔parse参数
        command = url[-5:]
        if command.startswith("ql"):
            command = command[-2:]
            disc = discriptions[command] if command in discriptions.keys() else ''
        else:
            command = ''
    return {
        'ip':ip,
        'time':time,
        'status':status,
        'command':command,
        'disc':disc
    } ## 存在command为空的情况，这个在后面异常处理掉吧

class detail(BaseModel):
    ip: str
    time: str
    command: str
    description: str
    status: str

resp = defaultdict(detail)
# class Resp(BaseModel):
#     id: int
#     dt: detail

# global id_count
id_count = 0


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, filename, db):
        self.filename = filename
        self.last_size = 0
        self.db = db #database object
        self.dbcur = db.cursor()

    def on_modified(self, event):
        print("it's running")
        print(f"{event.src_path}")
        if event.src_path == self.filename or event.src_path == ".\\" + self.filename:
            # self.detect_new_content()
            self.write2table()
            # print(resp) 不用这返回了
            # yield resp

    # def detect_new_content(self):
    #     try:
    #         with open(self.filename, "r") as file:
    #             file.seek(self.last_size)  # 从上次记录的位置开始读取
    #             new_content = file.read()
    #             if new_content:
    #                 print("New content detected:")
    #                 print(new_content)
    #             self.last_size = file.tell()  # 更新文件大小
    #     except Exception as e:
    #         print(f"Error reading file: {e}")

    '''
        insert to table tmp (可改)
        将更改的数据块返回 json response
    '''
    def write2table(self):
        global id_count
        try:
            with open(self.filename, 'r') as file:
                file.seek(self.last_size)
                new_content = file.read()
                if new_content:
                    print("New content detected:")
                    print(new_content)
                    lines = new_content.split('\n')
                    print(f"lines are {lines}")
                    for line in lines:
                        if line.strip() == '':
                            continue
                        rd = parse(line.strip())
                        ip, ctime, command, dis, status = rd['ip'], rd['time'], rd['command'], rd['disc'], rd['status']
                        if command.strip() == '':
                            continue
                        sql = """
                            insert into tmp (id, ip, time, command, detail, status) values (%s, %s, %s, %s, %s, %s);
                        """
                        try:
                            print(f"{id_count}, {ip}, {ctime}, {command}, {dis}, {status}")
                            self.dbcur.execute(sql, (id_count, ip, ctime, command, dis, status))
                            self.db.commit()
                            id_count += 1
                        except Exception as e:
                            print(f"fail to insert to database, thow exception as {e}")
                        # OneDetail = detail(ip=ip, time=ctime, command=command, discription=dis, status=status)
                        # tmp_set = parse(line.strip())
                        # resp[str(id_count)] = OneDetail
                self.last_size = file.tell()
                # return JSONResponse(content=resp)
                return
        except Exception as e:
            print(f"Error while reading file {self.filename}, throw exexcption {e}")

'''
    db: 主要是FileChangeHandler需要一个db
    filename: 监听的文件
'''
def watch_main(db, filename = ".\example.txt"):
    # db = pymysql.connect(
    #     host='localhost',
    #     user='root',
    #     password='kjl12345678',
    #     # charset = 'utf8'
    #     database='test_db'
    # )
    # cur = db.cursor()
    event_handler = FileChangeHandler(filename, db)
    observer = Observer()
    observer.schedule(event_handler, path=".", recursive=False)
    observer.start()
    print(f"Monitoring file: {filename}. Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

    # cur.execute("drop table tmp;")

@app.get("/dblog/{filename}")
async def post_log(filename:str):
    #connection
    db = pymysql.connect(
        host='localhost',
        user='root',
        password='Zm.1575098153',
        # charset = 'utf8'
        database='botnet'
    )

    cur = db.cursor()

    cur.execute("SELECT 1 FROM information_schema.tables WHERE table_schema = %s AND table_name = %s;",('botnet', 'tmp'))
    if cur.fetchone() is None:
        print(f"table not exist")
        cur.execute("create table tmp(id int, ip varchar(16), time varchar(25), command varchar(3), detail varchar(50), status varchar(50));")

    watch_main(db, filename)

    # cur.execute("create table tmp(id int, ip varchar(16), time varchar(25), command varchar(3), detail varchar(50), status varchar(50));")
    cur.execute("select * from tmp;")
    results = cur.fetchall()
    print(f"in main: results are {results}")
    return JSONResponse(content=results)




if __name__ == "__main__":
    # line = "2025-03-25 22:05:30,192.168.137.2,access,/content/faq.php?&ql=a5"
    # print(parse(line))

    filename = time.strftime('%Y-%m-%d', time.localtime()) + ".txt"
    # watch_main(filename)



