"""blog URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # 通过include，把users下的urls.py文件导入，即包含下所有路由
    # include参数中，首先设置一个元祖 urlconf_module, app_name
    # urlconf_module: 子应用的路由
    # app_name: 子应用的名字pa
    # namespace: 命名空间，区分不同子应用下路由，一般和子应用即可
    path('', include(('users.urls', 'users'), namespace='users')),

    path('', include(('home.urls', 'home'), namespace='home')),


]
