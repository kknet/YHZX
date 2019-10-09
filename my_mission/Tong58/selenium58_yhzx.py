#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/9/27 15:08
# @Author  : Lodge
import os
import re
import sys
import time
import json
import base64
import random
import urllib3
import logging
import importlib
from functools import wraps
from threading import Thread
from logging import getLogger
from fontTools.ttLib import TTFont
import matplotlib.pyplot as plt
from helper.Baidu_ocr.client import main_ocr

import requests
from lxml import etree
from selenium import webdriver
from fake_useragent import UserAgent
# from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions   # 不用EC 因为EC会有小黄下划线 不好看

from helper import python_config   # 这里是导入配置文件
# 这个可以做成完全不用自动化的程序,但是设计之初是有可能需要沟通交流功能,所以做成半自动化的

ua = UserAgent()     # fake useragent
LOG = getLogger()    # LOG recoder
LOG.setLevel(logging.DEBUG)  # Change the level of logging::
# You can modify the following code to change the location::
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
this_month = time.strftime('%Y%m', time.localtime())
filename = BASE_DIR + f'/helper/{this_month}.log'
formatter = logging.Formatter(
        "%(asctime)s %(filename)s[line:%(lineno)d]%(levelname)s - %(message)s"
)  # Define the log output format
fh = logging.FileHandler(filename=filename, encoding="utf-8")
fh.setFormatter(formatter)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.formatter = formatter
LOG.addHandler(fh)
LOG.addHandler(console_handler)
LOG.setLevel(logging.INFO)
urllib3.disable_warnings()   # disabled requests' verify warning
# ========================================================================================== #


