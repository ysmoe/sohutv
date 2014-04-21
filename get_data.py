#! /usr/bin/env python3



import ast
import json
import math
import queue
import re
import requests
import threading
import time

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
        video_page_queue queue 包含视频的页面地址队列
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
        self.video_page_queue = queue.Queue()
        self.video_urls_list = []

    def get_video_urls(self):
        """
        提取视频网址 直到满足limit限制

        返回：
            self.video_urls_list list 所有获取到的视频网址
        """

        total_page_urls = self.get_total_page_urls(self.start_url)
        for page in total_page_urls:
            self.video_page_queue.put(page)
        self.start_extract_video_urls()
        print('视频网址获取完成')
        return self.video_urls_list


    def get_total_page_urls(self, start_page):
        """
        获取到所有满足limit限制的视频页面

        参数:
            start_page string 起始网址

        返回：
            total_page_urls list 所有满足limit限制的视频页面
        """

        end_page_url = self.get_end_page_url()
        if end_page_url:
            end_page_number = self.split_url(end_page_url)[1]
            begin_url, start_page_number, end_url = self.split_url(start_page)
            grab_end_page = self.calculate_grab_end_page(start_page_number, end_page_number)
            total_page_urls = []
            for page in range(start_page_number, grab_end_page + 1):
                total_page_urls.append(self.joint_url(begin_url, page, end_url))
            return total_page_urls
        else:
            return [start_page]

    def get_end_page_url(self):
        """
        根据起始网址分析出此分类的末页地址

        返回
            若网页存在末页 返回end_page_url string
            若不存在或与起始页相同 返回False
        """

        parse = self.parse_url(self.start_url)
        end_page_tag = parse.select('div.num a')[-1]
        end_page_relative_url = re.search(r'href="(.*?)"', str(end_page_tag)).group(1)
        base_url = self.start_url.split('/')[2]
        end_page_url = 'http://' + base_url + end_page_relative_url
        start_page_number = self.split_url(self.start_url)[1]
        end_page_number = self.split_url(end_page_url)[1]
        return end_page_url if end_page_number > start_page_number else False

    def parse_url(self, page_url):
        """
        获取页面信息

        返回：
            若网页正常打开 返回BeautifulSoup处理后的页面
            若出现异常 返回False
        """

        print('parse_url', page_url)
        r = requests.get(page_url)
        try:
            assert r.status_code == 200
            parse = BeautifulSoup(r.text)
            return parse
        except AssertionError as e:
            print('无法读取网页', page_url)
            return False

    def split_url(self, page_url):
        """
        分割网址 提取需要的信息

        参数：
            page_url string 要分割的网址

        返回：
            begin_url, page_number, end_url  前半部分网址(string) 页码(int) 后半部分网址(string)
        """

        begin_url = re.search(r'(^.*p10)(\d*)(_p\d*\.html$)', page_url).group(1)
        page_number = re.search(r'(^.*p10)(\d*)(_p\d*\.html$)', page_url).group(2)
        end_url = re.search(r'(^.*p10)(\d*)(_p\d*\.html$)', page_url).group(3)
        return begin_url, int(page_number), end_url

    def calculate_grab_end_page(self, start_page_number, end_page_number):
        """
        计算出抓取页面的结束页码

        参数:
            start_page_number int 起始页码
            end_page_number int 视频末页页码

        返回:
            end_page_number int 要抓取的结束页码
        """

        if self.limit:
            temp_end_page_number = start_page_number + math.ceil(self.limit / 20) - 1
            return temp_end_page_number if temp_end_page_number < end_page_number else end_page_number
        else:
            return end_page_number

    def joint_url(self, begin_url, page, end_url):
        """
        拼接网址

        参数：
            begin_url string 前半部分网址
            page int 页码
            end——url string 后半部分网址

        返回：
            jointed_url string 拼接后的网址
        """

        jointed_url = begin_url + str(page) + end_url
        return jointed_url

    def start_extract_video_urls(self):
        """
        开始从视频页面提取单独的视频地址
        """

        th = []
        for i in range(settings.THREAD_NUMBER):
            t = threading.Thread(target=self.add_current_page_video_urls)
            t.start()
            th.append(t)
        for t in th:
            t.join()

    def add_current_page_video_urls(self):
        """
        提取视频页面内的视频网址 将网址加入self.video_urls_list
        """

        while not self.video_page_queue.empty():
            current_page = self.video_page_queue.get()
            parse = self.parse_url(current_page)
            video_div_list = parse.select('div.info')
            temp_video_link_list = []
            for video_div in video_div_list:
                url = re.search(r'href="(.*?)"', str(video_div)).group(1)
                temp_video_link_list.append(url)
            self.video_urls_list.extend(temp_video_link_list)
            self.video_page_queue.task_done()


class ExtractAndInsertVideoData(object):
    """
    从视频网址提取视频信息 并将数据插入数据库

    属性：
        insert_data_class InsertData的实例 负责插入数据
        video_queue queue 存储视频网址
        terminate_thread bool 线程是否应该结束
        threads_list list 所有开始的线程
    """

    def __init__(self, video_urls_list):
        """
        初始化class

        变量：
            video_queue：list 准备抓取的视频地址
        """

        self.insert_data_class = InsertData()
        self.video_queue = queue.Queue()
        self.terminate_thread = False
        for url in video_urls_list:
            self.video_queue.put(url)

    def set_terminate_thread(self):
        self.terminate_thread = True

    def start_threads(self):
        """
        创建线程 开始抓取并插入数据
        """

        self.threads_list = []
        for t in range(settings.THREAD_NUMBER):
            t = threading.Thread(target=self.extract_insert_video_data)
            self.threads_list.append(t)
            t.start()
        while True:
            alive_threads = list(filter(lambda x: x.is_alive(), self.threads_list))
            if not len(alive_threads):
                break
            else:
                time.sleep(1)

    def extract_insert_video_data(self):
        """
        提取并插入视频数据
        """

        while not self.video_queue.empty() and not self.terminate_thread:
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
            if r.status_code == 200:
                r.encoding = 'gbk'
                playlist_id = re.search(r'playlistId="(.*?)";', r.text).group(1)
                vid = re.search(r'vid="(.*?)";', r.text).group(1)
                return playlist_id, vid
        except:
            print('无法读取网页', video_url)

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
            if vote_info:
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
        try:
            params = {'vid': meta_data[1], 'type': '1'}
            r = requests.get('http://score.my.tv.sohu.com/digg/get.do', params=params)
            vote = json.loads(r.text.strip()[1:-1])
            down_vote = int(vote['downCount'])
            up_vote = int(vote['upCount'])
            return down_vote, up_vote
        except:
            print('获取投票信息失败', r.url)

    def insert_data(self, parsed_video):
        """
        将数据插入数据库

        参数:
            parsed_video Video()实例
        """

        self.insert_data_class.insert_into_database(parsed_video)
