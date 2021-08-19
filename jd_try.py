#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/19 12:19 下午
# @File    : jd_try.py
# @Project : jd_scripts
# @Desc    : 京东试用
import asyncio
import aiohttp

from urllib.parse import urlencode
from config import USER_AGENT
from utils.jd_init import jd_init
from utils.console import println
from utils.process import process_start
from utils.logger import logger





@jd_init
class JdTry:
    headers = {
        'user-agent': USER_AGENT,
        'referer': 'https://try.m.jd.com',
    }

    cid_map = {
        "全部商品": "0",
        "家用电器": "737",
        "手机数码": "652,9987",
        "电脑办公": "670",
        "家居家装": "1620,6728,9847,9855,6196,15248,14065",
        "美妆护肤": "1316",
        "服饰鞋包": "1315,1672,1318,11729",
        "母婴玩具": "1319,6233",
        "生鲜美食": "12218",
        "图书音像": "1713,4051,4052,4053,7191,7192,5272",
        "钟表奢品": "5025,6144",
        "个人护理": "16750",
        "家庭清洁": "15901",
        "食品饮料": "1320,12259",
        "更多惊喜": "4938,13314,6994,9192,12473,6196,5272,12379,13678,15083,15126,15980",
    }

    type_map = {
        "全部试用": "0",
        "普通试用": "1",
        "闪电试用": "3",
        "30天试用": "5",
    }

    min_price = 100  # 商品最低价格

    async def request(self, session, path='', params=None, method='GET'):
        """
        请求数据
        :param method:
        :param params:
        :param path:
        :param session:
        :return:
        """
        try:
            url = 'https://try.m.jd.com/{}?'.format(path) + urlencode(params)

            if method == 'GET':
                response = await session.get(url)
            else:
                response = await session.post(url)

            data = await response.json()

            println(data)

        except Exception as e:
            println('{}, 请求付费器数据失败, {}'.format(self.account, e.args))

    async def get_goods_list(self, session, page=1):
        """
        获取商品列表
        :param session:
        :param page:
        :return:
        """
        path = '/activity/list'
        params = {
            'pb': 1,
            'cids': 0,
            'pageSize': 12,
            'page': page,
            'type': 1,
            'state': 0,
        }
        await self.request(session, path, params)

    async def run(self):
        """
        :return:
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            await self.get_goods_list(session, page=1)


if __name__ == '__main__':
    from config import JD_COOKIES

    app = JdTry(**JD_COOKIES[0])
    asyncio.run(app.run())
