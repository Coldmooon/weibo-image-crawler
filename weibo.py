import json
import re
import requests
from requests.adapters import HTTPAdapter
import os

headers = {'User_Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
 'Cookie': ''}

    
def get_pageID(url):
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

def get_content_list(response):
    
    pic_ids = response['pic_ids']
    return pic_ids

def get_media_type(response, pic_id):
    # type:
    #       pic: photo
    #       livephoto: live photo

    media_type = response['pic_infos'][pic_id]['type']
    return media_type

def get_pics_url(response, pic_ids):
    # Note: 如果是转发微博，那么会有多个 pic_ids，其中当前微博的 pic_ids 是空，而被转发微博的 pic_ids 正常。
    if pic_ids is None:
        pic_ids = response['pic_ids']
    pic_urls = [response['pic_infos'][x]['largest']['url']  for x in pic_ids]
    return pic_urls

def get_livephoto_url(response, pic_id):
    
    livephoto_url = response['pic_infos'][pic_id]['video']
    return livephoto_url

def get_video_url(response):

    return response['page_info']['media_info']['mp4_720p_mp4']

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
            fail_flg_3 = url.endswith("mov") and False # to do: Verify mov file status
            fail_flg_4 = url.endswith(",video") and False
            if ( fail_flg_1  or fail_flg_2 or fail_flg_3 or fail_flg_4):
#                 logger.debug("[DEBUG] failed " + url + "  " + str(try_count))
                print("[DEBUG] Download failed ")
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
            print("[DEBUG] Save failed " )
    except Exception as e:
        error_file = "not_downloaded.txt"
        with open(error_file, "ab") as f:
            url = str(uid) + ":" + file_path + ":" + url + "\n"
            f.write(url.encode(sys.stdout.encoding))
#         logger.exception(e)


def weibo_image_download(url, save_folder="images"):
    print("Downloading URL: ", url)

    page_id = get_pageID(url)
    response = weibo_page(page_id)

    user_info = get_user_info(response)
    user_folder = user_info['screen_name'] + "_" + user_info['uid']
    save_folder = save_folder + "/" + user_folder
    if not os.path.isdir(save_folder):
        os.makedirs(save_folder)

    pic_ids = get_content_list(response)

    if not pic_ids and 'page_info' in response:
        print("Download video...")
        video_url = get_video_url(response)
        save_name = save_folder + "/" + page_id + ".mp4"
        download_image(video_url, save_name, user_info['uid'])
        return
    if not pic_ids and not 'page_info' in response:
        return

    pic_urls = get_pics_url(response, pic_ids)

    for pic_url, pic_id in zip(pic_urls, pic_ids):
        media_type = get_media_type(response, pic_id)
        if (media_type == "pic"):
            save_name = save_folder + "/" + pic_id + ".jpg"
            download_image(pic_url, save_name, user_info['uid'])
        elif (media_type == "livephoto"):
            print("Downloading Livephoto...")
            save_name = save_folder + "/" + pic_id + ".mov"
            media_url = get_livephoto_url(response, pic_id)
            download_image(media_url, save_name, user_info['uid'])
        else:
            print("Unknown Media Type: ", media_type)
