#! /usr/bin/env python3

import queue
import re
import ast
import json
import requests
import threading
from bs4 import BeautifulSoup
from insert_data import InsertData
from models import Video
import settings


class GetVideoUrls(object):
    """
    抓取数据并提取所需的视频信息

    属性：
        start_url string 开始抓取的网址
        limit int 抓取最大数量限制
        video_urls_list list 存储所有获取到的视频网址
    """

    def __init__(self, start_url, limit):
        """
        初始化class

        参数：
            start_url string 起始抓取网址
            limit int 抓取最大数量限制
        """

        self.start_url = start_url
        self.limit = limit
        self.video_urls_list = []

    def get_video_urls(self):
        """
        提取视频网址 直到满足limit限制

        返回：
            self.video_urls_list list 所有获取到的视频网址
        """

        next_page_url = self.start_url
        while not self.is_enough_urls():
            self.print_start_info(next_page_url)
            parse = self.parse_url(next_page_url)
            if parse:
                self.add_current_page_video_urls(parse)
                next_page_url = self.get_next_page_url(parse)
                if not next_page_url:
                    break
        print('视频网址获取完成')
        return self.video_urls_list[:self.limit]

    def is_enough_urls(self):
        """
        判断是否抓取到足够的视频网址

        返回：
            足够返回True 不足返回False
        """

        if self.limit == 0:
            return False
        else:
            return len(self.video_urls_list) > self.limit

    def print_start_info(self, page_url):
        if settings.DEBUG:
            print('getVideoUrl', page_url)

    def parse_url(self, page_url):
        """
        获取页面信息

        返回：
            若网页正常打开 返回BeautifulSoup处理后的页面
            若出现异常 返回False
        """

        r = requests.get(page_url)
        try:
            assert r.status_code == 200
            parse = BeautifulSoup(r.text)
            return parse
        except AssertionError as e:
            print('无法读取网页', page_url)
            return False

    def add_current_page_video_urls(self, parse):
        """
        提取当前页面的视频网址 将网址加入self.video_urls_list

        参数：
            parse parse Beautifulsoup处理过的网页
        """

        video_div_list = parse.select('div.info')
        temp_video_link_list = []
        for video_div in video_div_list:
            url = re.search(r'href="(.*?)"', str(video_div)).group(1)
            temp_video_link_list.append(url)
        self.video_urls_list.extend(temp_video_link_list)

    def get_next_page_url(self, parse):
        """
        提取页面的下一页地址

        参数：
            parse parse Beautifulsoup处理过的网页

        返回
            若网页存在下一页 返回next_page_url string
            若不存在 返回False
        """

        try:
            next_page_tag = parse.select('a.next')
            next_page_relative_url = re.search(r'href="(.*?)"', str(next_page_tag)).group(1)
            base_url = self.start_url.split('/')[2]
            next_page_url = 'http://' + base_url + next_page_relative_url
            return next_page_url
        except:
            print('已到达末页', self.url)
            return False


class ExtractAndInsertVideoData(object):
    """
    从视频网址提取视频信息 并将数据插入数据库

    属性：
        insert_data_class InsertData的实例 负责插入数据
        video_queue queue 存储视频网址
    """

    def __init__(self, video_urls_list):
        """
        初始化class

        变量：
            video_queue：list 准备抓取的视频地址
        """

        self.insert_data_class = InsertData()
        self.video_queue = queue.Queue()
        for url in video_urls_list:
            self.video_queue.put(url)

    def start_threads(self):
        """
        创建线程 开始抓取并插入数据
        """

        threads_list = []
        for t in range(settings.THREAD_NUMBER):
            t = threading.Thread(target=self.extract_insert_video_data)
            threads_list.append(t)
            t.start()
        for t in threads_list:
            t.join()

    def extract_insert_video_data(self):
        """
        提取并插入视频数据
        """

        while not self.video_queue.empty():
            video_url = self.video_queue.get()
            meta_data = self.get_playlistId_and_vid(video_url)
            if meta_data:
                parsed_video = self.parse_video_data(meta_data, video_url)
                self.insert_data(parsed_video)
            self.video_queue.task_done()

    def get_playlistId_and_vid(self, video_url):
        """
        提取playlist_id, vid
        
        参数:
            video_url string 要获取的视频网址
        
        返回：
            若网页读取正常 返回playlist_id, vid 均为string
            若读取失败 返回False
        """

        r = requests.get(video_url)
        try:
            assert r.status_code == 200
            r.encoding = 'gbk'
            playlist_id = re.search(r'playlistId="(.*?)";', r.text).group(1)
            vid = re.search(r'vid="(.*?)";', r.text).group(1)
            return playlist_id, vid
        except AssertionError as e:
            print('无法读取网页', video_url)
            return False

    def parse_video_data(self, meta_data, video_url):
        """
        提取视频数据
        
        参数:
            meta_data tuple 包含(playlist_id, vid)
            video_url string 提取页面的地址
        
        返回：
            temp_video Video()实例
        """

        r = requests.get('http://pl.hd.sohu.com/videolist', params={'playlistid': meta_data[0], 'vid': meta_data[1]})
        if r.status_code == 200:
            info = json.loads(r.text)
            extra_video_info = self.extra_video_info(info, video_url)
            vote_info = self.get_vote_info(meta_data)
            temp_video = Video()

            temp_video.name = extra_video_info['name']
            temp_video.en_name = info['tvEnglishName']
            temp_video.thumbnail = extra_video_info['largePicUrl']
            temp_video.directors = str(info['directors'])
            temp_video.actors = str(info['actors'])
            temp_video.categories = str(info['categories'])
            temp_video.description = info['albumDesc']
            temp_video.page_url = video_url

            temp_video.album_name = info['albumName']
            temp_video.album_thumbnail = info['largeVerPicUrl']
            temp_video.album_page_url = info['albumPageUrl']
            temp_video.default_page_url = info['defaultPageUrl']

            temp_video.playlist_id = meta_data[0]
            temp_video.vid = meta_data[1]
            temp_video.pid = info['pid']

            temp_video.update_time = info['updateTime']
            temp_video.publish_year = info['publishYear']
            temp_video.area = info['area']
            temp_video.play_length = extra_video_info['playLength']
            temp_video.publish_time = extra_video_info['publishTime']

            temp_video.up_vote = int(vote_info[0])
            temp_video.down_vote = int(vote_info[1])

            return temp_video
        else:
            print('无法读取网页', video_url)

    def extra_video_info(self, info, video_url):
        """
        提取info中的video信息
        
        参数:
            info dict 从视频json中提取的dict
            video_url 要提取的视频网址
        
        返回：
            dict 包含info中的video信息
        """

        if len(info['videos']) == 1:
            return ast.literal_eval(str(info['videos'])[1:-1])
        else:
            for i in info['videos']:
                if i['pageUrl'] == video_url:
                    return i

    def get_vote_info(self, meta_data):
        """
        提取视频的vote信息

        参数:
            meta_data tuple 包含(playlist_id, vid)

        返回：
            (own_vote, up_vote) 均为int
        """

        params = {'vid': meta_data[1], 'type': '1'}
        r = requests.get('http://score.my.tv.sohu.com/digg/get.do', params=params)
        vote = json.loads(r.text.strip()[1:-1])
        down_vote = int(vote['downCount'])
        up_vote = int(vote['upCount'])
        return down_vote, up_vote

    def insert_data(self, parsed_video):
        """
        将数据插入数据库

        参数:
            parsed_video Video()实例
        """

        self.insert_data_class.insert_into_database(parsed_video)
