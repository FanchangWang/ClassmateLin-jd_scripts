#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/6/14 14:38
# @File    : jd_sign_collection.py
# @Project : jd_scripts
# @Desc    : 京东签到合集
import os
import json
import asyncio
import re
import time
from urllib.parse import urlencode

import aiohttp
from rich.console import Console

from log import get_logger

logger = get_logger('jd_sign_collection')
console = Console()


class JdSignCollection:
    status_success = 1  # 成功
    status_fail = 2  # 失败
    status_signed = 3  # 已签到

    status_msg = {
        status_success: '成功',
        status_fail: '失败',
        status_signed: '今日已操作过',
    }

    def __init__(self, pt_pin='', pt_key=''):
        self._pt_pin = pt_pin
        self._pt_key = pt_key
        self._result = []

    @logger.catch
    async def is_login(self, session):
        """
        判断cookies是否有效
        :param session:
        :return:
        """
        url = 'https://plogin.m.jd.com/cgi-bin/ml/islogin?time={}'.format(int(time.time()*1000))
        try:
            response = await session.get(url=url)
            text = await response.text()
            data = json.loads(text)
            if data['islogin'] == '1':
                return True
        except Exception as e:
            logger.info('检查登录状态失败, 网络异常:{}'.format(e.args))

        return False

    @logger.catch
    async def jd_bean(self, session):
        """
        京东-签到领豆
        :param session:
        :return:
        """
        name = '京东-签到领豆'
        url = 'https://api.m.jd.com/client.action?functionId=signBeanAct&sv=110&sign=b36e85acac978be15adb87da7412929d' \
              '&uuid=a27b83d3d1dba1cc&client=android&clientVersion=10.0.4&st=1623724179703'
        body = 'body=%7B%22eid%22%3A%22eidA1a01812289s8Duwy8MyjQ9m%2FiWxzcoZ6Ig7sNGqHp2V8%2FmtnOs' \
               '%2BKCpWdqNScNZAsDVpNKfHAj3tMYcbWaPRebvCS4mPPRels2DfOi9PV0J%2B%2FZRhX%22%2C%22fp%22%3A%22-1%22%2C' \
               '%22jda%22%3A%22-1%22%2C%22referUrl%22%3A%22-1%22%2C%22rnVersion%22%3A%224.7%22%2C%22shshshfp%22%3A%22' \
               '-1%22%2C%22shshshfpa%22%3A%22-1%22%2C%22userAgent%22%3A%22-1%22%7D'
        session.headers.add('Content-Type', 'application/x-www-form-urlencoded')
        try:
            response = await session.post(url, data=body)
            text = await response.text()
            data = json.loads(text)
            logger.info("{}: {}".format(name, data))
            if data['code'] != '0':
                self._result.append({
                    'name': name,
                    'status': self.status_fail,
                    'message': data['echo']
                })
            else:
                data = data['data']
                if int(data['status']) == 2 or int(data['status']) == 1:
                    daily_award = data['dailyAward']
                    self._result.append({
                        'name': name,
                        'status': self.status_signed,
                        'message': daily_award['subTitle'] + ':{}京豆.'.format(daily_award['beanAward']['beanCount'])
                    })
                else:
                    self._result.append({
                        'name': name,
                        'status': self.status_fail,
                        'message': '原因未知'
                    })
        except Exception as e:
            logger.info("{}, 异常: {}".format(name, e.args))
            self._result.append({
                'name': name,
                'status': self.status_fail,
                'message': '程序异常出错',
            })

    @logger.catch
    async def jd_store(self, session):
        """
        京东超市签到
        :param session:
        :return:
        """
        name = '京东超市-签到'
        url = 'https://api.m.jd.com/api?appid=jdsupermarket&functionId=smtg_sign&clientVersion=8.0.0&client=m&body' \
              '=%7B%7D'
        session.headers.add('Origin', 'https://jdsupermarket.jd.com')
        try:
            response = await session.get(url)
            text = await response.text()
            data = json.loads(text)
            logger.info('{}, 数据: {}'.format(name, data))

            if data['code'] != 0:
                message = data['data']['bizMsg'].replace('\n', ',')
                self._result.append({
                    'name': name,
                    'status': self.status_fail,
                    'message': message,
                })
            else:
                if data['data']['bizCode'] == 811:
                    self._result.append({
                        'name': name,
                        'status': self.status_signed,
                        'message': '',
                    })
                else:
                    self._result.append({
                        'name': name,
                        'status': self.status_success,
                        'message': data['data']['bizMsg'],
                    })
        except Exception as e:
            logger.info('{}, 异常:{}'.format(name, e.args))
            self._result.append({
                'name': name,
                'status': self.status_fail,
                'message': '程序异常出错',
            })

    @logger.catch
    async def jr_steel(self, session):
        """
        金融钢镚
        :param session:
        :return:
        """
        name = '京东金融-钢镚'
        url = 'https://ms.jr.jd.com/gw/generic/hy/h5/m/signIn1?_={}'.format(int(time.time() * 1000))
        session.headers.add('Referer', 'https://member.jr.jd.com/activities/sign/v5/indexV2.html?channelLv=lsth')
        session.headers.add('Content-type', 'application/x-www-form-urlencoded;charset=UTF-8')
        body = 'reqData=%7B%22videoId%22%3A%22311372930347370496%22%2C%22channelSource%22%3A%22JRAPP6.0%22%2C' \
               '%22channelLv%22%3A%22lsth%22%2C%22riskDeviceParam%22%3A%22%7B%7D%22%7D'
        try:
            response = await session.post(url=url, data=body)
            text = await response.text()
            data = json.loads(text)
            logger.info('{}, 数据: {}'.format(name, data))
            if data['resultCode'] != 0:
                self._result.append({
                    'name': name,
                    'status': self.status_fail,
                    'message': data['resultMsg']
                })
            else:
                if data['resultData']['resBusiCode'] == 15:
                    self._result.append({
                        'name': name,
                        'status': self.status_signed,
                        'message': data['resultData']['resBusiMsg'] + '奖励.',
                    })
                else:
                    self._result.append({
                        'name': name,
                        'status': self.status_success,
                        'message': data['resultData']['resBusiMsg']
                    })
        except Exception as e:
            logger.info('签到失败, 异常:{}'.format(e.args))
            self._result.append({
                'name': name,
                'status': self.status_fail,
                'message': '程序异常出错',
            })

    @logger.catch
    async def jd_turn(self, session):
        """
        京东转盘-查询
        :param session:
        :return:
        """
        name = '京东转盘-查询'
        url = 'https://api.m.jd.com/client.action?functionId=wheelSurfIndex&body=%7B%22actId%22%3A%22jgpqtzjhvaoym%22' \
              '%2C%22appSource%22%3A%22jdhome%22%7D&appid=ld'
        try:
            response = await session.get(url)
            text = await response.text()
            data = json.loads(text)
            logger.info('{}, 数据:{}'.format(name, data))

            if data['code'] != '0':
                self._result.append({
                    'name': name,
                    'status': self.status_fail,
                    'message': data['echo']
                })
            else:
                if 'lotteryCode' in data['data']:
                    self._result.append({
                        'name': name,
                        'status': self.status_success,
                        'message': '',
                    })
                    logger.info('{}, 助力码: {}'.format(name, data['data']['lotteryCode']))
        except Exception as e:
            logger.info('{}, 异常:{}'.format(name, e.args))
            self._result.append({
                'name': name,
                'status': self.status_fail,
                'message': '程序异常出错',
            })

    async def jd_flash_sale(self, session):
        """
        京东闪购-签到
        :param session:
        :return:
        """
        name = '京东闪购-签到'
        url = 'https://api.m.jd.com/client.action?functionId=partitionJdSgin&clientVersion=10.0.4&partner=jingdong' \
              '&sign=4ede62576bdf67ef8a5488a66e275460&sv=101&client=android&st=1623675187639&uuid=a27b83d3d1dba1cc'
        body = 'body=%7B%22version%22%3A%22v2%22%7D'
        session.headers.add('Content-type', 'application/x-www-form-urlencoded;charset=UTF-8')
        try:
            response = await session.post(url=url, data=body)
            text = await response.text()
            data = json.loads(text)
            logger.info('{}, 数据:{}'.format(name, data))

            if data['code'] != '0':
                self._result.append({
                    'name': name,
                    'status': self.status_fail,
                    'message': data['echo']
                })
            else:
                if data['result']['code'] == '2020':
                    self._result.append({
                        'name': name,
                        'status': self.status_fail,
                        'message': '请稍后重试!'
                    })
                else:
                    self._result.append({
                        'name': name,
                        'status': self.status_success,
                        'message': data['result']['msg']
                    })

        except Exception as e:
            logger.info('{}, 异常:{}'.format(name, e.args))
            self._result.append({
                'name': name,
                'status': self.status_fail,
                'message': '程序异常出错',
            })

    async def jd_cash(self, session):
        """
        京东现金红包
        :param session:
        :return:
        """
        name = '京东-现金红包'
        url = 'https://api.m.jd.com/client.action?functionId=pg_interact_interface_invoke&clientVersion=10.0.4&build' \
              '=88623&partner=jingdong&openudid=a27b83d3d1dba1cc&uuid=a27b83d3d1dba1cc&aid=a27b83d3d1dba1cc&uts' \
              '=0f31TVRjBSsqndu4' \
              '%2FjgUPz6uymy50MQJBfnveeoiuNIbXyekvS9ORCSuomai1WQY0wdhG3U33LUq1bIOeJvrjVSe2OAzV8d0c9a' \
              '%2FxxjDubHoGvngh9behA5mRI%2FtJiit%2BOS4ZUfZeP6Z3iJ4BHAnX3gCJK7oGMl' \
              '%2BWRgKLncGjLTENZKciedrOekRwVutgFkgFdY1%2FJCmMNaHwC9zD3xT9g%3D%3D&st=1623675622893&sign' \
              '=78b531002169e564d30e18ef35507d3a&sv=120&client=android&body=%7B%22argMap%22%3A%7B%22currSignCursor' \
              '%22%3A1%7D%2C%22dataSourceCode%22%3A%22signIn%22%2C%22floorToken%22%3A%22caabe244-5288-4029-b533' \
              '-4e5a9a5ff284%22%7D'
        try:
            response = await session.get(url)
            text = await response.text()
            data = json.loads(text)
            logger.info('{}, 数据:{}'.format(name, data))

            if data['success']:
                self._result.append({
                    'name': name,
                    'status': self.status_success,
                    'message': data['message'],
                })
            else:
                self._result.append({
                    'name': name,
                    'status': self.status_fail,
                    'message': data['message'],
                })
        except Exception as e:
            logger.info('{}, 异常:{}'.format(name, e.args))
            self._result.append({
                'name': name,
                'status': self.status_fail,
                'message': '程序异常出错',
            })

    async def jd_magic_cube(self, session):
        """
        京东小魔方
        :param session:
        :return:
        """
        name = '京东小魔方-查询'
        url = 'https://api.m.jd.com/client.action?functionId=getNewsInteractionInfo&appid=smfe&body={}'.format(urlencode({
            'sign': '2'
        }))
        try:
            response = await session.get(url)
            text = await response.text()
            data = json.loads(text)
            if data['result']['code'] != 0:
                self._result.append({
                    'name': name,
                    'status': self.status_fail,
                    'message': ''
                })
            else:
                self._result.append({
                    'name': name,
                    'status': self.status_success,
                    'message': ''
                })
        except Exception as e:
            logger.info('{}, 异常:{}'.format(name, e.args))
            self._result.append({
                'name': name,
                'status': self.status_fail,
                'message': '程序异常出错',
            })

    async def jd_subsidy(self, session):
        """
        京东金贴
        :param session:
        :return:
        """
        name = '京东-金贴'
        url = 'https://ms.jr.jd.com/gw/generic/uc/h5/m/signIn7'
        session.headers.add('Referer', 'https://active.jd.com/forever/cashback/index')

        try:
            response = await session.get(url)
            text = await response.text()
            data = json.loads(text)
            if data['resultCode'] == 0:
                amount = data['resultData']['data']['thisAmount']
                amount_str = str(data['resultData']['data']['thisAmountStr'])
                self._result.append({
                    'name': name,
                    'status': self.status_success,
                    'message': '金贴: {}'.format(amount_str+'元' if amount > 0 else '无')
                })
            else:
                self._result.append({
                    'name': name,
                    'status': self.status_fail,
                    'message': data['resultMsg']
                })

        except Exception as e:
            logger.info('{}, 异常:{}'.format(name, e.args))
            self._result.append({
                'name': name,
                'status': self.status_fail,
                'message': '程序异常出错',
            })

    async def jd_get_cash(self, session):
        """
        京东领现金
        :return:
        """
        name = '京东-领现金'
        url = 'https://api.m.jd.com/client.action?functionId=cash_sign&body=%7B%22remind%22%3A0%2C%22inviteCode%22%3A' \
              '%22%22%2C%22type%22%3A0%2C%22breakReward%22%3A0%7D&client=apple&clientVersion=9.0.8&openudid' \
              '=1fce88cd05c42fe2b054e846f11bdf33f016d676&sign=7e2f8bcec13978a691567257af4fdce9&st=1596954745073&sv=111'

        try:
            response = await session.get(url)
            text = await response.text()
            data = json.loads(text)
            logger.info('{}, 数据:{}'.format(name, data))

            if data['code'] != 0:
                self._result.append({
                    'name': name,
                    'status': self.status_fail,
                    'message': data['echo']
                })
            else:
                data = data['data']
                if data['bizCode'] == 0:
                    self._result.append({
                        'name': name,
                        'status': self.status_success,
                        'message': '明细: {}现金'.format(data['result']['signCash'] if data['result']['signCash'] else '无')
                    })
                elif data['bizCode'] == 201:
                    self._result.append({
                        'name': name,
                        'status': self.status_signed,
                        'message': data['bizMsg'].split('\n')[-1]
                    })
                else:
                    self._result.append({
                        'name': name,
                        'status': self.status_fail,
                        'message': data['result']['bizMsg']
                    })

        except Exception as e:
            logger.info('{}, 异常:{}'.format(name, e.args))
            self._result.append({
                'name': name,
                'status': self.status_fail,
                'message': '程序异常出错',
            })

    async def jd_shake(self, session, award=None):
        """
        京东摇一摇
        :param award: 奖品
        :param session:
        :return:
        """
        if not award:
            award = {
                'bean_count': 0,
                'coupon': ''
            }
        name = '京东-摇一摇'
        url = 'https://api.m.jd.com/client.action?appid=vip_h5&functionId=vvipclub_shaking'
        try:
            response = await session.get(url)
            text = await response.text()
            data = json.loads(text)
            logger.info('{}, 数据:{}'.format(name, data))

            if data['success']:
                data = data['data']
                if 'prizeBean' in data:
                    award['bean_count'] += data['prizeBean']['count']
                if 'prizeCoupon' in data:
                    award['coupon'] += ' 获得满{}减{}优惠券-> {}!'.format(data['prizeCoupon']['quota'],
                                                                   data['prizeCoupon']['discount'],
                                                                   data['prizeCoupon']['limitStr'])
                if data['luckyBox']['freeTimes'] > 0:
                    await self.jd_shake(session, award)
                else:
                    message = ''
                    if award['bean_count'] > 0:
                        message = '获得{}金豆,'.format(award['bean_count'])
                    message += award['coupon']
                    self._result.append({
                        'name': name,
                        'status': self.status_success,
                        'message': message,
                    })
            else:
                if data['resultCode'] == '9000005' or data['resultCode'] == '8000005':
                    message = '已摇过!'
                else:
                    message = data['message']
                self._result.append({
                    'name': name,
                    'status': self.status_fail,
                    'message': message,
                })
        except Exception as e:
            logger.info('{}, 异常:{}'.format(name, e.args))
            self._result.append({
                'name': name,
                'status': self.status_fail,
                'message': '程序异常出错',
            })

    async def jd_killing(self, session):
        """
        京东秒杀
        :param session:
        :return:
        """
        name = '京东-秒杀'
        url = 'https://api.m.jd.com/client.action'
        session.headers.add('Origin', 'https://h5.m.jd.com')
        session.headers.add('Content-type', 'application/x-www-form-urlencoded;charset=UTF-8')
        body = 'functionId=freshManHomePage&body=%7B%7D&client=wh5&appid=SecKill2020'
        try:
            response = await session.post(url=url, data=body)
            text = await response.text()
            data = json.loads(text)
            logger.info('{}, 数据:{}'.format(name, data))

            if data['code'] == '1':
                self._result.append({
                    'name': name,
                    'status': self.status_fail,
                    'message': '暂无有效活动!'
                })
            elif data['code'] == '0':
                self._result.append({
                    'name': name,
                    'status': self.status_success,
                    'message': ''
                })
            else:
                self._result.append({
                    'name': name,
                    'status': self.status_fail,
                    'message': '原因未知',
                })
        except Exception as e:
            logger.info('{}, 异常:{}'.format(name, e.args))
            self._result.append({
                'name': name,
                'status': self.status_fail,
                'message': '程序异常出错',
            })

    async def jd_wonderful(self, session):
        """
        京东精彩
        :return:
        """
        name = '京东-精彩'
        url = 'https://lop-proxy.jd.com/jiFenApi/signInAndGetReward'
        session.headers.add('Referer', 'https://jingcai-h5.jd.com/')
        session.headers.add('appparams', '{"appid":158,"ticket_type":"m"}')
        session.headers.add('lop-dn', 'jingcai.jd.com')
        session.headers.add('Content-type', 'application/x-www-form-urlencoded;charset=UTF-8')
        body = '[{"userNo":"$cooMrdGatewayUid$"}]'
        try:
            response = await session.post(url=url, data=body)
            text = await response.text()
            data = json.loads(text)
            logger.info('{}, 数据:{}'.format(name, data))

            if data['code'] == -101:
                self._result.append({
                    'name': name,
                    'status': self.status_success,
                    'message': data['msg'],
                })
            elif data['code'] == -1:
                self._result.append({
                    'name': name,
                    'status': self.status_signed,
                    'message': data['msg']
                })
            else:
                self._result.append({
                    'name': name,
                    'status': self.status_fail,
                    'message': data['msg']
                })
        except Exception as e:
            logger.info('{}, 异常:{}'.format(name, e.args))
            self._result.append({
                'name': name,
                'status': self.status_fail,
                'message': '程序异常出错',
            })

    async def jd_car(self, session):
        """
        京东汽车
        :param session:
        :return:
        """
        name = '京东-汽车'
        url = 'https://cgame-stadium.jd.com/api/v1/first/login'
        session.headers.add('ActivityId', '6cd8e0c2e84a421ebf4a39d502141861')
        try:
            response = await session.get(url)
            text = await response.text()
            data = json.loads(text)

            logger.info('{}, 数据: {}'.format(name, data))

            if data['status']:
                self._result.append({
                    'name': name,
                    'status': self.status_success,
                    'message': ''
                })
            else:
                self._result.append({
                    'name': name,
                    'status': self.status_fail,
                    'message': data['error']['msg']
                })
        except Exception as e:
            logger.info('{}, 异常:{}'.format(name, e.args))
            self._result.append({
                'name': name,
                'status': self.status_fail,
                'message': '程序异常出错',
            })

    async def get_total_steel(self, session):
        """
        获取总钢镚
        :param session:
        :return:
        """
        name = '京东金融-钢镚查询'
        url = 'https://coin.jd.com/m/gb/getBaseInfo.html'
        try:
            response = await session.get(url)
            text = await response.text()
            data = json.loads(text)
            logger.info('{}, 数据:{}'.format(name, data))
            if 'gbBalance' in data:
                self._result.append({
                    'name': name,
                    'status': self.status_success,
                    'message': '钢镚:{}￥'.format(data['gbBalance']),
                })
            else:
                self._result.append({
                    'name': name,
                    'status': self.status_success,
                    'message': '原因未知!'
                })
        except Exception as e:
            logger.info('{}, 异常:{}'.format(name, e.args))
            self._result.append({
                'name': name,
                'status': self.status_fail,
                'message': '程序异常出错',
            })

    async def get_total_bean(self, session):
        """
        获取总京豆
        :param session:
        :return:
        """
        name = '京豆查询'
        url = 'https://me-api.jd.com/user_new/info/GetJDUserInfoUnion'
        try:
            response = await session.get(url)
            text = await response.text()
            data = json.loads(text)
            logger.info('{}, 数据:{}'.format(name, data))
            if data['retcode'] == '0':
                bean_num = data['data']['assetInfo']['beanNum']
                self._result.append({
                    'name': name,
                    'status': self.status_success,
                    'message': '京豆余额: {}'.format(bean_num)
                })
            else:
                self._result.append({
                    'name': name,
                    'status': self.status_fail,
                    'message': data['msg']
                })

        except Exception as e:
            logger.info('{}, 异常:{}'.format(name, e.args))
            self._result.append({
                'name': name,
                'status': self.status_fail,
                'message': '程序异常出错',
            })

    async def get_total_cash(self, session):
        """
        京东红包查询
        :param session:
        :return:
        """
        name = '京东-红包查询'
        try:
            url = 'https://api.m.jd.com/client.action?functionId=myhongbao_balance'
            body = 'body=%7B%22fp%22%3A%22-1%22%2C%22appToken%22%3A%22apphongbao_token%22%2C%22childActivityUrl%22%3A' \
                   '%22-1%22%2C%22country%22%3A%22cn%22%2C%22openId%22%3A%22-1%22%2C%22childActivityId%22%3A%22-1%22' \
                   '%2C%22applicantErp%22%3A%22-1%22%2C%22platformId%22%3A%22appHongBao%22%2C%22isRvc%22%3A%22-1%22' \
                   '%2C%22orgType%22%3A%222%22%2C%22activityType%22%3A%221%22%2C%22shshshfpb%22%3A%22-1%22%2C' \
                   '%22platformToken%22%3A%22apphongbao_token%22%2C%22organization%22%3A%22JD%22%2C%22pageClickKey%22' \
                   '%3A%22-1%22%2C%22platform%22%3A%221%22%2C%22eid%22%3A%22-1%22%2C%22appId%22%3A%22appHongBao%22%2C' \
                   '%22childActiveName%22%3A%22-1%22%2C%22shshshfp%22%3A%22-1%22%2C%22jda%22%3A%22-1%22%2C%22extend' \
                   '%22%3A%22-1%22%2C%22shshshfpa%22%3A%22-1%22%2C%22activityArea%22%3A%22-1%22%2C' \
                   '%22childActivityTime%22%3A%22-1%22%7D&client=apple&clientVersion=8.5.0&d_brand=apple' \
                   '&networklibtype=JDNetworkBaseAF&openudid=1fce88cd05c42fe2b054e846f11bdf33f016d676&sign' \
                   '=fdc04c3ab0ee9148f947d24fb087b55d&st=1581245397648&sv=120'
            session.headers.add('Content-type', 'application/x-www-form-urlencoded;charset=UTF-8')
            response = await session.post(url=url, data=body)
            text = await response.text()
            data = json.loads(text)
            logger.info('{}, 数据:{}'.format(name, data))
            if 'resultCode' in data and data['resultCode'] == 200:
                self._result.append({
                    'name': name,
                    'status': self.status_success,
                    'message': '总余额:{}￥, 可用余额:{}￥！'.format(data['balanceMap']['allOrgBalance'],
                                                           data['balanceMap']['totalUsableBalance'])
                })
            else:
                self._result.append({
                    'name': name,
                    'status': self.status_fail,
                    'message': data['echo']
                })

        except Exception as e:
            logger.info('{}, 异常:{}'.format(name, e.args))
            self._result.append({
                'name': name,
                'status': self.status_fail,
                'message': '程序异常出错',
            })

    async def get_total_subsidy(self, session):
        """
        总金贴查询
        :param session:
        :return:
        """
        name = '金贴查询'
        url = 'https://ms.jr.jd.com/gw/generic/uc/h5/m/mySubsidyBalance'
        session.headers.add('Referer', 'https://active.jd.com/forever/cashback/index?channellv=wojingqb')
        try:
            response = await session.get(url)
            text = await response.text()
            data = json.loads(text)
            logger.info('{}, 数据: {}'.format(name, text))
            if 'resultCode' in data and data['resultCode'] == 0:
                self._result.append({
                    'name': name,
                    'status': self.status_success,
                    'message': '金贴余额:{}￥!'.format(data['resultData']['data']['balance'])
                })
            else:
                self._result.append({
                    'name': name,
                    'status': self.status_fail,
                    'message': data['resultMsg']
                })
        except Exception as e:
            logger.info('{}, 异常:{}'.format(name, e.args))
            self._result.append({
                'name': name,
                'status': self.status_fail,
                'message': '程序异常出错',
            })

    async def output(self):
        """
        :return:
        """
        console.print('\n')
        start_line = "============================账号: {}==============================".format(self._pt_pin)
        console.print(start_line, style='bold blue')
        for i in range(len(self._result)):
            res = self._result[i]
            console.print("\t{}.{}: {}! {}".format(i+1, res['name'], self.status_msg[res['status']], res['message']),
                          style='bold green')

        console.print('=' * (len(start_line)+2), style='bold blue')
        console.print('\n')

    async def start(self):
        cookies = {
            'pt_pin': self._pt_pin,
            'pt_key': self._pt_key,
        }
        headers = {
            'user-agent': 'okhttp/3.12.1;jdmall;android;version/10.0.4;build/88623;screen/1080x2293;os/11;network/wifi;',
        }
        async with aiohttp.ClientSession(headers=headers, cookies=cookies) as session:
            is_login = await self.is_login(session)
            if not is_login:
                console.print("账号: {}, cookies已过期, 请重新获取...".format(self._pt_pin))
                return
            await self.jd_bean(session)  # 京东京豆
            await self.jd_store(session)  # 京东超市
            await self.jr_steel(session)  # 金融钢镚
            await self.jd_turn(session)   # 京东转盘
            await self.jd_flash_sale(session)  # 京东闪购
            await self.jd_cash(session)  # 京东现金红包
            await self.jd_magic_cube(session)  # 京东小魔方
            await self.jd_subsidy(session)  # 京东金贴
            await self.jd_get_cash(session)  # 京东领现金
            await self.jd_shake(session)  # 京东摇一摇
            await self.jd_killing(session)  # 京东秒杀, API提示没有权限
            await self.jd_wonderful(session)  # 京东精彩
            await self.jd_car(session)  # 京东汽车
            await self.get_total_steel(session)  # 总钢镚查询
            await self.get_total_bean(session)  # 总金豆查询
            await self.get_total_cash(session)  # 红包查询
            await self.get_total_subsidy(session)  # 金贴查询

        await self.output()


def start():
    console.print("开始执行京东签到合集...", style='bold yellow')
    jd_cookies = os.getenv('JD_COOKIES', None)
    if not jd_cookies:
        console.print("未设置JD_COOKIES环境变量, 退出程序")
        return
    jd_cookie_list = jd_cookies.split('&')

    for jd_cookie in jd_cookie_list:
        pt_pin = re.findall('pt_pin=(.*?);', jd_cookie)
        pt_key = re.findall('pt_key=(.*?);', jd_cookie)

        if len(pt_pin) != 1 or len(pt_key) != 1:
            console.print("JD_COOKIE有误, 请检查配置")
            continue
        pt_pin = pt_pin[0]
        pt_key = pt_key[0]
        app = JdSignCollection(pt_pin, pt_key)
        asyncio.run(app.start())

    console.print("京东签到合集执行完毕...", style='bold yellow')


if __name__ == '__main__':
    start()