import os

from dotenv import load_dotenv

# 加载 .env 文件
env_path = '.env'
load_dotenv(env_path)

print(f".env文件路径: {os.path.abspath(env_path)}")
print(f".env文件存在: {os.path.exists(env_path)}")

def debug_env_variables():
    """调试函数：显示所有环境变量"""
    print("=== 环境变量调试信息 ===")
    env_vars = [
        'PASSWORD', 'REDIS_HOST', 'REDIS_PORT',
        'PG_HOST', 'PG_PORT', 'PG_DATABASE', 'PG_USER', 'PG_PASSWORD',
        'PG_TABLE', 'PG_COLUMN', 'REDIS_SET_NAME', 'BATCH_SIZE'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # 对密码字段进行部分隐藏
            if 'PASSWORD' in var:
                masked_value = value[:2] + '***' + value[-2:] if len(value) > 4 else '***'
                print(f"  {var}: {masked_value}")
            else:
                print(f"  {var}: {value}")
        else:
            print(f"  {var}: [未设置]")
