# coding:utf-8
from http.server import BaseHTTPRequestHandler
import redis
import os
from datetime import datetime

# 定义域名
DOMAIN = "https://wallpaper.virola.me"

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

def render_home_page():
    """渲染首页"""
    return f"""
<!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Wallpaper Image API</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
            .container {{ background: #f5f5f5; padding: 20px; border-radius: 8px; }}
            code {{ background: #eee; padding: 2px 6px; border-radius: 3px; }}
            .endpoint {{ margin: 15px 0; padding: 10px; background: white; border-left: 4px solid #007cba; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🖼️ Wallpaper Image API</h1>
            <p>这是一个简单的壁纸图片 API 服务</p>
            <h2>📚 API 端点</h2>
            <div class="endpoint">
                <h3>获取所有图片列表</h3>
                <p><code>GET /api/images</code></p>
                <p><strong>参数:</strong> <code>sort</code> (alphabetical, reverse, random), <code>format</code> (json, image)</p>
                <p><strong>示例:</strong> <a href="/api/images" target="_blank">/api/images</a></p>
            </div>
            <div class="endpoint">
                <h3>获取最新图片</h3>
                <p><code>GET /api/images/latest</code></p>
                <p><strong>参数:</strong> <code>format</code> (json, image)</p>
                <p><strong>示例:</strong> 
                    <a href="/api/images/latest" target="_blank">JSON格式</a> | 
                    <a href="/api/images/latest?format=image" target="_blank">直接跳转图片</a>
                </p>
            </div>
            
            <div class="endpoint">
                <h3>获取指定位置图片</h3>
                <p><code>GET /api/images/position/{{number}}</code></p>
                <p><strong>参数:</strong> <code>format</code> (json, image)</p>
                <p><strong>示例:</strong> 
                    <a href="/api/images/position/0" target="_blank">第1张(JSON)</a> | 
                    <a href="/api/images/position/0?format=image" target="_blank">第1张(图片)</a>
                </p>
            </div>

            <div class="endpoint">
                <h3>获取今日壁纸（缓存24小时）</h3>
                <p><code>GET /api/images/today</code></p>
                <p><strong>参数:</strong> <code>format</code> (json, image)</p>
                <p><strong>示例:</strong> 
                    <a href="/api/images/today" target="_blank">JSON格式</a> | 
                    <a href="/api/images/today?format=image" target="_blank">直接跳转图片</a>
                </p>
            </div>
            
            <h2>🔄 使用方式</h2>
            <pre><code># 获取随机图片
curl -L "{DOMAIN}/api/images?format=image"

# 获取最新图片信息
curl "{DOMAIN}/api/images/latest"

# 获取所有图片列表
curl "{DOMAIN}/api/images?sort=random"

# 获取今日壁纸
curl -L "{DOMAIN}/api/today?format=image"
</code></pre>
        </div>
    </body>
</html>
    """

class handler(BaseHTTPRequestHandler):
    def send_html_response(self, content):
        """发送HTML响应"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            html_content = render_home_page()
            self.send_html_response(html_content)
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