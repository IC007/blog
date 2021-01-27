from django.shortcuts import render

# Create your views here.

from random import randint
from django.views import View
from django.http.response import HttpResponseBadRequest
from libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from django.http import HttpResponse
from django.http.response import JsonResponse
from utils.response_code import RETCODE
from libs.yuntongxun.sms import CCP
import logging

logger = logging.getLogger('fei_log')

# 注册视图


class RegisterView(View):
    def get(self, request):
        return render(request, 'register.html')


# 验证码
class ImageCodeView(View):
    def get(self, request):
        """
        接收前端传过来的uuid
        判断uuid是否获取到
        通过调用captcha来生成图片验证码(图片二进制和图片内容)
        将图片内容保存到redis中
        uuid为key，图片内容为value，还需设置一个时效
        返回图片二进制
        """

        uuid = request.GET.get('uuid')
        if uuid is None:
            return HttpResponseBadRequest('没有传递uuid')

        text, image = captcha.generate_captcha()
        # 这里的default，就是settings里面redis的default
        redis_conn = get_redis_connection('default')
        # key,value,seconds
        redis_conn.setex('img:%s' % uuid, 300, text)
        # 返回图片二进制
        return HttpResponse(image, content_type='image/jpeg')


# 发送短信验证码
class SmsCodeView(View):

    def get(self, request):
        """
        1、接收参数
        2、验证参数
            2.1 参数是否齐全
            2.2 图片验证码的验证
                连接redis，获取redis中的图片验证码
                判断图片验证码是否存在
                如果图片验证码未过期，我们获取到之后就可以删除图片验证码
                比对图片验证码
        3、生成短信验证码
        4、保存短信验证码到redis
        5、发送短信
        6、返回响应
        """

        mobile = request.GET.get('mobile')
        image_code = request.GET.get('image_code')
        uuid = request.GET.get('uuid')

        if not all([mobile, image_code, uuid]):
            return JsonResponse({'code': RETCODE.NECESSARYPARAMERR,'errmsg': '缺少必要参数'})

        redis_conn = get_redis_connection('default')
        redis_image_code = redis_conn.get('img:%s' % uuid)

        if redis_image_code is None:
            return JsonResponse({'code': RETCODE.NECESSARYPARAMERR,'errmsg': '图片验证码已过期'})
        try:
            redis_conn.delete('img:%s' % uuid)
        except Exception as e:
            logger.error(e)
        # 注意验证码大小写，redis数据是bytes类型
        if redis_image_code.decode().lower() != image_code.lower():
            return JsonResponse({'code': RETCODE.IMAGECODEERR,'errmsg': '图片验证码错误'})

        # 六位数字验证码
        sms_code = '%06d' % randint(0, 999999)
        # 记录验证码到日志
        logger.info(sms_code)

        redis_conn.setex('sms:%s' % mobile, 300, sms_code)

        # 参数1： 测试手机号
        # 参数2：模板内容列表： {1} 短信验证码   {2} 分钟有效
        # 参数3：模板 免费开发测试使用的模板ID为1
        CCP().send_template_sms(mobile,[sms_code, 5], 1)

        return JsonResponse({'code': RETCODE.OK, 'errmsg': '短信发送成功'})

