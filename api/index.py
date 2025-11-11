# coding:utf-8
from http.server import BaseHTTPRequestHandler
import redis
import os

# 初始化 Redis
r = redis.Redis(
    host=os.environ.get('REDIS_HOST'),
    port=os.environ.get('REDIS_PORT'),
    password=os.environ.get('REDIS_PASSWORD'),
    ssl=True,
    decode_responses=True
)


def get_bing():
    _params_data = r.srandmember("bing_images", -1)[0].decode('utf-8')
    # full_uel = "https://bing.com" + _params_data.split("_1920x1080")[0] + "_UHD.jpg"
    full_uel = "https://bing.com" + _params_data
    return full_uel


def get_now_time():
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def url_redirect(self, url):
    self.send_response(307)  # vercel 只有 308 跳转才可以缓存 详情见官方文档
    self.send_header('Access-Control-Allow-Origin', '*')
    self.send_header('location', url)  # 这个是主要的
    self.send_header('Refresh', '0;url={}'.format(url))
    # self.send_header('Cache-Control', 'max-age=0, s-maxage=60, stale-while-revalidate=3600')  # vercel 缓存
    self.send_header('Content-type', 'text/plain')
    self.end_headers()
    self.wfile.write('Redirecting to {} (308)'.format(url).encode('utf-8'))  # 这里无所谓
    return None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        params_data = get_bing()
        url_redirect(self, params_data)
        return None


