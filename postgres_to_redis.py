# coding: utf-8
import os
import psycopg2
import redis
from datetime import datetime
import load_env

load_env.debug_env_variables()

class PostgreSQLToRedisMigrator:
    def __init__(self):
        self.config = self.load_config()
        
    def load_config(self):
        """从环境变量加载配置"""
        return {
            'redis': {
                'host': os.getenv('REDIS_HOST', 'localhost'),
                'port': int(os.getenv('REDIS_PORT', '6379')),
                'password': os.getenv('PASSWORD'),
                'ssl': True if os.getenv('REDIS_SSL', 'false').lower() == 'true' else False
            },
            'postgresql': {
                'host': os.getenv('PG_HOST', 'localhost'),
                'port': int(os.getenv('PG_PORT', '5432')),
                'database': os.getenv('PG_DATABASE', 'postgres'),
                'user': os.getenv('PG_USER', 'postgres'),
                'password': os.getenv('PG_PASSWORD'),
            },
            'migration': {
                'table': os.getenv('PG_TABLE', 'bing'),
                'column': os.getenv('PG_COLUMN', 'image'),
                'redis_set': os.getenv('REDIS_SET_NAME', 'bing_images'),
                'batch_size': int(os.getenv('BATCH_SIZE', '100'))
            }
        }
    
    def get_now_time(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def test_connections(self):
        """测试数据库连接"""
        # 测试Redis连接
        try:
            r = redis.Redis(**self.config['redis'], decode_responses=True)
            r.ping()
            print(f"[{self.get_now_time()}] Redis连接测试成功")
            r.close()
        except Exception as e:
            raise Exception(f"Redis连接失败: {e}")
        
        # 测试PostgreSQL连接
        try:
            conn = psycopg2.connect(**self.config['postgresql'])
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            print(f"[{self.get_now_time()}] PostgreSQL连接测试成功")
            cursor.close()
            conn.close()
        except Exception as e:
            raise Exception(f"PostgreSQL连接失败: {e}")
    
    def migrate_data(self):
        """执行数据迁移"""
        print(f"[{self.get_now_time()}] 开始数据迁移")
        
        # 连接数据库
        pg_conn = psycopg2.connect(**self.config['postgresql'])
        pg_cursor = pg_conn.cursor()
        
        r = redis.Redis(**self.config['redis'], decode_responses=True)
        
        try:
            # 获取数据
            sql = f"SELECT {self.config['migration']['column']} FROM {self.config['migration']['table']}"
            pg_cursor.execute(sql)
            results = pg_cursor.fetchall()
            
            total_count = len(results)
            print(f"[{self.get_now_time()}] 从PostgreSQL获取到 {total_count} 条记录")
            
            # 使用pipeline批量导入
            pipeline = r.pipeline()
            success_count = 0
            batch_size = self.config['migration']['batch_size']
            
            for i, record in enumerate(results, 1):
                try:
                    value = str(record[0])  # 确保转换为字符串
                    pipeline.sadd(self.config['migration']['redis_set'], value)
                    success_count += 1
                    
                    # 批量执行
                    if i % batch_size == 0:
                        pipeline.execute()
                        print(f"[{self.get_now_time()}] 已处理 {i}/{total_count} 条记录")
                        
                except Exception as e:
                    print(f"[{self.get_now_time()}] 跳过记录 {i}: {e}")
                    continue
            
            # 执行剩余的批次
            pipeline.execute()
            
            # 验证结果
            redis_count = r.scard(self.config['migration']['redis_set'])
            print(f"[{self.get_now_time()}] 迁移完成!")
            print(f"[{self.get_now_time()}] PostgreSQL记录数: {total_count}")
            print(f"[{self.get_now_time()}] Redis集合成员数: {redis_count}")
            print(f"[{self.get_now_time()}] 成功导入: {success_count}")
            
        finally:
            # 清理资源
            pg_cursor.close()
            pg_conn.close()
            r.close()

def main():
    migrator = PostgreSQLToRedisMigrator()
    
    try:
        # 测试连接
        migrator.test_connections()
        
        # 执行迁移
        migrator.migrate_data()
        
    except Exception as e:
        print(f"[{migrator.get_now_time()}] 错误: {e}")

if __name__ == "__main__":
    main()