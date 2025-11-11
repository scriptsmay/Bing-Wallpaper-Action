# api/images.py
from http.server import BaseHTTPRequestHandler
import json
import redis
import os
import urllib.parse

class Handler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.redis_client = None
        super().__init__(*args, **kwargs)
    
    def get_redis_client(self):
        """获取Redis客户端（单例）"""
        if self.redis_client is None:
            try:
                self.redis_client = redis.Redis(
                    host=os.environ.get('REDIS_HOST'),
                    port=os.environ.get('REDIS_PORT'),
                    password=os.environ.get('REDIS_PASSWORD'),
                    ssl=True,
                    decode_responses=True,
                    socket_connect_timeout=5
                )
                # 测试连接
                self.redis_client.ping()
            except Exception as e:
                raise Exception(f"Redis连接失败: {e}")
        return self.redis_client
    
    def parse_query_params(self, path):
        """解析查询参数"""
        if '?' in path:
            path, query = path.split('?', 1)
            params = urllib.parse.parse_qs(query)
            return path, {k: v[0] for k, v in params.items()}
        return path, {}
    
    def get_sorted_images(self, sort_by='alphabetical'):
        """获取排序后的图片列表"""
        r = self.get_redis_client()
        images = list(r.smembers("wallpapers"))
        
        if sort_by == 'alphabetical':
            return sorted(images)
        elif sort_by == 'reverse':
            return sorted(images, reverse=True)
        elif sort_by == 'random':
            import random
            random.shuffle(images)
            return images
        else:
            return images  # 默认不排序
    
    def url_redirect(self, url):
        """执行 URL 重定向"""
        self.send_response(308)  # 使用 308 永久重定向，便于缓存
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Location', url)
        self.send_header('Cache-Control', 'max-age=0, s-maxage=86400, stale-while-revalidate=3600')  # 缓存24小时
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write('Redirecting to {} (308)'.format(url).encode('utf-8'))
    
    def send_json_response(self, data, status_code=200):
        """发送JSON响应"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def do_GET(self):
        try:
            r = self.get_redis_client()
        except Exception as e:
            self.send_error(500, f"Redis连接失败: {e}")
            return
        
        try:
            path, params = self.parse_query_params(self.path)
            sort_by = params.get('sort', 'alphabetical')
            response_format = params.get('format', 'json')  # 默认json格式
            
            if path == '/api/images' or path == '/api/images/':
                # 获取所有图片
                images_list = self.get_sorted_images(sort_by)
                
                if response_format == 'image':
                    # 如果要求返回图片，从列表中随机选一张并重定向
                    if images_list:
                        import random
                        random_image = random.choice(images_list)
                        self.url_redirect(random_image)  # 直接使用存储的完整URL
                    else:
                        self.send_json_response(
                            {"status": "error", "message": "没有找到图片"}, 
                            404
                        )
                else:
                    # 默认返回JSON
                    self.send_json_response({
                        "status": "success",
                        "count": len(images_list),
                        "sort": sort_by,
                        "images": images_list
                    })
                
            elif path == '/api/images/latest':
                # 获取最新一张图片
                images_list = self.get_sorted_images(sort_by)
                
                if not images_list:
                    self.send_json_response(
                        {"status": "error", "message": "没有找到图片"}, 
                        404
                    )
                    return
                
                latest_image = images_list[-1]  # 排序后的最后一个就是最新的
                
                if response_format == 'image':
                    # 直接重定向到最新图片
                    self.url_redirect(latest_image)  # 直接使用存储的完整URL
                else:
                    # 返回JSON格式
                    self.send_json_response({
                        "status": "success",
                        "image": latest_image,
                        "total": len(images_list)
                    })
                
            elif path.startswith('/api/images/position/'):
                # 获取指定位置的图片
                try:
                    position_str = path.split('/')[-1]
                    position = int(position_str)
                    
                    images_list = self.get_sorted_images(sort_by)
                    
                    if not images_list:
                        self.send_json_response(
                            {"status": "error", "message": "没有找到图片"}, 
                            404
                        )
                        return
                    
                    # 支持负数索引，比如 -1 表示最后一个
                    if position < 0:
                        position = len(images_list) + position
                    
                    if position < 0 or position >= len(images_list):
                        self.send_json_response({
                            "status": "error", 
                            "message": f"位置超出范围，有效范围: 0-{len(images_list)-1} (或 -1 到 -{len(images_list)})",
                            "available_positions": len(images_list)
                        }, 400)
                        return
                    
                    selected_image = images_list[position]
                    
                    if response_format == 'image':
                        # 直接重定向到指定位置的图片
                        self.url_redirect(selected_image)  # 直接使用存储的完整URL
                    else:
                        # 返回JSON格式
                        self.send_json_response({
                            "status": "success",
                            "position": position,
                            "total": len(images_list),
                            "sort": sort_by,
                            "image": selected_image
                        })
                    
                except ValueError:
                    self.send_json_response(
                        {"status": "error", "message": "无效的位置参数"}, 
                        400
                    )
                    
            else:
                self.send_json_response(
                    {"status": "error", "message": "接口不存在"}, 
                    404
                )
                
        except Exception as e:
            self.send_json_response(
                {"status": "error", "message": f"服务器错误: {str(e)}"}, 
                500
            )