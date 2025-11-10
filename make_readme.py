# coding:utf-8
import json
import time


def get_now_time():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


#   "zh-CN", "en-US"
# 读取 data/zh-CN_all.json 文件，生成 README.md 文件
with open('data/zh-CN_all.json', 'r', encoding='utf-8') as f:
    zh_data = json.load(f)

with open('data/en-US_all.json', 'r', encoding='utf-8') as f:
    en_data = json.load(f)

all_day = min(
    len(zh_data['data']),
    len(en_data['data'])
)
print("[{}] all day: {}".format(get_now_time(), all_day))

head_img = "https://www.bing.com" + zh_data['data'][0]['urlbase'] + "_UHD.jpg"
head_des = zh_data['data'][0]['copyright']
head_title = zh_data['data'][0]['title']

f = open('README.md', 'w', encoding='utf-8')
f.write("# Bing Wallpaper\n")
f.write(f"<!--{get_now_time()}-->\n")
f.write("![{0}]({2}) Today: [{0}]({1})\n".format(head_title, head_img, head_img + "&w=1920"))
f.write("""
|  Chinese – China   |   English – United States   |
| :----: | :----: |
""")
for i in range(all_day):
    print("[{}] day: {}".format(get_now_time(), i + 1))
    zh_day = zh_data['data'][i]
    en_day = en_data['data'][i]
    zh_date = zh_day['enddate']
    zh_date_format = "{}-{}-{}".format(zh_date[0:4], zh_date[4:6], zh_date[6:8])
    en_date = en_day['enddate']
    en_date_format = "{}-{}-{}".format(en_date[0:4], en_date[4:6], en_date[6:8])
    zh_url_full = "https://www.bing.com" + zh_day['urlbase'] + "_UHD.jpg"
    zh_readme_url = zh_url_full + "&pid=hp&w=384&h=216&rs=1&c=4"
    en_url_full = "https://www.bing.com" + en_day['urlbase'] + "_UHD.jpg"
    en_readme_url = en_url_full + "&pid=hp&w=384&h=216&rs=1&c=4"
    f.write("| ![{0}]({1}) {0} [download 4k]({3})| ![{2}]({4}) {2} [download 4k]({5})|\n".format(zh_date_format, zh_readme_url, en_date_format, zh_url_full, en_readme_url, en_url_full))

f.write("-------------------\n")