from django.contrib import admin
from home.models import ArticleCategory, Article
# Register your models here.

# 这里注册后，可以在django自带的admin后台进行修改响应的模块
admin.site.register(ArticleCategory)
admin.site.register(Article)


