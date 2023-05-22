import json
import re
import requests
from requests.adapters import HTTPAdapter
import os

headers = {'User_Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
 'Cookie': ''}

    
def extract_pageid_from_link(url):
    # 匹配UID和页面ID的正则表达式
    pattern = re.compile(r'https?://weibo.com/(\d+)/?(\w+)?')
    
    # 尝试匹配链接中的UID和页面ID
    match = pattern.match(url)
    if match:
        uid = match.group(1)
        if match.group(2):
            page_id = match.group(2)
        else:
            # 如果页面ID没有在链接中指定，则默认为最后一个字符
            page_id = url[-1]
        return page_id
    
    # 如果链接格式不正确，则返回None
    return None

def weibo_page(page_id):
    request_link = "https://weibo.com/ajax/statuses/show?id=" + page_id
    r = requests.get(request_link, headers=headers, verify=False)

    return r.json()

def get_pics_url(response):
    # Note: 如果是转发微博，那么会有多个 pic_ids，其中当前微博的 pic_ids 是空，而被转发微博的 pic_ids 正常。
    pic_urls = [response['pic_infos'][x]['largest']['url']  for x in pic_ids]
    pic_ids = response['pic_ids']

    return pic_urls, pic_ids

def get_user_info(response):
    user = {}
    user['screen_name'] = response['user']['screen_name']
    user['uid'] = str(response['user']['id'])
    
    return user

def download_image(url, file_path, uid):
    try:
        file_exist = os.path.isfile(file_path)
        need_download = (not file_exist)
        if not need_download:
            return 
        s = requests.Session()
        s.mount(url, HTTPAdapter(max_retries=5))
        try_count = 0
        success = False
        MAX_TRY_COUNT = 3
        while try_count < MAX_TRY_COUNT:
            downloaded = s.get(
                url, headers=headers, timeout=(5, 10), verify=False
            )
            try_count += 1
            fail_flg_1 = url.endswith(("jpg", "jpeg")) and not downloaded.content.endswith(b"\xff\xd9")
            fail_flg_2 = url.endswith("png") and not downloaded.content.endswith(b"\xaeB`\x82")
            if ( fail_flg_1  or fail_flg_2):
#                 logger.debug("[DEBUG] failed " + url + "  " + str(try_count))
                print("[DEBUG] failed ")
            else:
                success = True
#                 logger.debug("[DEBUG] success " + url + "  " + str(try_count))
                print("[DEBUG] success ")
                break
        if success: 
            if not file_exist:
                with open(file_path, "wb") as f:
                    f.write(downloaded.content)
#                     logger.debug("[DEBUG] save " + file_path )
                    print("saved")
        else:
#             logger.debug("[DEBUG] failed " + url + " TOTALLY")
            print("[DEBUG] failed " )
    except Exception as e:
        error_file = "not_downloaded.txt"
        with open(error_file, "ab") as f:
            url = str(uid) + ":" + file_path + ":" + url + "\n"
            f.write(url.encode(sys.stdout.encoding))
#         logger.exception(e)


def weibo_image_download(url, save_folder="images"):
    print("Downloading URL: ", url)
    page_id = extract_pageid_from_link(url)
    response = weibo_page(page_id)
    pic_urls, pic_ids = get_pics_url(response)
    
    user_info = get_user_info(response)
    user_folder = user_info['screen_name'] + "_" + user_info['uid']
    save_folder = save_folder + "/" + user_folder

    if not os.path.isdir(save_folder):
        os.makedirs(save_folder)
    for pic_url, pic_id in zip(pic_urls, pic_ids):
        img_save_name = save_folder + "/" + pic_id + ".jpg"
        download_image(pic_url, img_save_name, user_info['uid'])
