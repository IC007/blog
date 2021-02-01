# 进行users子应用视图路由
from django.urls import path
from users.views import RegisterView, ImageCodeView, SmsCodeView, LoginView, LogoutView, UserCenterView, WriteBlogView

urlpatterns = [
    # path 第一个参数：路由
    # path 第二个参数：视图函数名
    # 注册
    path('register/', RegisterView.as_view(), name='register'),

    # 图片验证码
    path('imagecode/', ImageCodeView.as_view(), name='imagecode'),

    # 短信验证码
    path('smscode/', SmsCodeView.as_view(), name='smscode'),

    # 登陆
    path('login/', LoginView.as_view(), name='login'),

    # 登出
    path('logout/', LogoutView.as_view(), name='logout'),

    # 个人中心
    path('center/', UserCenterView.as_view(), name='center'),

    # 写博客
    path('writeblog/', WriteBlogView.as_view(), name='writeblog'),
]
