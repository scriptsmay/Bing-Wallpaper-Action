# api/debug.py
from http.server import BaseHTTPRequestHandler
import redis
import os
import json

def get_redis_client():
    return redis.Redis(
        host=os.environ.get('REDIS_HOST'),
        port=os.environ.get('REDIS_PORT'),
        password=os.environ.get('REDIS_PASSWORD'),
        ssl=True,
        decode_responses=True
    )

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            r = get_redis_client()
            
            # 测试连接
            ping_result = r.ping()
            
            # 检查 bing_images 集合
            exists = r.exists("bing_images")
            count = r.scard("bing_images") if exists else 0
            sample_images = r.srandmember("bing_images", 5) if count > 0 else []
            
            # 获取所有键
            all_keys = r.keys('*')
            
            info = {
                "redis_connection": "success" if ping_result else "failed",
                "bing_images_exists": exists,
                "bing_images_count": count,
                "sample_images": sample_images,
                "all_keys": all_keys,
                "environment_vars": {
                    "REDIS_HOST_set": bool(os.environ.get('REDIS_HOST')),
                    "REDIS_PORT_set": bool(os.environ.get('REDIS_PORT')),
                    "REDIS_PASSWORD_set": bool(os.environ.get('REDIS_PASSWORD'))
                }
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(info, indent=2).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_info = {
                "error": str(e),
                "environment_vars": {
                    "REDIS_HOST": os.environ.get('REDIS_HOST'),
                    "REDIS_PORT": os.environ.get('REDIS_PORT'),
                    "REDIS_PASSWORD_set": bool(os.environ.get('REDIS_PASSWORD'))
                }
            }
            self.wfile.write(json.dumps(error_info, indent=2).encode('utf-8'))