# -*- coding: utf-8 -*-
import os
import platform
from ruamel.yaml import YAML
import logging
from logging import handlers


class LoggerFactory(object):
    """ 记录系统日志的类 """
    # 日志级别关系映射
    level_relations = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }

    log = None

    def __init__(self):
        pass

    @classmethod
    def __loadConfig__(cls):
        """ 加载配置文件 """
        fileName = ""   # 配置文件的位置
        if platform.platform().startswith("Windows"):
            fileName = "./conf/logging.yaml"
        else:
            fileName = "/home/pi/Desktop/Imgtest/src/conf/logging.yaml"
        filename = None
        level = None
        fmt = None
        with open(fileName, mode="r", encoding="utf-8") as configFile:
            if configFile.readable():
                yaml = YAML(typ='safe')
                config = yaml.load(configFile)
                filename = config.get("filename")
                level = config.get("level")
                fmt = config.get("format")
        return filename, level, fmt

    @classmethod
    def getLogger(cls):
        """ 获取日志对象 """
        if cls.log is None:
            filename, level, fmt = cls.__loadConfig__()
            # 判断filename文件夹是否存在
            if not os.path.exists(filename):
                os.mkdir(filename)
            filename = filename + os.sep + "main.log"
            # 配置logging日志对象
            logger = logging.getLogger(filename)
            # 设置日志格式
            format_str = logging.Formatter(fmt)
            # 设置日志级别
            logger.setLevel(cls.level_relations.get(level))
            # 往屏幕上输出
            sh = logging.StreamHandler()
            # 设置屏幕上显示的格式
            sh.setFormatter(format_str)
            # 往文件里写入指定间隔时间自动生成文件的处理器
            # 实例化TimedRotatingFileHandler
            # interval是时间间隔，backupCount是备份文件的个数，如果超过这个个数，就会自动删除，when是间隔的时间单位，单位有以下几种：
            # S秒,M分, H小时, D 天,W 每星期（interval==0时代表星期一）,midnight 每天凌晨
            th = handlers.TimedRotatingFileHandler(
                filename=filename,
                when="D",
                backupCount=3,
                encoding='utf-8')
            # 设置文件里写入的格式
            th.setFormatter(format_str)
            # 把对象加到logger里
            logger.addHandler(sh)
            logger.addHandler(th)
            cls.log = logger
        return cls.log


if __name__ == '__main__':
    log = LoggerFactory.getLogger()
    log.debug('debug')
    log.info('info')
    log.warning('警告')
    log.error('报错')
    log.critical('严重')