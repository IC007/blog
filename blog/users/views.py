from django.shortcuts import render

# Create your views here.

from django.views import View
from django.http.response import HttpResponseBadRequest
from libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from django.http import HttpResponse


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
        接收参数
        验证参数
            参数是否齐全
            参数是否正确
        生成短信验证码
        保存短信验证码到redis
        发送短信
        返回响应
        """