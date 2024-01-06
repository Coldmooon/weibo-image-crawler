import json
import re
import requests
from requests.adapters import HTTPAdapter
import os

headers = {'User_Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
 'Cookie': ''}

    
def get_page_id(url):
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

def weibo_pagesource(page_id):
    
    request_link = "https://weibo.com/ajax/statuses/show?id=" + page_id
    r = requests.get(request_link, headers=headers, verify=False)
    return r.json()

def get_page_type(response):
    page_type = ''
    if 'mix_media_info' in response.keys():
        page_type = 'multimedia'
    elif 'page_info' in response.keys():
        page_type = 'video'
    elif 'pic_infos' in response.keys():
        page_type = 'images'
    else:
        page_type = 'Unknown'

    return page_type

def get_pic_type(response, pic_id):
    # type:
    #       pic: photo
    #       livephoto: live photo

    media_type = response['pic_infos'][pic_id]['type']
    return media_type


def get_media_urls(response, page_type):

    media_urls = []

    if page_type == 'multimedia': 
        num_medias = len(response['mix_media_info']['items'])
        for i in range(num_medias):
            media = response['mix_media_info']['items'][i]
            if 'pic' == media['type']:
                media_urls += [{'url': media['data']['largest']['url'],
                                'media_id': media['data']['pic_id'],
                                'media_type': 'pic'}]
            elif 'video' == media['type']:
                video_url = media['data']['media_info']['mp4_720p_mp4'] or \
                            media['data']['media_info']['stream_url_hd']

                media_urls += [{'url': video_url, 
                                'media_id': media['data']['media_info']['media_id'],
                                'media_type': 'video'}]
            else:
                print('unknown media type in multi-media page...')
         
    elif page_type == 'video':
        video_url = response['page_info']['media_info']['mp4_720p_mp4'] or \
                    response['page_info']['media_info']['stream_url_hd']

        media_urls += [{'url': video_url,
                        'media_id':  response['page_info']['media_info']['media_id'],
                        'media_type': 'video'}]

    elif page_type == 'images':
        pic_ids = response['pic_ids']
        # Note: 如果是转发微博，那么会有多个 pic_ids，其中当前微博的 pic_ids 是空，而被转发微博的 pic_ids 正常。
        for pic_id in pic_ids: 
            pic_type = get_pic_type(response, pic_id)
            if pic_type == "pic":
                media_urls += [{'url': response['pic_infos'][pic_id]['largest']['url'],
                                'media_id': pic_id,
                                'media_type': 'pic'}]
            elif (pic_type == "livephoto"):
                media_urls += [{'url': response['pic_infos'][pic_id]['video'],
                                'media_id': pic_id,
                                'media_type': 'livephoto'}]
    else:
        print("No urls catched for new type of weibo_page.")

    return media_urls


def get_user_info(response):
    user = {}
    user['screen_name'] = response['user']['screen_name']
    user['uid'] = str(response['user']['id'])
    
    return user

def download_media(url, file_path, uid):
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

    page_id = get_page_id(url)
    response = weibo_pagesource(page_id)

    user_info = get_user_info(response)
    user_folder = user_info['screen_name'] + "_" + user_info['uid']
    save_folder = save_folder + "/" + user_folder
    if not os.path.isdir(save_folder):
        os.makedirs(save_folder)

    page_type = get_page_type(response)
    media_urls = get_media_urls(response, page_type)

    for i in range(len(media_urls)):
        media = media_urls[i]

        media_url = media['url']
        media_type = media['media_type']
        media_id = media['media_id']

        if "pic" == media_type:
            save_name = save_folder + "/" + media_id + ".jpg"
        elif "video" == media_type:
            save_name = save_folder + "/" + media_id + ".mp4"
        elif "livephoto" == media_type:
            save_name = save_folder + "/" + media_id + ".mov"

        download_media(media_url, save_name, user_info['uid'])

    print("Finished downloading user: ", user_info['screen_name'])
