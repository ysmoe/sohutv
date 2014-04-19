sohutv
==============================

抓取搜狐视频基本信息


----------

###Requirement

[Requests](http://docs.python-requests.org/en/latest/)

[SQLAlchemy](http://www.sqlalchemy.org/)

[Python3](https://www.python.org/downloads/)

----------
###Usage
程序需要两个参数 sohu视频分类检索网页的网址 及 视频数量限制（默认为抓取所有检索结果的前1000个视频）

更多分类可在[sohu分类检索](http://so.tv.sohu.com/list_p11_p2_p3_p4-1_p5_p6_p70_p80_p9_2d2_p101_p11.html)中找到

main.py 程序入口

settings.py 可设置线程数及数据库参数

	python tv.py http://so.tv.sohu.com/list_p1100_p20_p3_p40_p5_p6_p77_p80_p9_2d0_p101_p11.html 2000

----------
###Screenshot
![截图](https://raw.github.com/bebound/sohutv/master/screenshot/1.png)