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
import re
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from users.models import User
from django.db import DatabaseError
from django.shortcuts import redirect
from django.urls import reverse
from home.models import ArticleCategory, Article
import logging

logger = logging.getLogger('fei_log')


# 注册视图


class RegisterView(View):
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        """
        1.接收数据
        2.验证数据
            2.1 参数是否齐全
            2.2 手机号的格式是否正确
            2.3 密码是否符合格式
            2.4 密码和确认密码要一致
            2.5 短信验证码是否和redis中的一致
        3.保存注册信息
        4.返回响应跳转到指定页面
        :param request:
        :return:
        """
        # 1.接收数据
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        smscode = request.POST.get('sms_code')
        # 2.验证数据
        #     2.1 参数是否齐全
        if not all([mobile, password, password2, smscode]):
            return HttpResponseBadRequest('缺少必要的参数')
        #     2.2 手机号的格式是否正确
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseBadRequest('手机号不符合规则')
        #     2.3 密码是否符合格式
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return HttpResponseBadRequest('请输入8-20位密码，密码是数字，字母')
        #     2.4 密码和确认密码要一致
        if password != password2:
            return HttpResponseBadRequest('两次密码不一致')
        #     2.5 短信验证码是否和redis中的一致
        redis_conn = get_redis_connection('default')
        redis_sms_code = redis_conn.get('sms:%s' % mobile)
        if redis_sms_code is None:
            return HttpResponseBadRequest('短信验证码已过期')
        if smscode != redis_sms_code.decode():
            return HttpResponseBadRequest('短信验证码不一致')
        # 3.保存注册信息
        # create_user 可以使用系统的方法来对密码进行加密
        try:
            user = User.objects.create_user(username=mobile,
                                            mobile=mobile,
                                            password=password)
        except DatabaseError as e:
            logger.error(e)
            return HttpResponseBadRequest('注册失败')

        login(request, user)
        # 4.返回响应跳转到指定页面
        # 暂时返回一个注册成功的信息，后期再实现跳转到指定页面

        # redirect 是进行重定向
        # reverse 是可以通过 namespace:name 来获取到视图所对应的路由
        response = redirect(reverse('home:index'))
        # return HttpResponse('注册成功，重定向到首页')

        # 设置cookie信息，以方便首页中 用户信息展示的判断和用户信息的展示
        response.set_cookie('is_login', True)
        response.set_cookie('username', user.username, max_age=7 * 24 * 3600)

        return response


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
            return JsonResponse({'code': RETCODE.NECESSARYPARAMERR, 'errmsg': '缺少必要参数'})

        redis_conn = get_redis_connection('default')
        redis_image_code = redis_conn.get('img:%s' % uuid)

        if redis_image_code is None:
            return JsonResponse({'code': RETCODE.NECESSARYPARAMERR, 'errmsg': '图片验证码已过期'})
        try:
            redis_conn.delete('img:%s' % uuid)
        except Exception as e:
            logger.error(e)
        # 注意验证码大小写，redis数据是bytes类型
        if redis_image_code.decode().lower() != image_code.lower():
            return JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图片验证码错误'})

        # 六位数字验证码
        sms_code = '%06d' % randint(0, 999999)
        # 记录验证码到日志
        logger.info(sms_code)

        redis_conn.setex('sms:%s' % mobile, 300, sms_code)

        # 参数1： 测试手机号
        # 参数2：模板内容列表： {1} 短信验证码   {2} 分钟有效
        # 参数3：模板 免费开发测试使用的模板ID为1
        CCP().send_template_sms(mobile, [sms_code, 5], 1)

        return JsonResponse({'code': RETCODE.OK, 'errmsg': '短信发送成功'})


# 登陆
class LoginView(View):

    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        """
        接收参数
        参数验证
            验证手机号
            验证密码是否符合
        用户认证登陆
        登陆状态保持
        根据用户选择是否记住登陆状态
        为了首页显示我们需要设置一些cookie信息
        返回响应
        """
        # 接收参数
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        remember = request.POST.get('remember')

        # 参数验证
        # 验证手机号
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseBadRequest('手机号不符合规则')
            # 验证密码是否符合
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return HttpResponseBadRequest('密码不符合规则')
        # 用户认证登陆
        # 采用系统自带的认证方法认证
        # 如果用户名密码正确，返回user
        # 如果用户名或密码不正确，返回None
        # 系统自带的方法默认是针对username字段进行判断
        # 当前判断信息是手机号，所以我们需要在User模型中修改认证字段
        user = authenticate(mobile=mobile, password=password)
        if user is None:
            return HttpResponseBadRequest('用户名或密码错误')
        # 登陆状态保持
        login(request, user)
        # 根据用户选择是否记住登陆状态
        # 为了首页显示我们需要设置一些cookie信息

        # 根据 next参数进行页面跳转
        # 获取next参数内容
        next_page = request.GET.get('next')
        if next_page:
            response = redirect(next_page)
        else:
            response = redirect(reverse('home:index'))

        if remember != 'on':
            # 浏览器关闭后
            request.session.set_expiry(0)
            response.set_cookie('is_login', True)
            response.set_cookie('username', user.username, max_age=14 * 24 * 3600)
        else:
            # 记住两周
            request.session.set_expiry(None)
            response.set_cookie('is_login', True, max_age=14 * 24 * 3600)
            response.set_cookie('username', user.username, max_age=14 * 24 * 3600)
        # 返回响应
        return response


# 登出
class LogoutView(View):

    def get(self, request):
        # session 清除
        logout(request)
        # 删除部分cookie数据
        response = redirect(reverse('home:index'))
        response.delete_cookie('is_login')
        # 跳转到首页
        return response


# 个人中心
# 判断是否登录, 若未登录，则会默认跳转
# 默认跳转路由 /accounts/login/?next=/center/
class UserCenterView(LoginRequiredMixin, View):

    def get(self, request):
        # 获取登录用户的信息
        user = request.user
        # 组织获取用户的信息
        context = {
            'username': user.username,
            'mobile': user.mobile,
            'avatar': user.avatar.url if user.avatar else None,
            'user_desc': user.user_desc
        }
        return render(request, 'center.html', context=context)


# 写日志
class WriteBlogView(LoginRequiredMixin, View):

    def get(self, request):
        # 查询所有分类莫西
        categories = ArticleCategory.objects.all()

        context = {
            'categories': categories
        }

        return render(request, 'write_blog.html', context=context)

    def post(self, request):
        # 接收数据
        avatar = request.FILES.get('avatar')
        title = request.POST.get('title')
        category_id = request.POST.get('category')
        tags = request.POST.get('tags')
        summary = request.POST.get('summary')
        content = request.POST.get('content')
        user = request.user
        # 验证数据
            # 验证参数是否齐全
        if not all([avatar, title, category_id, summary, content]):
            return HttpResponseBadRequest('参数不全')
            # 判断分类ID
        try:
            article_category = ArticleCategory.objects.get(id=category_id)
        except ArticleCategory.DoesNotExist:
            return HttpResponseBadRequest('没有此分类')
        # 数据入库
        try:
            article = Article.objects.create(
                author=user,
                avatar=avatar,
                category=article_category,
                tags=tags,
                summary=summary,
                content=content
            )
        except Exception as e:
            logger.error(e)
            return HttpResponseBadRequest('发布失败，请稍后再试')
        # 跳转到指定页
        return redirect(reverse('home:index'))
