#! /usr/bin/env python3

import queue
import re
import ast
import json
import requests
import sys
import threading
from bs4 import BeautifulSoup
from sqlalchemy.orm import sessionmaker, scoped_session
from models import db_connect, create_table, Video, Actor, Director
import settings


class Crawler():
    """
    抓取数据并提取所需的视频信息

    变量：
        url 抓取的网址
        limit 抓取最大数量限制
    """

    def __init__(self, start_url, limit):
        """
        初始化Crauler

        变量：
            start_url：起始抓取网址
            limit：抓取最大数量限制
            video_urls_list:抓取到的视频网址list
        """
        self.start_url = start_url
        self.limit = limit
        self.video_urls_list=[]

    def get_video_urls(self):
        next_grab_page_url=self.start_url
        while not self.is_enough_urls():
            next_grab_page_url=self.current_page_video_urls(next_grab_page_url)
            if not next_grab_page_url:
                break
        print('视频网址获取完成，获取到',len(self.video_urls_list),'个视频')


    def is_enough_urls(self):
        if self.limit==0:
            return True
        else:
            return len(self.video_urls_list)<self.limit

    def current_page_video_urls(self,page_url):
        self.print_start_info(page_url)
        parse_html = self.parse_url(page_url)
        video_link = self.get_current_page_video_link(parse_html)
        next_page_url = self.get_next_page_url(parse_html)
        if next_page_url:
            return next_page_url
        else:
            return False


    def print_start_info(self,page_url):
        if settings.DEBUG:
            print('getVideoUrl', page_url)

    def parse_url(self,page_url):
        r = requests.get(page_url)
        try:
            assert r.status_code == 200
            parse = BeautifulSoup(r.text)
            return parse
        except AssertionError as e:
            print('无法读取网页', page_url)
            raise e


    def get_current_page_video_link(self, parse):
        video_div_list = parse.select('div.info')
        temp_video_link_list = []
        for video_div in video_div_list:
            url = re.search(r'href="(.*?)"', str(video_div)).group(1)
            temp_video_link_list.append(url)
        return temp_video_link_list

    def get_next_page_url(self, parse):
        try:
            next_page_tag = parse.select('a.next')
            return self.extract_next_page_url(next_page_tag)
        except:
            print('已到达末页', self.url)
            return False

    def extract_next_page_url(self, next_page_url):
        next_page_relative_url = re.search(r'href="(.*?)"', str(next_page_tag)).group(1)
        base_url = self.url.split('/')[2]
        next_page_url = 'http://' + base_url + next_page_relative_url
        return next_page_url






    #提取video信息
    def getVideoInfo():
        while not videoQueue.empty():
            tempVideo = videoQueue.get()
            if DEBUG:
                print('getVideoInfo', tempVideo.pageUrl)
            r = requests.get(tempVideo.pageUrl)
            r.encoding = 'gbk'
            parse = BeautifulSoup(r.text)
            playlistId = re.search(r'playlistId="(.*?)";', r.text).group(1)
            vid = re.search(r'vid="(.*?)";', r.text).group(1)
            r = requests.get('http://pl.hd.sohu.com/videolist', params={'playlistid': playlistId, 'vid': vid})
            info = json.loads(r.text)
            #print(r.text)
            #print(playlistId,vid,info)
            tempVideo.playlistId = playlistId
            tempVideo.vid = vid

            tempVideo.actors = str(info['actors'])
            tempVideo.categories = str(info['categories'])
            tempVideo.directors = str(info['directors'])
            #tempVideo.actors = info['mainActors']
            tempVideo.defaultPageUrl = info['defaultPageUrl']
            tempVideo.pid = info['pid']
            tempVideo.albumName = info['albumName']
            tempVideo.albumThumbnail = info['largeVerPicUrl']
            tempVideo.EngName = info['tvEnglishName']
            tempVideo.albumPageUrl = info['albumPageUrl']
            tempVideo.description = info['albumDesc']
            tempVideo.updateTime = info['updateTime']
            tempVideo.publishYear = info['publishYear']
            tempVideo.area = info['area']

            if len(info['videos']) == 1:
                videoInfo = ast.literal_eval(str(info['videos'])[1:-1])
            else:
                for i in info['videos']:
                    if i['pageUrl'] == tempVideo.pageUrl:
                        videoInfo = i
                    break

            #pageUrl = videoInfo['pageUrl']
            name = videoInfo['name']
            playLength = videoInfo['playLength']
            thumbnail = videoInfo['largePicUrl']
            publishTime = videoInfo['publishTime']

            # 获取投票
            r = requests.get('http://score.my.tv.sohu.com/digg/get.do', params={'vid': vid})
            vote = json.loads(r.text.strip()[1:-1])
            down = vote['downCount']
            up = vote['upCount']

            #提取播放次数
            # if DEBUG:
            #     print(tempVideo.pageUrl, playlistId, tempVideo.pid, vid)
            r = requests.get('http://count.vrs.sohu.com/count/stat.do?', params={'vid': vid, 'playlistId': playlistId})
            r.encoding = 'gbk'
            #print(r.text)


            #插入director actor 和video
            directorList = []
            directorNameList = []
            actorList = []
            actorNameList = []
            findActor = re.compile(r'target="_blank">(.*?)</a>')
            findActorUrl = re.compile(r'href="(.*?)"')
            try:
                tempBasicInfo = parse.select('div.info.info-con')[0]
                director = re.search(r'导演：.*?target="_blank">(.*?)</a>', str(tempBasicInfo)).group(1)
                dirctorUrl = re.search(r'导演：<a href="(.*?)" target="_blank">', str(tempBasicInfo)).group(1)
                directorNameList.append((director))
                directorList.append(Director(name=director, url=dirctorUrl))
                tempActors = tempBasicInfo.select('li#mainactor a')

                for tempActor in tempActors:
                    actor = findActor.search(str(tempActor)).group(1)
                    actorUrl = findActorUrl.search(str(tempActor)).group(1)
                    actorNameList.append(actor)
                    actorList.append(Actor(name=actor, url=actorUrl))
            except:
                directorInfo = parse.select('div.con a')
                for i in directorInfo:
                    if 'javascript' not in str(i):
                        director = re.search(r'target="_blank">(.*?)</a>', str(i)).group(1)
                        dirctorUrl = re.search(r'href="(.*?)" target="_blank">', str(i)).group(1)
                        directorList.append(Director(name=director, url=dirctorUrl))

                actorInfo = parse.select('div#mainactor a')
                for i in actorInfo:
                    if 'javascript' not in str(i):
                        actor = findActor.search(str(i)).group(1)
                        actorUrl = findActorUrl.search(str(i)).group(1)
                        actorList.append(Actor(name=actor, url=actorUrl))

            session = Session()


            for i in directorList:
                if i.name in directorNameList:
                    session.add(i)
            for i in actorList:
                if i.name in actorNameList:
                    session.add(i)
            session.add(tempVideo)
            session.commit()
            Session.remove()
            videoQueue.task_done()
        print('已插入', name)