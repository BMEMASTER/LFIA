# -*- coding: utf-8 -*-
import os
import platform
from ruamel.yaml import YAML


class DatabaseConfig:
    """ 数据库配置文件 """
    def __init__(self, params: dict):
        self.user = params.get("user")
        self.password = params.get("password")
        self.host = params.get("host")
        self.port = params.get("port")
        self.dbName = params.get("dbName")


class Config:
    """ 加载配置文件的对象 """
    def __init__(self):
        filename = ""
        if platform.platform().startswith("Windows"):
            filename = "{}/conf/conf.yaml".format(os.getcwd())
        else:
            filename = "/home/tao/Desktop/IFIR-101/src/conf/logging.yaml"
        with open(filename, mode="r", encoding="utf-8") as configFile:
            if configFile.readable():
                yaml = YAML(typ='safe')
                self.__config__ = yaml.load(configFile)
                self.env = self.__config__.get("env")
                self.name = self.__config__.get("name")
                self.version = self.__config__.get("version")
                self.camera = self.__config__.get("camera")
                self.dbConfig = DatabaseConfig(self.__config__.get("database"))
