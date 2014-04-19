#! /usr/bin/env python3

import threading

from sqlalchemy.orm import sessionmaker, scoped_session

from models import db_connect, create_table


class InsertData(object):
    """
    将数据插入数据库

    属性：
        Session scoped_session
        number 插入的数据计数
        print_lock lock 处理print时的锁
    """

    def __init__(self):
        """
        初始化class
        """

        engine = db_connect()
        create_table(engine)
        sessionFactory = sessionmaker(bind=engine)
        self.Session = scoped_session(sessionFactory)
        self.number = 1
        self.print_lock = threading.Lock()

    def insert_into_database(self, item):
        """
        将数据插入数据库

        参数：
            item model 要插入的数据
        """

        session = self.Session()
        session.add(item)
        session.commit()
        with self.print_lock:
            print(self.number, '已插入：', item)
            self.number += 1
        self.Session.remove()