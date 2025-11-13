# coding:utf-8

import redis
import json
import time
import os

env_dist = os.environ
PASSWORD = env_dist.get('PASSWORD')
REDIS_HOST = env_dist.get('REDIS_HOST')
REDIS_PORT = env_dist.get('REDIS_PORT')

def get_redis_connection():
    """获取Redis连接，包含错误处理"""
    try:
        print(f"[{get_now_time()}] 尝试连接Redis: {REDIS_HOST}:{REDIS_PORT}")
        
        r = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=PASSWORD, 
            ssl=True,
            decode_responses=True,
            socket_connect_timeout=10,  # 添加连接超时
            socket_timeout=10,          # 添加socket超时
            retry_on_timeout=True       # 超时重试
        )
        
        # 测试连接
        if r.ping():
            print(f"[{get_now_time()}] ✅ Redis连接成功")
            return r
        else:
            raise Exception("Redis ping失败")
            
    except redis.AuthenticationError as e:
        print(f"[{get_now_time()}] ❌ Redis认证失败: {e}")
        print("请检查 PASSWORD 环境变量是否正确")
        raise
    except redis.ConnectionError as e:
        print(f"[{get_now_time()}] ❌ Redis连接错误: {e}")
        print("请检查 REDIS_HOST 和 REDIS_PORT 环境变量")
        raise
    except Exception as e:
        print(f"[{get_now_time()}] ❌ Redis连接异常: {e}")
        raise

def get_now_time():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def main(run_type):
    # 读取 data/temo.json
    with open(f'data/{run_type}_temp.json', 'r', encoding="utf-8") as f:
        data = json.load(f)
    print("[{}] 开始更新 redis".format(get_now_time()))

    try:
        # 获取Redis连接
        r = get_redis_connection()
        
        success_count = 0
        error_count = 0
        
        for i in data:
            try:
                print("[{}] 更新图片：{}".format(get_now_time(), i["title"]))
                result = r.sadd("bing_images", i["url"])
                
                if result == 1:
                    print(f"[{get_now_time()}] ✅ 成功添加: {i['title']}")
                    success_count += 1
                else:
                    print(f"[{get_now_time()}] ℹ️ 图片已存在: {i['title']}")
                    
            except Exception as e:
                print(f"[{get_now_time()}] ❌ 添加失败 {i['title']}: {e}")
                error_count += 1
                continue  # 继续处理下一张图片

        print("[{}] 更新完成: 成功 {} 张, 失败 {} 张".format(get_now_time(), success_count, error_count))
        
        # 关闭连接
        r.close()
        
    except Exception as e:
        print(f"[{get_now_time()}] ❌ Redis操作失败: {e}")
        raise