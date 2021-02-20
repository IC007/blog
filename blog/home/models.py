from django.db import models
from django.utils import timezone
from users.models import User

# Create your models here.


class ArticleCategory(models.Model):
    """
    文章分类
    """
    # 分类标题
    title = models.CharField(max_length=100, blank=True)
    # 分类的创建时间
    created = models.DateTimeField(default=timezone.now)

    # 会让我们在django-admin后台可以看到我们输入的内容
    def __str__(self):
        return self.title

    class Meta:
        db_table = 'tb_category'  # 修改表名
        verbose_name = '类别管理'  # admin站点显示
        verbose_name_plural = verbose_name


# 文章模型
class Article(models.Model):
    """
    作者
    标题图
    标题
    分类
    标签
    摘要
    正文
    浏览量
    评论量
    文章创建时间
    文章的修改时间
    """
    # 作者
    # on_delete, 当user表中数据删除后，文章信息同步删除
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    # 标题图
    avatar = models.ImageField(upload_to='article/%Y%m%d/', blank=True)
    # 标题
    title = models.CharField(max_length=20, blank=True)
    # 分类
    category = models.ForeignKey(
        ArticleCategory,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='article'
    )
    # 标签
    tags = models.CharField(max_length=20, blank=True)
    # 摘要
    summary = models.CharField(max_length=200, null=False, blank=False)
    # 正文
    content = models.TextField()
    # 浏览量
    total_views = models.PositiveIntegerField(default=0)
    # 评论量
    comments_count = models.PositiveIntegerField(default=0)
    # 文章创建时间
    created = models.DateTimeField(default=timezone.now)
    # 文章的修改时间
    updated = models.DateTimeField(auto_now=True)

    # 修改表名、以及django-admin展示配置信息
    class Meta:
        db_table = 'tb_article'
        ordering = ('-created',)
        verbose_name = '文章管理'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title


# 评论模型
class Comment(models.Model):

    # 评论内容
    content = models.TextField()
    # 评论的文章
    article = models.ForeignKey(Article, on_delete=models.SET_NULL, null=True)
    # 评论的用户
    user = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    # 评论的时间
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.article.title

    class Meta:
        db_table = 'tb_comment'
        verbose_name = '评论管理'
        verbose_name_plural = verbose_name