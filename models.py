#! /usr/bin/env python3

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

import settings


Base = declarative_base()


class Video(Base):
    """
    定义表video中存储的视频信息

    变量：
        name 视频名称
        en_name 视频英文名称
        thumbnail 视频缩略图网址
        directors 导演
        actors 主演
        categories 视频类型
        description 视频描述
        page_url 视频所在网址

        album_name 视频所属专辑名称
        album_thumbnail 视频所属专辑缩略图
        album_page_url 视频所在专辑网址
        default_page_url 视频默认网页地址

        playlist_id playlist_id
        vid vid
        pid pid

        update_time 最后更新时间
        publish_year 发布年费
        area 所属地区
        play_length 视频长度
        publish_time 视频发布时间

        up_vote 顶
        down_vote 踩
    """

    __tablename__ = 'video'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    en_name = Column(String)
    thumbnail = Column(String)
    directors = Column(String)
    actors = Column(String)
    categories = Column(String)
    description = Column(String)
    page_url = Column(String)

    album_name = Column(String)
    album_thumbnail = Column(String)
    album_page_url = Column(String)
    default_page_url = Column(String)

    playlist_id = Column(String)
    vid = Column(String)
    pid = Column(String)

    update_time = Column(String)
    publish_year = Column(String)
    area = Column(String)
    play_length = Column(String)
    publish_time = Column(String)


    up_vote = Column(Integer)
    down_vote = Column(Integer)


    def __repr__(self):
        return "<Video(name={0},url={1})>".format(self.name, self.page_url)


def db_connect():
    """
    连接数据库

    返回：连接的数据库引用
    """

    return create_engine(settings.DATABASE)


def create_table(engine):
    """
    根据models中定义的表结构 在数据库中创建表
    """

    Base.metadata.create_all(engine)