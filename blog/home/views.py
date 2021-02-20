from django.shortcuts import render
from home.models import Comment
from home.models import Article
from home.models import ArticleCategory
from django.http import HttpResponseNotFound
from django.core.paginator import Paginator, EmptyPage
from django.shortcuts import redirect
from django.urls import reverse
# Create your views here.
from django.views import View


class IndexView(View):
    """首页广告"""

    def get(self, request):

        # 接收用户点击的分类id
        # ?cat_id=xxx&page_num=xxx&page_size=xxx
        cat_id = request.GET.get('cat_id', 1)
        # 判断分类ID,根据分类id进行分类查询
        try:
            category = ArticleCategory.objects.get(id=cat_id)
        except ArticleCategory.DoesNotExist:
            return HttpResponseNotFound('没有此分类')
        # 获取博客分类信息
        categories = ArticleCategory.objects.all()

        # 获取分页参数
        page_num = request.GET.get('page_num', 1)
        page_size = request.GET.get('page_size', 10)

        # 根据分类信息查询文章数据
        articles = Article.objects.filter(category=category)

        # 创建分页器
        paginator = Paginator(articles, per_page=page_size)

        # 分页处理
        try:
            page_articles = paginator.page(page_num)
        except EmptyPage:
            return HttpResponseNotFound('empty page')

        # 总页数
        total_page = paginator.num_pages
        # 组织数据传递给模板
        context = {
            'categories': categories,
            'category': category,
            'articles': page_articles,
            'page_size': page_size,
            'total_page': total_page,
            'page_num': page_num
        }

        return render(request, 'index.html', context=context)


class DetailView(View):

    def get(self, request):

        # detail/?id=xxx&page_num=xxx&page_size=xxx
        # 获取文章id
        article_id = request.GET.get('id')
        try:
            article = Article.objects.get(id=article_id)
        except Article.DoesNotExist:
            return render(request, '404.html')
        else:
            # 浏览后，浏览量+1
            article.total_views += 1
            article.save()
        # 查询浏览量前10的文章
        # orderby默认是升序，我们通过负号 - 来改为降序
        hot_articles = Article.objects.order_by('-total_views')[:9]
        # 获取分类信息
        categories = ArticleCategory.objects.all()

        # 获取分页请求参数
        page_size = request.GET.get('page_size', 10)
        page_num = request.GET.get('page_num', 1)

        # 根据文章信息查询评论数据
        comments = Comment.objects.filter(article=article).order_by('-created')

        # 获取评论总数
        total_count = comments.count()

        # 创建分页器
        paginator = Paginator(comments, page_size)

        # 进行分页处理
        try:
            page_comments = paginator.page(page_num)
        except  EmptyPage:
            return HttpResponseNotFound('empty page')

        # 总页数
        total_page = paginator.num_pages

        context = {
            'categories': categories,
            'category': article.category,
            'article': article,
            'hot_articles': hot_articles,
            'total_count': total_count,
            'comments': comments,
            'page_size': page_size,
            'total_page': total_page,
            'page_num': page_num
        }
        return render(request, 'detail.html', context=context)

    def post(self, request):
        # 获取用户信息
        user = request.user

        # 判断用户是否登录
        if user and user.is_authenticated:
            # 接收数据
            article_id = request.POST.get('id')
            content = request.POST.get('content')

            # 判断文章是否存在
            try:
                article = Article.objects.get(id=article_id)
            except Article.DoesNotExist:
                return HttpResponseNotFound('文章不存在')

            # 保存到数据
            Comment.objects.create(
                content=content,
                article=article,
                user=user
            )

            # 修改文章评论数量
            article.comments_count += 1
            article.save()

            # 拼接跳转路由
            path = reverse('home:detail')+'?id={}'.format(article_id)
            return redirect(path)
        
        else:
            # 未登录则跳转至登录页面
            return redirect(reverse('users:login'))