class TongCheng(object):
    def __init__(self):
        self.base_url = 'https://employer.58.com/'
        self.down_url = self.base_url + 'resumedownload?'
        self.down_url_api = self.base_url + 'resume/downloadlist?'
        self.auto_resume_url = self.base_url + 'resumereceive?'
        self.auto_resume_api = self.base_url + 'resume/deliverlist?'

        self.local_class = self.__class__.__name__

        self.session = requests.Session()
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("--no-sandbox")
        self.options.add_argument('--disable-gpu')
        # chrome.exe --remote-debugging-port=58580 --user-data-dir="C:\selenium_58_yh\AutomationProfile"  # start chrome
        self.options.add_experimental_option("debuggerAddress", f"127.0.0.1:{python_config.chrome_port}")  # connect
        self.driver = webdriver.Chrome(options=self.options)

    def post_data_down(self, info):
        print(info)

    @staticmethod
    def handle_num(key):
        key_code = re.findall(r'(&#x.*?);', key)
        if len(key_code) == 7 or 11:
            key_1 = key_code[0]   # 1
            key = key.replace(f'{key_1};', '1')
        else:
            key = key

        xml = etree.parse(BASE_DIR + r'\helper\fonts\b64.xml')
        root = xml.getroot()
        font_dict = {}
        all_data = root.xpath('//glyf/TTGlyph')
        for index, data in enumerate(all_data):
            font_key = data.attrib.get('name')[3:].lower()
            contour_list = list()
            if index == 0:
                continue
            for contour in data:
                for pt in contour:
                    contour_list.append(dict(pt.attrib))
            font_dict[font_key] = json.dumps(contour_list, sort_keys=True)

        for each_value in key_code:
            if each_value == key_code[0]:
                continue
            else:
                each_value = each_value.replace('&#x', '')
                for v in font_dict:
                    value = font_dict[v]
                    value = json.loads(value)
                    x = []
                    y = []
                    if v == each_value:
                        for al in value:
                            x_e = int(al['x'])
                            y_e = int(al['y'])
                            x.append(x_e)
                            y.append(y_e)
                        plt.figure(figsize=(1, 1))  # 设置保存图片的大小 (n x 100px)
                        plt.fill_between(x, y, facecolor='black')  # 填充图片,使用黑色
                        # plt.grid(True)
                        plt.plot(x, y)  # 这里可以额外添加很多属性比如线型,线色('-k')这个表示实线黑色  线宽(linewidth)
                        plt.axis('off')  # 关闭坐标
                        plt.savefig(BASE_DIR + r"\helper\fonts\plt.png")
                        plt.show()   # 这个和下面那个功能会重置坐标 如果两个都要显示的话 不要放上句前面

                        sub_key = main_ocr()   # 调用百度的识别，发现很慢

                        if sub_key:
                            key = key.replace(f'&#x{each_value};', sub_key)
                        else:
                            key = key.replace(f'&#x{each_value};', '*')
                    time.sleep(0.5)

        return key

    @staticmethod
    def handle_name(data):
        true_name = data['trueName']
        family_name = data['familyName'][0]
        name_re = re.findall(r'(&#x[0-9a-z]+;)', true_name)
        if not name_re:
            return true_name
        else:
            true_name = true_name.replace(name_re[0], family_name)
            return true_name

    def transfer_useful(self, handled_data, order_list):
        # 这里是最后要处理数据的地方，在这之前还有很多地方的数据需要处理（解码为主）
        data_s = handled_data
        for _ in range(order_list):
            data = data_s[_]
            # print('data:', data)
            gender_judge = data['sex']
            work_exp = data['experiences']
            if work_exp:
                work_experience = []
                for each_work in work_exp:
                    work_info = {
                        '起止时间': each_work['startDate'] + each_work['endDate'],
                        '公司信息': each_work['company'],
                        '工作内容': each_work['positionName'] + ":" + each_work['description']
                    }
                    work_experience.append(work_info)
            else:
                work_experience = []
            phone_num = self.handle_num(data['mobile'])
            name = self.handle_name(data)
            # work_year = self.handle_num(data['workYear'])
            work_year = data['workYear']
            # salary = self.handle_num(data['targetSalary']) if '面议' not in data['targetSalary'] else '面议'
            salary = data['targetSalary'] if '面议' not in data['targetSalary'] else '面议'

            json_info = {
                'name': name,
                'mobile_phone': phone_num,
                'company_dpt': 1,   # 不确定写啥
                'resume_key': data['expectCateName'],
                'gender': 2 if gender_judge == '0' else 1,
                'date_of_birth': f'-01-01',
                'current_residency': data['expectArea'],
                'years_of_working': work_year,
                'hukou': '',
                'current_salary': '',
                'politics_status': '',
                'marital_status': 2,
                'address': '',
                'zip_code': '',
                'email': '',
                'home_telephone': '',
                'personal_home_page': '',
                'excecutiveneed': '',
                'self_assessment': data['letter'],
                'i_can_start': '',
                'employment_type': 1,
                'industry_expected': '',
                'working_place_expected': data['expectArea'],
                'salary_expected': salary,
                'job_function_expected': 1,
                'current_situation': '',
                'word_experience': work_experience,
                'project_experience': [],
                'education': [],
                'honors_awards': [],
                'practical_experience': [],
                'training': '',
                'language': [],
                'it_skill': [],
                'certifications': [],
                'is_viewed': 1,
                'resume_date': '',
                'get_type': '',
                'external_resume_id': data['resumeid'][-49:],
                'labeltype': 1,
                'resume_logo': data['picUrl'],
                'resume_from': 3,           # 这里忘记该写啥了
                'account_from': python_config.account_from,
                'update_date': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            }

            yield json_info

    def click_get_code(self):
        time.sleep(0.5)
        all_code_pos = self.driver.find_elements_by_xpath(
            '/html/body/div[2]/div[2]/div[1]/div[4]/div[2]/ul/li/div[1]/div[3]/section[1]')
        num_all_code = len(all_code_pos)
        if num_all_code != 0:
            time.sleep(0.3)
            for i in range(1, num_all_code+1):
                each_pos = self.driver.find_element_by_xpath(
                    f'/html/body/div[2]/div[2]/div[1]/div[4]/div[2]/ul/li[{i}]/div[1]/div[3]/section[1]'
                )
                each_pos_text = each_pos.text
                if each_pos_text == '获取密号':
                    each_pos_c = self.driver.find_element_by_xpath(
                        f'/html/body/div[2]/div[2]/div[1]/div[4]/div[2]/ul/li[{i}]/div[1]/div[3]/section[1]/a'
                    )
                    each_pos_c.click()
                    time.sleep(1)

                if i == 5:
                    break

    @staticmethod
    def requests_headers(referer_url):
        # 5.请求头
        cookies = importlib.reload(python_config).cookies
        headers = {
            'User-Agent': ua.random,
            'x-requested-with': 'XMLHttpRequest',
            'referer': referer_url,
            'cookie': cookies,
            'accept': 'text/javascript, application/javascript, application/ecmascript, application/x-ecmascript, */*; q=0.01',
        }
        return headers

    def download_page_each_info(self):
        # 5. 分析每个数据
        pass

    def download_page_all_detail(self, referer_url, people_num):
        # 4.开始爬基础数据。
        headers = self.requests_headers(referer_url)
        pgs = people_num // 50 + 1
        for pg in range(1, pgs+1):
            LOG.info(f'当前下载页为:{pg}, 页面数据有{people_num}条')
            time.sleep(random.uniform(1, 3))
            now_pg_data = requests.get(self.down_url_api, params={'pageindex': pg}, headers=headers, verify=False)
            # print('now_pg_data:', now_pg_data.text)
            new_data = now_pg_data.text.lstrip('(').rstrip(')')
            new_data = json.loads(new_data)
            resume_data = new_data['data']['resumeList']
            yield resume_data

    def download_page_people_each(self, today_all_num):
        # 3.这里是点击每一个人 然后...
        # /html/body/div[2]/div[2]/div[1]/div[4]/div[2]/ul/li/div[1]/div[1]/div[3]/p[1]/span[1]
        now_page_referer = self.driver.current_url
        pages = today_all_num   # 总共的数量(后面两个调用函数意思不一样)
        time.sleep(random.uniform(1, 3))
        # 下面是好一点的办法,速度快,但是需要处理的地方有点多
        resume_data = self.download_page_all_detail(now_page_referer, pages)  # 这里的pages是该函数拿来确定页数的
        for each_data in resume_data:
            data_info_down = self.transfer_useful(each_data, pages)   # 这里的pages是用来保留几条数据的
            for post_data_down in data_info_down:
                self.post_data_down(post_data_down)

    def handle_font(self, page_source):
        bs64_str = re.findall(
            r'@font-face{font-family:"customfont"; src:url\(data:application/font-woff;charset=utf-8;base64,(.*?)\)  format',
            page_source)[0]
        temp_str = base64.b64decode(bs64_str)
        with open(BASE_DIR + '/helper/fonts/b64.woff', 'wb') as fl:
            fl.write(temp_str)
        time.sleep(0.5)
        font = TTFont(BASE_DIR + '/helper/fonts/b64.woff')
        font.saveXML(BASE_DIR + '/helper/fonts/b64.xml')

        get_cmap = font['cmap'].getBestCmap()
        new_map = dict()

        for key in get_cmap.keys():
            value = re.search(r'(\d+)', get_cmap[key])
            if not value:
                continue
            # print(get_cmap[key])
            value = int(re.search(r'(\d+)', get_cmap[key]).group(1)) - 1
            key = hex(key)
            new_map[key] = value

        pass

    def download_page_people(self):
        # 2.这里先判断今天有没有人
        today_tik = time.strftime('%Y-%m-%d', time.localtime())
        today_tik = '2018-11-26'
        LOG.info(f'今天日期为{today_tik},下载任务开始查询...')
        page_source = self.driver.page_source
        self.handle_font(page_source)
        # print('开始休息了...')           # # # #
        # time.sleep(10000)
        # self.click_get_code()    # 这里是处理页面的数据，让每一个都变成可以识别的密令
        try:
            today_all = self.driver.find_elements_by_xpath(
                f'/html/body/div[2]/div[2]/div[1]/div[4]/div[2]/ul/li/div[1]/div[text()="{today_tik}"]')
        except Exception as e:
            print(e)
            today_all_num = 0
        else:
            today_all_num = len(today_all)

        if today_all_num != 0:
            self.download_page_people_each(today_all_num)
        else:
            return

    def download_page(self):
        # 1.只是去下载页面而已
        self.driver.get(self.down_url)
        try:
            WebDriverWait(self.driver, 7200, poll_frequency=10).until(
                expected_conditions.presence_of_element_located((
                    By.XPATH, '/html/body/div[2]/div[2]/div[1]/div[4]/div[2]/ul/li[1]/div[1]/div[1]/div[3]/p[1]/span[1]'
                )))
        except Exception as e:
            print(e)
        else:
            self.download_page_people()

    # =============================================================== # 上面是关于下载简历的部分,里面的加密暂时还未处理

    def post_data_auto(self, resume_data):
        print(resume_data)
        pass

    def all_auto_get(self, nums):
        referer_url = self.driver.current_url
        headers = self.requests_headers(referer_url)
        pgs = nums // 50 + 1
        for pg in range(1, pgs+1):
            time.sleep(random.uniform(1, 3))
            now_pg_data = requests.get(self.auto_resume_api, params={'pageindex': pg}, headers=headers, verify=False)
            new_data = now_pg_data.text.lstrip('(').rstrip(')')
            new_data = json.loads(new_data)
            resume_data = new_data['data']['resumeList']
            yield resume_data

    def auto_resume(self):
        # 1. 到主动投递的页面去拿到 当天 的简历的数量
        self.driver.get(self.auto_resume_url)
        today_tic = time.strftime('%Y-%m-%d', time.localtime())
        xpath_today = f'投递时间：{today_tic}'
        xpath_today = '投递时间：2019-10-06'
        time.sleep(0.5)
        all_auto = self.driver.find_elements_by_xpath(f'//span[text()="{xpath_today}"]')
        all_nums_auto = len(all_auto)
        if all_nums_auto == 0:
            LOG.info(f'{today_tic}检测的时候没有简历投递进来...')
        else:
            LOG.info(f'{xpath_today}为这天的简历有:{all_nums_auto}条')
            auto_resume_data = self.all_auto_get(all_nums_auto)
            for each_data in auto_resume_data:
                need_post = self.transfer_useful_auto(each_data)
                for post_resume in need_post:
                    self.post_data_auto(post_resume)

    def transfer_useful_auto(self, handled_data):
        # 这里是最后要处理数据的地方，在这之前还有很多地方的数据需要处理（解码为主）
        data_s = handled_data
        for _ in range(len(data_s)):
            data = data_s[_]
            # print('data:', data)
            gender_judge = data['sex']
            work_exp = data['experiences']
            if work_exp:
                work_experience = []
                for each_work in work_exp:
                    work_info = {
                        '起止时间': each_work['startDate'] + each_work['endDate'],
                        '公司信息': each_work['company'],
                        '工作内容': each_work['positionName'] + ":" + each_work['description']
                    }
                    work_experience.append(work_info)
            else:
                work_experience = []
            phone_num = self.handle_num(data['mobile'])
            name = self.handle_name(data)
            work_year = self.handle_num(data['workYear'])
            salary = self.handle_num(data['targetSalary']) if '面议' not in data['targetSalary'] else '面议'
            age = int(data['age'])
            now_year = int(time.strftime('%Y', time.localtime()))

            json_info = {
                'name': name,
                'mobile_phone': phone_num,
                'company_dpt': 1,  # 不确定写啥
                'resume_key': data['expectCateName'],
                'gender': 2 if gender_judge == '0' else 1,
                'date_of_birth': f'{now_year - age}-01-01',
                'current_residency': data['expectArea'],
                'years_of_working': work_year,
                'hukou': '',
                'current_salary': '',
                'politics_status': '',
                'marital_status': 2,
                'address': '',
                'zip_code': '',
                'email': '',
                'home_telephone': '',
                'personal_home_page': '',
                'excecutiveneed': '',
                'self_assessment': data['letter'],
                'i_can_start': '',
                'employment_type': 1,
                'industry_expected': '',
                'working_place_expected': data['expectArea'],
                'salary_expected': salary,
                'job_function_expected': 1,
                'current_situation': '',
                'word_experience': work_experience,
                'project_experience': [],
                'education': [],
                'honors_awards': [],
                'practical_experience': [],
                'training': '',
                'language': [],
                'it_skill': [],
                'certifications': [],
                'is_viewed': 1,
                'resume_date': '',
                'get_type': '',
                'external_resume_id': data['resumeid'][-49:],
                'labeltype': 1,
                'resume_logo': data['picUrl'],
                'resume_from': 3,  # 这里忘记该写啥了
                'account_from': python_config.account_from,
                'update_date': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            }

            yield json_info

    def run(self):
        self.download_page()    # 获取下载的简历信息 (涉及到加密,正在处理中)

        # self.auto_resume()   # 获取主动投递的简历信息


def send_rtx_msg(msg):
    """
    公司的内部的rtx信息发送接口, 接收人已经写成了配置文件了
    :param msg: 要发送的信息
    :return: 不返回
    """
    post_data = {
        "sender": "系统机器人",
        "receivers": python_config.receivers,
        "msg": msg,
    }
    # requests.Session().post("http://rtx.fbeads.cn:8012/sendInfo.php", data=post_data)


def clear_timer(set_time):
    """
    一个简单地定时器装置, 放入的 set_time 必须为集合, 列表, 元组。 里面的元素必须为字符串::方便设置指定的时间比如('18:21')
    :param set_time: 设定的触发时间: 全称: 小时。
    :return:
    """

    def work_time(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now_time = time.strftime("%H:%M", time.localtime())
            if now_time in set_time:
                print()
                func(*args, **kwargs)
                print('\r这个程序停了,正在休眠中...', end='')
                # print('清除程序开始了,正在休眠中...')
                time.sleep(60)
            else:
                print('\r这个程序停了,继续休眠中...', end='')
                # print('不是清除程序运行的时间,继续休眠中...')
                time.sleep(60)

        return wrapper
    return work_time


def main():
    app = TongCheng()
    app.run()


if __name__ == '__main__':
    main()
