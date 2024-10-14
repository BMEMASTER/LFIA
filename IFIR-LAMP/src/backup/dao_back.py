# -*- coding: utf-8 -*-
import pymysql
from pymysql import Error
from config import DatabaseConfig
from logFactory import LoggerFactory


log = LoggerFactory.getLogger()


class DataRecord:
    """ 数据库记录 """
    def __init__(self):
        self.id = None
        self.number = None
        self.cLine = None
        self.tLine = None
        self.createTime = None

    def __str__(self):
        return "{"  \
               + "id:{}, number:{}, cLine:{}, tLine:{}, createTime:{}" \
                   .format(self.id, self.number, self.cLine, self.tLine, self.createTime) \
               + "}"

    def __repr__(self):
        return self.__str__()


class HistoryRecord:
    """ 历史记录 """

    def __init__(self):
        self.id = None
        self.testNum = None
        self.serialNum = None
        self.rVal = None
        self.gVal = None
        self.createTime = None


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

    def addRecord(self, record: DataRecord):
        """ 添加记录 """
        db = None
        cursor = None
        try:
            db = self.connect()
            cursor = db.cursor()
            sql = "INSERT INTO `data`(number, c_line, t_line, create_time) VALUES ('{}', {}, {}, '{}')" \
                .format(record.number, record.cLine, record.tLine, record.createTime)
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

    def addRecords(self, dataList: list):
        """ 批量添加数据 """
        db = None
        cursor = None
        try:
            db = self.connect()
            cursor = db.cursor()
            sql = "INSERT INTO `data`(number, c_line, t_line, create_time) VALUES (%s, %s, %s, %s)"
            # 执行语句
            cursor.executemany(sql, dataList)
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

    def selectAll(self):
        """ 查询全部的记录 """
        try:
            dataList = []
            records = self.executeQuery("SELECT id, number, c_line, t_line, create_time from data")
            for record in records:
                data = DataRecord()
                data.id, data.number, data.cLine, data.tLine, data.createTime = record
                dataList.append(data)
            return dataList
        except Exception as e:
            log.debug(e)
            raise e

    def selectNum(self):
        """ 查询所有的编号 """
        try:
            records = self.executeQuery("SELECT DISTINCT number from data")
            numList = []
            for number in records:
                numList.append(number[0])
            return numList
        except Exception as e:
            log.debug(e)
            raise e

    def select(self, beginTime=None, endTime=None, num=None):
        """ 按条件查询 """
        try:
            sql = "SELECT id, number, c_line, t_line, create_time from data where "
            if beginTime and endTime:
                sql = sql + "create_time >= '{}' and create_time <= '{}'".format(beginTime, endTime)
            if num:
                sql = sql + " and number = '{}'".format(num)
            dataList = []
            print(sql)
            records = self.executeQuery(sql)
            for record in records:
                data = DataRecord()
                data.id, data.number, data.cLine, data.tLine, data.createTime = record
                dataList.append(data)
            return dataList
        except Exception as e:
            log.debug(e)
            raise e

    def selectByNum(self, num):
        """ 通过编号查询记录 """
        try:
            sql = "SELECT id, number, c_line, t_line, create_time from data where number = '{}'".format(num)
            recordList = self.executeQuery(sql)
            dataList = []
            for record in recordList:
                data = DataRecord()
                data.id, data.number, data.cLine, data.tLine, data.createTime = record
                dataList.append(data)
            return dataList
        except Exception as e:
            log.debug(e)
            raise e

    def updateByNum(self, record: DataRecord):
        """ 根据编号更新数据 """
        db = None
        cursor = None
        try:
            db = self.connect()
            cursor = db.cursor()
            sql = "UPDATE `data` SET c_line = {}, t_line = {}, create_time = '{}' where number = '{}'" \
                .format(record.cLine, record.tLine, record.createTime, record.number)
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

    def deleteByTimeAndNumber(self, beginTime, endTime, num=None):
        """ 删除数据 """
        db = None
        cursor = None
        try:
            db = self.connect()
            cursor = db.cursor()
            sql = "DELETE from `data` where "
            if beginTime and endTime:
                sql = sql + "create_time >= '{}' and create_time <= '{}'".format(beginTime, endTime)
            if num:
                sql = sql + " and number = '{}'".format(num)
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
    # records = select("2021-11-28", "2021-12-29")
    # print(records)
    record = DataRecord()
    record.number = "123"
    record.tLine = 10.00
    record.cLine = 11.00
    record.createTime = "2021/12/15 15:35:35"
    dao = Dao(DatabaseConfig({
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "12345678",
        "dbName": "bdjc"
    }))
    # 检查是否存在相同的记录
    records = dao.selectByNum(record.number)
    print(records)
    # 若存在相同编号的记录则更新数据，否则添加数据
    if len(records) > 0:
        dao.updateByNum(record)
    else:
        dao.addRecord(record)