# weibo-image-crawler
从一条特定的微博中下载所有的高清大图、livephoto动图、高清视频。那些需要订阅收费才能观看的图片和视频也可利用本工具免费爬取获得。

# Usage
1. 获取一条微博链接。链接的形式有两种：
- 短码链接： https://weibo.com/5573443261/MFWrOyfe5
- 长码链接： https://weibo.com/5573443261/4899961248161685

这两个链接指向同一个微博页面。

2.
下载一条微博的所有高清大图/livephoto动图/高清视频:
```
python main.py -l https://weibo.com/5573443261/MFWrOyfe5
```

下载多条微博的所有高清大图/livephoto动图/高清视频，可以把微博链接放到一个文本文件里，每个链接占一行:
```
python main.py -f links.txt
```

设定图片存储到本地 images 目录下:
```
python main.py -f links.txt -s images
```
