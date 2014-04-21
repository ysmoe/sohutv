#! /usr/bin/env python3

import os
import pickle
import sys
import time

from get_data import GetVideoUrls, ExtractAndInsertVideoData
import settings


def main():
    """
    程序入口 开始抓取程序
    """
    if os.path.exists('queue.pickle'):
        if choose_task():
            continue_old_task()
        else:
            os.remove('queue.pickle')
            start_new_task()
    else:
        start_new_task()


def start_new_task():
    """
    开始新任务
    """
    try:
        url, limit = get_url_and_limit()
        print('url:', url, 'limit:', limit)
        url_getter = GetVideoUrls(url, limit)
        video_urls_list = url_getter.get_video_urls()
        data_paser = ExtractAndInsertVideoData(video_urls_list)
        data_paser.start_threads()
        print('完成')
        return 0
    except KeyboardInterrupt:
        if 'data_paser' in dir():
            data_paser.set_terminate_thread()
            dump_queue(data_paser)


def choose_task():
    """
    选择是否继续未完成任务

    返回:
        继续未完成任务 返回True
        开始新任务 返回False
    """
    while True:
        choice = input('存在未完成队列\n1 继续未完成任务\n2 开始新任务\n')
        if choice == '1':
            return True
        elif choice == '2':
            return False
        else:
            print('输入错误')


def continue_old_task():
    """
    继续未完成任务
    """
    try:
        with open('queue.pickle', 'rb') as f:
            queue_list = pickle.load(f)
        print('已读取旧队列，共有', len(queue_list), '个任务')
        data_paser = ExtractAndInsertVideoData(queue_list)
        data_paser.start_threads()
        print('完成')
        os.remove('queue.pickle')
        return 0
    except KeyboardInterrupt:
        if 'data_paser' in dir():
            dump_queue(data_paser)


def get_url_and_limit():
    """
    获取url和limit

    返回：
        (url, limit) url为string limit为int
    """

    url = ''
    limit = 0
    if settings.DEBUG:
        url = 'http://so.tv.sohu.com/list_p1100_p20_p3_u9999_u6e2f_p40_p5_p6_p77_p80_p9_2d0_p101_p11.html'
        limit = 1000
    elif len(sys.argv) > 1:
        try:
            url = sys.argv[1]
            limit = int(sys.argv[2])
        except:
            pass
    else:
        url = input('url:')
        limit = int(input('limit(0为不限制):'))
    return url, limit


def dump_queue(data_paser):
    """
    保存未完成的queue至queue.pickle
    """
    while True:
        alive_threads = list(filter(lambda x: x.is_alive(), data_paser.threads_list))
        if not len(alive_threads):
            break
        else:
            time.sleep(1)
    with open('queue.pickle', 'wb') as f:
        queue_list = []
        while not data_paser.video_queue.empty():
            queue_list.append(data_paser.video_queue.get())
        pickle.dump(queue_list, f)
    print('video_queue已保存至video_queue')


if __name__ == '__main__':
    sys.exit(main())