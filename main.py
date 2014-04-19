#! /usr/bin/env python3

import sys

from get_data import GetVideoUrls, ExtractAndInsertVideoData
import settings


def main():
    """
    开始抓取程序
    """

    url, limit = get_url_and_limit()
    print('url:', url, 'limit:', limit)
    url_getter = GetVideoUrls(url, limit)
    video_urls_list = url_getter.get_video_urls()
    data_paser = ExtractAndInsertVideoData(video_urls_list)
    data_paser.start_threads()
    print('完成')
    return 0


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


if __name__ == '__main__':
    sys.exit(main())