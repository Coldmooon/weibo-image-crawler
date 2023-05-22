import sys
import hashlib
import json
from flask import Flask, request

from weibo import weibo_image_download as wb
import re

# 导入 CallbackSDK 类
from msgsdk import CallbackSDK

# 设置 app_key 对应的 app_secret
app_secret = "5fda2753c4af0e8c02fdb8afb92a8f0c"

# 初始化 SDK
call_back_SDK = CallbackSDK()
call_back_SDK.setAppSecret(app_secret)

# 验证签名
def verify():
    signature = request.args.get("signature")
    timestamp = request.args.get("timestamp")
    nonce = request.args.get("nonce")
    if not call_back_SDK.checkSignature(signature, timestamp, nonce):
        return "check signature error"

    # 首次验证 url 时会有 'echostr' 参数，后续推送消息时不再有 'echostr' 字段
    # 若存在 'echostr' 说明是首次验证，则返回 'echostr' 的内容
    if request.args.get("echostr"):
        return request.args.get("echostr")

    # 处理开放平台推送来的消息，首先获取推送来的数据
    post_msg_str = call_back_SDK.getPostMsgStr()

    # 设置接口默认返回值为空字符串
    # 请注意数据编码类型，接口要求返回的字符串需要是 utf8 编码
    # 需要说明的是开放平台判断推送成功的标志是接口返回的 http 状态码
    # 只要应用的接口返回的状态为 200 就会认为消息推送成功，如果 http 状态码不为 200 则会重试，共重试 3 次
    str_return = ""

    if post_msg_str:
        text_received = post_msg_str["text"]
        print("Text: \n", text_received)
        pattern = re.compile(r'https?://weibo.com/(\d+)/?(\w+)?')

        # 尝试匹配链接中的UID和页面ID
        match = pattern.match(text_received)
        if match:
            print("Matched. Start downloading...")
            wb(text_received, "test")

        # sender_id 为发送回复消息的 uid，即蓝 v 自己
        sender_id = post_msg_str["receiver_id"]
        # receiver_id 为接收回复消息的 uid，即蓝 v 的粉丝
        receiver_id = post_msg_str["sender_id"]

        # 回复 text 类型的消息示例
        data_type = "text"
        data = call_back_SDK.textData("真不错啊！好看！")

        # 回复 articles 类型的消息示例
        # data_type = "articles"
        # article_data = [
        #     {
        #         "display_name": "第一个故事",
        #         "summary": "今天讲两个故事，分享给你。谁是公司？谁又是中国人？",
        #         "image": "http://storage.mcp.weibo.cn/0JlIv.jpg",
        #         "url": "http://e.weibo.com/mediaprofile/article/detail?uid=1722052204&aid=983319"
        #     },
        #     {
        #         "display_name": "第二个故事",
        #         "summary": "今天讲两个故事，分享给你。谁是公司？谁又是中国人？",
        #         "image": "http://storage.mcp.weibo.cn/0JlIv.jpg",
        #         "url": "http://e.weibo.com/mediaprofile/article/detail?uid=1722052204&aid=983319"
        #     }
        # ]
        # data = call_back_SDK.articleData(article_data)

        # 回复 position 类型的消息示例
        # data_type = "position"
        # longitude = "123.01"
        # latitude = "154.2"
        # data = call_back_SDK.positionData(longitude, latitude)
        
        str_return = call_back_SDK.buildReplyMsg(receiver_id, sender_id, data, data_type)

    return json.dumps(str_return)
