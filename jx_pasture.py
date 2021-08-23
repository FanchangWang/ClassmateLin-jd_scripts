#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/23 下午6:54
# @Project : jd_scripts
# @File    : jx_pasture.py
# @Cron    :
# @Desc    :
import json
import time
from datetime import datetime
from urllib.parse import urlencode

import aiohttp
import asyncio

from config import USER_AGENT

from utils.jx_init import jx_init
from utils.logger import logger
from utils.console import println
from db.model import Code, CODE_JD_PASTURE


@jx_init
class JdPasture:

    headers = {
        'user-agent': USER_AGENT.replace('jdapp;', 'jdpingou;'),
        'referer': 'https://st.jingxi.com/'
    }

    coins = 0  # 金币数量
    food_num = 0  # 白菜数量
    active_id = ''  # 活动ID
    pet_info_list = None  # 小鸡相关信息列表
    cow_info = None  # 牛相关信息
    share_code = None

    async def request(self, session, path, body=None, method='GET'):
        """
        请求数据
        :param session:
        :param body:
        :param path:
        :param params:
        :param method:
        :return:
        """
        try:
            time_ = datetime.now()
            params = {
                'channel': '7',
                'sceneid': '1001',
                'activeid': self.active_id,
                'activekey': 'null',
                '_ste': '1',
                '_': int(time_.timestamp() * 1000) + 2,
                'sceneval': '2',
                'g_login_type': '1',
                'callback': '',
                'g_ty': 'ls',
            }
            if not body:
                body = dict()
            params.update(body)
            url = 'https://m.jingxi.com/jxmc/{}?'.format(path) + urlencode(params)
            h5st = await self.encrypt(time_, url)
            url += '&h5st=' + h5st
            if method == 'GET':
                response = await session.get(url=url)
            else:
                response = await session.post(url=url)

            text = await response.text()
            data = json.loads(text)
            return data
        except Exception as e:
            println(e.args)

    async def get_home_data(self, session):
        """
        获取首页数据
        :param session:
        :return:
        """
        body = {
            'isgift': 1,
            'isquerypicksite': 1,
            '_stk': 'activeid,activekey,channel,isgift,isquerypicksite,sceneid'
        }
        res = await self.request(session, 'queryservice/GetHomePageInfo', body)
        if res.get('ret') != 0:
            return None
        else:
            return res.get('data')

    async def get_gold_from_bull(self, session):
        """
        收牛的金币
        :param session:
        :return:
        """

    async def init(self, session):
        """
        初始化
        :param session:
        :return:
        """
        home_data = await self.get_home_data(session)
        if not home_data:
            return False

        self.coins = home_data.get('coins', 0)

        try:
            self.food_num = home_data.get('materialinfo', list())[0]['value']
        except Exception as e:
            println('{}, 活动未开启/黑号, {}'.format(self.account, e.args))
            return False
        self.active_id = home_data.get('activeid', '')
        self.pet_info_list = home_data.get('petinfo', [])
        self.share_code = home_data.get('sharekey')
        self.cow_info = home_data.get('cow')

        return True

    async def run(self):
        """
        :return:
        """
        await self.get_encrypt()
        async with aiohttp.ClientSession(cookies=self.cookies, headers=self.headers) as session:
            if not await self.init(session):
                println('{}, 无法初始化, 退出程序!'.format(self.account))
                return

            if self.share_code:
                println('{}, 助力码:{}'.format(self.account, self.share_code))
                Code.insert_code(code_key=CODE_JD_PASTURE, code_val=self.share_code, sort=self.sort,
                                 account=self.account)




if __name__ == '__main__':
    from config import JD_COOKIES
    app = JdPasture(**JD_COOKIES[0])
    asyncio.run(app.run())