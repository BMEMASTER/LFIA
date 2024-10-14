# -*- coding: utf-8 -*-
import pymysql
from pymysql import Error
from config import DatabaseConfig
from logFactory import LoggerFactory


log = LoggerFactory.getLogger()


class HistoryRecord:
    """ 历史记录 """

    def __init__(self):
        self.id = None
        self.testNum = None
        self.serialNum = None
        self.rVal = None
        self.gVal = None
        self.createTime = None

    def __str__(self):
        return str({
            "id": self.id,
            "testNum": self.testNum,
            "serialNum": self.serialNum,
            "rVal": self.rVal,
            "gVal": self.gVal,
            "createTime": self.createTime
        })

    def __repr__(self):
        return self.__str__()


class Dao:

    def __init__(self, config: DatabaseConfig):
        self.__config = config

    def connect(self):
        """ 获取数据库连接 """
        try:
            db = pymysql.connect(
                host=self.__config.host,
                user=self.__config.user,
                password=self.__config.password,
                database=self.__config.dbName
            )
            return db
        except Exception as e:
            log.debug(e)
            raise e

    def executeQuery(self, sql: str):
        """ 执行查询sql语句 """
        db = None
        cursor = None
        try:
            db = self.connect()
            cursor = db.cursor()
            # 执行语句
            cursor.execute(sql)
            result = cursor.fetchall()
            return result
        except Exception as e:
            log.debug(e)
            raise e
        finally:
            if db is not None:
                db.close()
            if cursor is not None:
                cursor.close()

    def addRecord(self, peaksR, number, testTime):
        """ 批量添加数据 """
        db = None
        cursor = None
        try:
            db = self.connect()
            cursor = db.cursor()
            for i in range(len(peaksR)):
                data = HistoryRecord()
                data.testNum = number
                data.serialNum = i + 1
                data.rVal = peaksR[i].avePix
                # data.gVal = peaksG[i].sumPix
                data.createTime = testTime
                print(type(peaksR[i].avePix))
                #sql = "INSERT INTO `history`(test_num, serial_num, r_val, create_time) VALUES ('{}', {}, {}, {}, '{}')"\
                #    .format(number, i + 1, peaksR[i].avePix,  testTime.toString("yyyy/MM/dd HH:mm:ss"))
                sql = "INSERT INTO `history`(test_num, serial_num, r_val, create_time) VALUES ('{}', {}, {}, '{}')"\
                    .format(number, i + 1, peaksR[i].avePix, testTime.toString("yyyy/MM/dd HH:mm:ss"))
                #create table test.history(test_num char(10), serial_num int(10), r_val int(10), create_time Datetime(6));
                print(sql)
                cursor.execute(sql)
            # 执行语句
            db.commit()
            return True
        except Error as e:
            db.rollback()
            log.debug(e)
            raise e
        finally:
            if db is not None:
                db.close()
            if cursor is not None:
                cursor.close()

    def select(self, beginTime, endTime):
        """ 按条件查询 """
        try:
            sql = "SELECT * from history where create_time >= '{}' and create_time <= '{}'".format(beginTime, endTime)
            dataList = []
            print(sql)
            records = self.executeQuery(sql)
            print(records)
            for record in records:
                history = HistoryRecord()
                #history.id, history.testNum, history.serialNum, history.rVal, history.gVal, history.createTime = record
                history.testNum, history.serialNum, history.rVal, history.createTime = record
                dataList.append(history)
            return dataList
        except Exception as e:
            log.debug(e)
            raise e

    def deleteByTime(self, beginTime, endTime):
        """ 删除数据 """
        db = None
        cursor = None
        try:
            db = self.connect()
            cursor = db.cursor()
            sql = "DELETE from `history` where create_time >= '{}' and create_time <= '{}'".format(beginTime, endTime)
            print(sql)
            # 执行语句
            cursor.execute(sql)
            db.commit()
        except Error as e:
            db.rollback()
            log.debug(e)
            raise e
        finally:
            if db is not None:
                db.close()
            if cursor is not None:
                cursor.close()


if __name__ == "__main__":
    # record.createTime = "2021/12/15 15:35:35"
    # dao = Dao(DatabaseConfig({
    #     "host": "localhost",
    #     "port": 3306,
    #     "user": "root",
    #     "password": "12345678",
    #     "dbName": "bdjc"
    # }))
    # # 检查是否存在相同的记录
    # records = dao.selectByNum(record.number)
    # print(records)
    # # 若存在相同编号的记录则更新数据，否则添加数据
    # if len(records) > 0:
    #     dao.updateByNum(record)
    # else:
    #     dao.addRecord(record)
    pass