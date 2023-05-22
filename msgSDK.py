import json
import hashlib
import urllib.parse
from flask import request

class CallbackSDK:
    def __init__(self):
        self.app_secret = "" # 私有变量，存储 app_secret

    # 设置 app_key 对应的 app_secret
    def setAppSecret(self, app_secret):
        self.app_secret = app_secret # 赋值给私有变量

    # 获取推送来的的数据
    # 必须使用 request.data 方法获取 post 过来的原始数据来解析
    def getPostMsgStr(self):
        return json.loads(request.data) # 返回解析后的 JSON 对象

    # 验证签名
    # 根据 app_secret, timestamp 和 nonce 生成一个哈希值，与 signature 进行比较
    def checkSignature(self, signature, timestamp, nonce):
        tmpArr = [self.app_secret, timestamp, nonce] # 创建一个列表
        tmpArr.sort() # 对列表进行排序
        tmpStr = hashlib.sha1("".join(tmpArr).encode('utf-8')).hexdigest()

        if tmpStr == signature: # 如果哈希值和签名相同
            return True # 返回 True
        else: # 否则
            return False # 返回 False

    # 组装返回数据
    # 包括 sender_id, receiver_id, type 和 data
    def buildReplyMsg(self, receiver_id, sender_id, data, type):
        msg = {
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "type": type,
            # data 字段需要进行 urlencode 编码
            "data": urllib.parse.quote(json.dumps(data))
        }
        return msg

    # 生成 text 类型的回复消息内容
    # 包括 text 字段
    def textData(self, text):
        data = {"text": text}
        return data

    # 生成 article 类型的回复消息内容
    # 包括 articles 字段
    def articleData(self, articles):
        data = {"articles": articles}
        return data

    # 生成 position 类型的回复消息内容
    # 包括 longitude 和 latitude 字段
    def positionData(self, longitude, latitude):
        data = {
            "longitude": longitude,
            "latitude": latitude
        }
        return data
