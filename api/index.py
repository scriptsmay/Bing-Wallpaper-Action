# coding:utf-8
from http.server import BaseHTTPRequestHandler
import redis
import os
from datetime import datetime

def get_now_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_redis_client():
    """获取 Redis 客户端"""
    return redis.Redis(
        host=os.environ.get('REDIS_HOST'),
        port=os.environ.get('REDIS_PORT'),
        password=os.environ.get('REDIS_PASSWORD'),
        ssl=True,
        decode_responses=True,  # 自动解码，不需要手动 decode
        socket_connect_timeout=5,
        socket_timeout=5
    )

def get_bing():
    """获取随机 Bing 图片 URL"""
    try:
        r = get_redis_client()
        
        # 检查集合是否存在且不为空
        if not r.exists("bing_images"):
            return None, "图片集合不存在"
        
        count = r.scard("bing_images")
        if count == 0:
            return None, "图片集合为空"
        
        # 获取随机图片
        # srandmember 返回一个随机元素，count=1 表示返回1个
        random_image = r.srandmember("bing_images", 1)
        
        if not random_image:
            return None, "获取随机图片失败"
        
        # 由于 decode_responses=True，已经是字符串，不需要 decode
        _params_data = random_image[0]
        
        # 构建完整 URL
        if "_1920x1080" in _params_data:
            full_url = "https://bing.com" + _params_data.split("_1920x1080")[0] + "_UHD.jpg"
        else:
            full_url = "https://bing.com" + _params_data
            
        return full_url, None
        
    except Exception as e:
        return None, f"Redis 错误: {str(e)}"

def url_redirect(self, url):
    """执行 URL 重定向"""
    self.send_response(308)  # 使用 308 永久重定向，便于缓存
    self.send_header('Access-Control-Allow-Origin', '*')
    self.send_header('Location', url)
    self.send_header('Cache-Control', 'max-age=0, s-maxage=86400, stale-while-revalidate=3600')  # 缓存24小时
    self.send_header('Content-type', 'text/plain')
    self.end_headers()
    self.wfile.write('Redirecting to {} (308)'.format(url).encode('utf-8'))

def url_error(self, message):
    """返回错误信息"""
    self.send_response(500)
    self.send_header('Content-type', 'application/json')
    self.send_header('Access-Control-Allow-Origin', '*')
    self.end_headers()
    error_response = {
        "status": "error",
        "message": message,
        "timestamp": get_now_time()
    }
    self.wfile.write(json.dumps(error_response).encode('utf-8'))

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 添加对根路径的访问支持
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Bing Image Redirect Service is running!')
            return
        
        # 获取随机图片
        image_url, error = get_bing()
        
        if error:
            # 返回错误信息
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = {
                "status": "error",
                "message": error,
                "timestamp": get_now_time()
            }
            import json
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
        else:
            # 执行重定向
            url_redirect(self, image_url)