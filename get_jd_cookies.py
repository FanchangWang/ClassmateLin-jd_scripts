#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/6/14 9:57
# @File    : get_jd_cookies.py
# @Project : jd_scripts
# @Desc    : 京东扫描登录获取cookies
import time
import qrcode
import requests
from utils.logger import get_logger
from utils.console import println
from config import USER_AGENT

logger = get_logger('get_jd_cookies')


def get_timestamp():
    """
    获取当前毫秒时间戳
    :return:
    """
    return int(time.time() * 1000)


def get_headers():
    """
    获取请求头
    :return:
    """
    headers = {
        'Connection': 'Keep-Alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-cn',
        'Referer': 'https://plogin.m.jd.com/login/login?appid=300&returnurl=https://wq.jd.com/passport'
                   '/LoginRedirect?state={}&returnurl=https://home.m.jd.com/myJd/newhome.action?sceneval=2&ufc'
                   '=&/myJd/home.action&source=wq_passport'.format(get_timestamp()),
        'User-Agent': USER_AGENT,
        'Host': 'plogin.m.jd.com'
    }
    return headers


class JDCookies:
    """
    通过扫码登录获取JD Cookies
    """
    def __init__(self):
        self._http = requests.Session()
        self._http.headers = get_headers()

    def __login_entrance(self):
        """
        扫描登录入口，先获取s_token
        :return:
        """
        url = 'https://plogin.m.jd.com/cgi-bin/mm/new_login_entrance?lang=chs&appid=300&returnurl=https://wq.jd.com' \
              '/passport/LoginRedirect?state={}&returnurl=https://home.m.jd.com ' \
              '/myJd/newhome.action?sceneval=2&ufc=&/myJd/home.action&source=wq_passport'.format(get_timestamp())
        try:
            response = self._http.get(url)
            logger.info("获取s_token， 数据:{}".format(response.json()))
            return response.json()['s_token']
        except requests.RequestException as e:
            logger.info("获取s_token失败, 原因: {}".format(e.args))

    def __generate_qr_code(self, s_token=''):
        """
        用s_token生成二维码
        :param s_token:
        :return:
        """
        url = 'https://plogin.m.jd.com/cgi-bin/m/tmauthreflogurl?s_token={}&v={}&remember=true'.format(s_token,
                                                                                                       get_timestamp())
        body = 'lang=chs&appid=300&source=wq_passport&returnurl=https://wqlogin2.jd.com/passport/LoginRedirect?state' \
               '={}&returnurl=//home.m.jd.com/myJd/newhome.action?sceneval=2&' \
               'ufc=&/myJd/home.action'.format(get_timestamp())

        try:
            response = self._http.post(url, body)
            data = response.json()
            logger.info("获取二维码, 数据:{}".format(data))
            token = data['token']
            qr_code_url = 'https://plogin.m.jd.com/cgi-bin/m/tmauth?appid=300&client_type=m&token=' + token
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=4,
                border=1,
            )
            qr.add_data(qr_code_url)
            qr.make(fit=True)

            println('请扫描二维码登录, 有效期三分钟...', style="bold white")

            img = qr.make_image(fill_color="black", back_color="white")
            img.save('./qrcode.png')
            img.show()
            return token

        except requests.RequestException as e:
            logger.info("获取二维码失败, 网络异常: {}".format(e.args))

    def __check_login(self, token=''):
        """
        检查登录状态
        :param token:
        :return:
        """
        okl_token = self._http.cookies.get('okl_token')

        url = 'https://plogin.m.jd.com/cgi-bin/m/tmauthchecktoken?&token={}&ou_state=0&okl_token={}'.format(token,
                                                                                                            okl_token)
        body = 'lang=chs&appid=300&source=wq_passport&returnurl=https://wqlogin2.jd.com/passport/LoginRedirect?state' \
               '={}&returnurl=//home.m.jd.com/myJd/' \
               'newhome.action?sceneval=2&ufc=&/myJd/home.action'.format(get_timestamp())
        start_time = int(time.time())

        println("等待扫码中...", style='bold yellow')
        while True:
            time.sleep(1)
            try:
                response = self._http.post(url, body)
                data = response.json()
                logger.info("获取扫描状态, 数据:{}".format(data))
                if data['errcode'] == 0:
                    pt_pin = self._http.cookies.get('pt_pin')
                    pt_key = self._http.cookies.get('pt_key')
                    logger.info("成功获取cookie: pt_pin={};pt_key={};".format(pt_pin, pt_key))
                    println("成功获取cookie, 如下:", style='bold green')
                    println("pt_pin={};pt_key={};".format(pt_pin, pt_key), style='bold green')
                    break
                elif data['errcode'] == 176:
                    println('获取cookie失败, 请扫码登录...', style='bold red')
                else:
                    println("获取cookie失败, 原因:{}".format(data['message']), style='bold red')
                    break
            except requests.RequestException as e:
                println("获取登录状态失败, 网络异常...", style='bold red')
                logger.info("获取登录状态失败, 原因:{}".format(e.args))
                break
            if int(time.time()) - start_time > 60 * 3:
                logger.info("超过三分钟仍未扫码...")
                println("超过三分钟未扫码...", style='bold red')
                break

    def start(self):
        """
        :return:
        """
        println("获取cookie脚本开始执行...", style='bold blue')
        s_token = self.__login_entrance()
        token = self.__generate_qr_code(s_token)
        self.__check_login(token)
        println("获取cookie脚本执行完毕...", style='bold green')


if __name__ == '__main__':
    jd = JDCookies()
    jd.start()
