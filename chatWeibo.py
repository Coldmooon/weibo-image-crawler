# 导入 flask 模块
from flask import Flask, request
# 导入 msg 模块
import msg 
import sys

# 创建一个 flask 应用对象
app = Flask(__name__)

# 定义一个路由函数，使用 app.route 装饰器
@app.route("/", methods=["GET", "POST"])
def index():
    # 调用 demo 模块里的 demo 函数，返回结果
    return msg.verify()

# 在文件的最后运行 flask 应用对象
if __name__ == "__main__":
  port = int(sys.argv[1]) if len(sys.argv) > 1 else 80
  app.run(host="0.0.0.0", port=port)
