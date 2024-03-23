import json
import re
import requests
from requests.adapters import HTTPAdapter
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

headers = {
    'User_Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
}

cookies = [
    'XSRF-TOKEN=df6_295NgzFvJXS5Ebir3Lsy; SUB=_2AkMSoQfrf8NxqwFRmfsVyG3mbYp3wgjEieKk_fYwJRMxHRl-yT9vqlIAtRB6OSEpBFcGiARBOAnwKhC5ZrKPs-0Tb0Qo; SUBP=0033WrSXqPxfM72-Ws9jqgMF55529P9D9WWFg0fG6cq3oE2bqhsoAldV; WBPSESS=gJ7ElPMf_3q2cdj5JUfmvGVqkHB92RE2_AwewsrjYWIBFCA1ZPKYgsEdwAzm6brHYlW5B6maWDy-hBEgLCyxVoJJry48tUmcvk0HOSyHP_39vQbgHUQVhjsEpRu0qJLNziegtrfv2J4r-EEdKdga-YSfVBhzDTG8azkZAaaS7Pw=',
    'XSRF-TOKEN=df6_295NgzFvJXS5Ebir3Lsy; _s_tentry=-; Apache=6386009078674.588.1711119828939; SINAGLOBAL=6386009078674.588.1711119828939; ULV=1711119828990:1:1:1:6386009078674.588.1711119828939:; ALF=1713761012; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WWuyTE2R_nVVR8Gh5or-UwK5JpX5KzhUgL.FoeNeKM4eh2pehe2dJLoIEBLxK-LBozLB-BLxKBLB.2L1K2LxKqL1KMLB.2LxKqL1-eL1hnt; SUB=_2A25I-vXPDeRhGeVJ6lUY8C_Nyz-IHXVodncHrDV8PUJbn9AGLRfgkW1NT-K3eh5dPZM9ZF7BK1xxHGc5IPJnHuMf; PC_TOKEN=f7723f2711; WBPSESS=HRGrvUX5o6Tu2aaaIhJAc5AQgyd_ChArhzxpTq2G3firFqV8woflsEY-USPTjze-BoOqGxKWzJs_RNqUxg8KLzjyZVqLaIkbmQaoOqD2zfduwsrQg_Im_Rf7wmjlKZHFecpsx1yYhPLc5CTwHO7KuQ==',
]

def extract_redirected_link(short_link):
    try:
        response = requests.get(short_link, headers=headers, allow_redirects=False)
        if response.status_code == 200:
            for key, value in response.__dict__.items():
                print(f"{key}: {value}")
            return None
        elif response.status_code == 302:
            # Extract the redirection URL from the Location header
            if 'Location' in response.headers:
                final_url = response.headers['Location']
                return final_url
            else:
                print("Error: Redirection URL not found in response headers.")
                return None
        else:
            print(f"Error: Unable to access {short_link}. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None
    
def get_page_id(url):
    # 匹配UID和页面ID的正则表达式
    if "t.cn" in url:
        url = extract_redirected_link(url)

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

def weibo_pagesource(page_id, cookies):

    headers_copy = headers.copy()
    
    for cookie in cookies:
        headers_copy['Cookie'] = cookie
        request_link = "https://weibo.com/ajax/statuses/show?id=" + page_id

        response = requests.get(request_link, headers=headers_copy)
        if response.ok:
            try:
                data = response.json()
                return data
            except ValueError:
                print("Failed to decode JSON. Response was:", response.text)
        elif response.status_code == 400:
            print("Request failed with status code 400. Trying next cookie.")
            continue
        else:
            print("Request failed with status code:", response.status_code)
            return ""

    print("All cookies failed. Unable to retrieve data.")
    return ""

def get_page_type(response):
    page_type = ''
    if 'mix_media_info' in response.keys():
        page_type = 'multimedia'
    elif 'pic_infos' in response.keys() and 'pic_ids' in response.keys() and 'pic_num' in response.keys():
        page_type = 'images'
    # Note: Some picture weibo also has the 'page_info' field, e.g., https://weibo.com/2687932353/O594VFGac
    elif 'page_info' in response.keys() and 'media_info' in response['page_info'].keys():
        page_type = 'video'
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
    downloader_headers = {
        'User_Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Referer': 'https://weibo.com/',
        'Sec_Fetch_Site': 'cross-site',
        'Cookie': 'XSRF-TOKEN=df6_295NgzFvJXS5Ebir3Lsy; SUB=_2AkMSoQfrf8NxqwFRmfsVyG3mbYp3wgjEieKk_fYwJRMxHRl-yT9vqlIAtRB6OSEpBFcGiARBOAnwKhC5ZrKPs-0Tb0Qo; SUBP=0033WrSXqPxfM72-Ws9jqgMF55529P9D9WWFg0fG6cq3oE2bqhsoAldV; WBPSESS=gJ7ElPMf_3q2cdj5JUfmvGVqkHB92RE2_AwewsrjYWIBFCA1ZPKYgsEdwAzm6brHYlW5B6maWDy-hBEgLCyxVoJJry48tUmcvk0HOSyHP_39vQbgHUQVhjsEpRu0qJLNziegtrfv2J4r-EEdKdga-YSfVBhzDTG8azkZAaaS7Pw=; _s_tentry=-; Apache=6386009078674.588.1711119828939; SINAGLOBAL=6386009078674.588.1711119828939; ULV=1711119828990:1:1:1:6386009078674.588.1711119828939:',
    }
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
                #url, headers=downloader_headers, timeout=(5, 10), verify=False
                url, headers=downloader_headers, timeout=(5, 10)
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
    save_folder = os.path.join(save_folder, user_folder)
    if not os.path.isdir(save_folder):
        os.makedirs(save_folder)

    page_type = get_page_type(response)
    media_urls = get_media_urls(response, page_type)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for media in media_urls:
            media_url = media['url']
            media_type = media['media_type']
            media_id = media['media_id']
            if 'pic' == media_type:
                save_name = os.path.join(save_folder, media_id + '.jpg')
            elif 'video' == media_type:
                save_name = os.path.join(save_folder, media_id + '.mp4')
            elif 'livephoto' == media_type:
                save_name = os.path.join(save_folder, media_id + '.mov')

            future = executor.submit(download_media, media_url, save_name, user_info['uid'])
            futures.append(future)

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                print('There was an exception: %s' % exc)

    print("Finished downloading user: ", user_info['screen_name'])
