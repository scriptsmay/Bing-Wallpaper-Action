# coding:utf-8
import json
import os
import sys
import shutil
from datetime import datetime
import logging
import re

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_backup(filepath, backup_dir='bak'):
    """
    创建备份文件到指定目录，保持目录结构
    
    :param filepath: 原文件路径
    :param backup_dir: 备份目录
    :return: 备份文件路径，如果失败返回None
    """
    try:
        # 获取相对路径
        if filepath.startswith('data/'):
            relative_path = filepath[5:]  # 去掉 'data/' 前缀
        else:
            relative_path = os.path.basename(filepath)
        
        backup_path = os.path.join(backup_dir, relative_path + '.bak')
        
        # 确保备份目录的父目录存在
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        # 创建备份
        shutil.copy2(filepath, backup_path)
        logger.info(f"创建备份: {backup_path}")
        return backup_path
        
    except Exception as e:
        logger.error(f"创建备份失败 {filepath}: {e}")
        return None


def extract_date_from_filename(filename):
    """
    从文件名中提取日期
    支持格式：de-DE_2022-05-05_14-19-25.json
    """
    # 匹配语言代码_YYYY-MM-DD_HH-MM-SS.json 格式
    patterns = [
        # 格式: de-DE_2022-05-05_14-19-25.json
        r'^[a-z]{2}-[A-Z]{2}_(\d{4})-(\d{2})-(\d{2})_\d{2}-\d{2}-\d{2}\.json$',
        # 格式: en-US_2023-12-31_23-59-59.json
        r'^[a-z]{2}-[A-Z]{2}_(\d{4})-(\d{2})-(\d{2})_\d{2}-\d{2}-\d{2}\.json$',
        # 其他可能的日期格式（保留原有逻辑）
        r'(\d{4})(\d{2})(\d{2})',  # YYYYMMDD
        r'(\d{4})-(\d{2})-(\d{2})',  # YYYY-MM-DD
        r'(\d{4})_(\d{2})_(\d{2})',  # YYYY_MM_DD
        r'(\d{4})\.(\d{2})\.(\d{2})',  # YYYY.MM.DD
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            try:
                if len(match.groups()) == 3:
                    year, month, day = match.groups()
                    date_obj = datetime.strptime(f"{year}-{month}-{day}", '%Y-%m-%d').date()
                    return date_obj
            except ValueError:
                continue
    
    return None


def should_keep_item(item, date_field, target_date):
    """
    判断是否应该保留该条目（针对 _all.json 和 _update.json 文件）
    """
    date_str = item.get(date_field, '')
    
    # 检查日期字符串格式
    if len(date_str) >= 8:
        try:
            year = date_str[0:4]
            month = date_str[4:6]
            day = date_str[6:8]
            
            # 验证日期有效性
            if year.isdigit() and month.isdigit() and day.isdigit():
                item_date = datetime.strptime(f"{year}-{month}-{day}", '%Y-%m-%d').date()
                return item_date >= target_date
        except ValueError as e:
            logger.warning(f"日期解析错误: {date_str}, 错误: {e}")
    
    # 如果日期格式不正确，默认保留该条目
    return True


def process_json_file(filepath, target_date, backup=True):
    """
    处理单个JSON文件
    
    :return: (是否成功, 原始记录数, 过滤后记录数, 文件类型)
    """
    try:
        # 获取文件名
        filename = os.path.basename(filepath)
        
        # 首先检查是否是特殊格式文件（_all.json 或 _update.json）
        is_special_file = filename.endswith('_all.json') or filename.endswith('_update.json')
        
        # 创建备份
        backup_created = False
        if backup:
            backup_path = create_backup(filepath, 'bak')
            backup_created = backup_path is not None
        
        # 如果是特殊文件，处理内容；否则根据文件名日期判断
        if is_special_file:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            original_count = 0
            filtered_count = 0
            file_type = "unknown"
            
            # 根据文件类型处理数据
            if 'data' in data:  # _all.json 类型文件
                file_type = "all"
                original_count = len(data.get('data', []))
                filtered_data = []
                
                for item in data['data']:
                    if should_keep_item(item, 'enddate', target_date):
                        filtered_data.append(item)
                
                data['data'] = filtered_data
                if 'Total' in data:
                    data['Total'] = len(filtered_data)
                filtered_count = len(filtered_data)
                
            elif 'images' in data:  # _update.json 类型文件
                file_type = "update"
                original_count = len(data.get('images', []))
                filtered_images = []
                
                for item in data['images']:
                    if should_keep_item(item, 'startdate', target_date):
                        filtered_images.append(item)
                
                data['images'] = filtered_images
                filtered_count = len(filtered_images)
            
            # 保存修改后的数据
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            removed_count = original_count - filtered_count
            backup_status = "已备份" if backup_created else "未备份"
            logger.info(f"处理 {filename} ({file_type}): {original_count} -> {filtered_count} 条记录, 移除 {removed_count} 条 [{backup_status}]")
            
            return True, original_count, filtered_count, file_type
            
        else:
            # 普通JSON文件，根据文件名日期判断是否删除整个文件
            file_date = extract_date_from_filename(filename)
            if file_date:
                if file_date < target_date:
                    # 删除整个文件
                    os.remove(filepath)
                    logger.info(f"删除文件 {filename} (文件日期: {file_date})")
                    return True, 1, 0, "deleted"
                else:
                    # 保留文件
                    logger.info(f"保留文件 {filename} (文件日期: {file_date})")
                    return True, 1, 1, "retained"
            else:
                # 文件名中没有找到日期，保留文件
                logger.info(f"保留文件 {filename} (未找到日期信息)")
                return True, 1, 1, "no_date"
        
    except Exception as e:
        logger.error(f"处理文件 {filepath} 时出错: {e}")
        return False, 0, 0, "error"


def clear_data_before_date(target_date_str, data_dir='data', backup=True):
    """
    清除 data 目录下 JSON 文件中标题日期在指定日期之前的条目
    支持子目录和普通JSON文件
    
    :param target_date_str: 指定日期字符串，格式为 'YYYY-MM-DD'
    :param data_dir: 数据目录路径
    :param backup: 是否创建备份文件
    """
    # 验证目录存在
    if not os.path.exists(data_dir):
        logger.error(f"数据目录不存在: {data_dir}")
        return False
    
    try:
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
    except ValueError as e:
        logger.error(f"日期格式错误: {e}")
        return False
    
    processed_files = 0
    total_removed_records = 0
    deleted_files = 0
    retained_files = 0
    
    # 递归遍历 data 目录下的所有 JSON 文件
    for root, dirs, files in os.walk(data_dir):
        for filename in files:
            if filename.endswith('.json'):
                filepath = os.path.join(root, filename)
                
                success, original_count, filtered_count, file_type = process_json_file(
                    filepath, target_date, backup
                )
                
                if success:
                    processed_files += 1
                    if file_type == "deleted":
                        deleted_files += 1
                    elif file_type in ["retained", "no_date"]:
                        retained_files += 1
                    else:
                        total_removed_records += (original_count - filtered_count)
    
    # 输出汇总信息
    logger.info(f"处理完成: 共处理 {processed_files} 个文件")
    logger.info(f"- 删除 {deleted_files} 个文件")
    logger.info(f"- 保留 {retained_files} 个文件")
    logger.info(f"- 移除 {total_removed_records} 条记录")
    
    if backup:
        backup_files_count = count_backup_files('bak')
        logger.info(f"- 备份 {backup_files_count} 个文件到 bak 目录")
    
    return True


def count_backup_files(backup_dir):
    """
    统计备份文件数量
    """
    if not os.path.exists(backup_dir):
        return 0
    
    count = 0
    for root, dirs, files in os.walk(backup_dir):
        for file in files:
            if file.endswith('.bak'):
                count += 1
    return count


def validate_date(date_str):
    """
    验证日期格式
    """
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def show_backup_info():
    """
    显示备份目录信息
    """
    backup_dir = 'bak'
    if os.path.exists(backup_dir):
        backup_files = []
        for root, dirs, files in os.walk(backup_dir):
            for file in files:
                if file.endswith('.bak'):
                    rel_path = os.path.relpath(os.path.join(root, file), backup_dir)
                    backup_files.append(rel_path)
        
        if backup_files:
            print(f"\n备份目录 '{backup_dir}' 中有 {len(backup_files)} 个备份文件:")
            for file in sorted(backup_files):
                file_path = os.path.join(backup_dir, file)
                file_size = os.path.getsize(file_path)
                print(f"  - {file} ({file_size} bytes)")
        else:
            print(f"\n备份目录 '{backup_dir}' 为空")
    else:
        print(f"\n备份目录 '{backup_dir}' 不存在")


def show_sample_files(data_dir='data'):
    """
    显示一些示例文件，帮助用户确认文件格式
    """
    print(f"\n扫描 {data_dir} 目录中的文件格式...")
    sample_files = []
    
    for root, dirs, files in os.walk(data_dir):
        for filename in files:
            if filename.endswith('.json'):
                filepath = os.path.join(root, filename)
                file_date = extract_date_from_filename(filename)
                date_info = f"日期: {file_date}" if file_date else "未识别到日期"
                
                if len(sample_files) < 5:  # 只显示前5个示例
                    sample_files.append(f"  - {filename} ({date_info})")
                
                if len(sample_files) >= 5:
                    break
        if len(sample_files) >= 5:
            break
    
    if sample_files:
        print("发现的文件格式示例:")
        for sample in sample_files:
            print(sample)
    else:
        print("未找到 JSON 文件")


def main():
    """
    主函数
    """
    if len(sys.argv) < 2:
        print("用法: python clear_data.py <YYYY-MM-DD> [数据目录]")
        print("示例: python clear_data.py 2025-01-01")
        print("示例: python clear_data.py 2025-01-01 /path/to/data")
        print("\n选项:")
        print("  --no-backup    不创建备份文件")
        print("\n功能说明:")
        print("  - 处理 _all.json 和 _update.json 文件：根据内容中的日期过滤条目")
        print("  - 处理其他 .json 文件：根据文件名中的日期决定是否删除整个文件")
        print("  - 支持 de-DE_2022-05-05_14-19-25.json 格式的文件名")
        print("  - 支持子目录递归处理")
        print("  - 备份文件保存在 bak 目录，保持原目录结构")
        sys.exit(1)
    
    target_date = sys.argv[1]
    data_dir = sys.argv[2] if len(sys.argv) > 2 else 'data'
    backup = True
    
    # 检查是否包含 --no-backup 参数
    if '--no-backup' in sys.argv:
        backup = False
        # 从参数列表中移除，避免影响其他参数解析
        sys.argv.remove('--no-backup')
        # 重新调整数据目录参数
        if len(sys.argv) > 2:
            data_dir = sys.argv[2]
    
    if not validate_date(target_date):
        print("错误: 日期格式不正确，请使用 YYYY-MM-DD 格式")
        sys.exit(1)
    
    # 显示示例文件
    show_sample_files(data_dir)
    
    # 显示操作信息
    print(f"\n操作摘要:")
    print(f"  - 目标日期: {target_date}")
    print(f"  - 数据目录: {data_dir}")
    print(f"  - 备份模式: {'开启 (备份到 bak 目录)' if backup else '关闭'}")
    print(f"  - 处理范围: 所有子目录中的 .json 文件")
    
    # 确认操作
    confirm = input(f"\n确定要继续吗？(y/N): ")
    if confirm.lower() != 'y':
        print("操作已取消")
        sys.exit(0)
    
    success = clear_data_before_date(target_date, data_dir, backup)
    
    if success:
        print(f"\n✓ 已清除 {target_date} 之前的日期数据")
        if backup:
            show_backup_info()
    else:
        print("✗ 处理过程中出现错误，请检查日志")
        sys.exit(1)


if __name__ == "__main__":
    main()