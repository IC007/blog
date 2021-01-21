from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.

# 对默认的User进行扩展，然后在 settings.py中，替换掉默认的User
class User(AbstractUser):
    # tel
    mobile = models.CharField(max_length=11, unique=True, blank=False)
    # head_img, upload_to 保存到指定位置
    avatar = models.ImageField(upload_to='avatar/%Y%m%d/', blank=True)
    # 简介
    user_desc = models.CharField(max_length=500, blank=True)

    class Meta:
        # 表名
        db_table = 'tb_users'
        # admin后台显示
        verbose_name = '用户管理'
        # admin后台显示
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.mobile
