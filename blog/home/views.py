from django.shortcuts import render
from home.models import ArticleCategory, Article
from django.http import HttpResponseNotFound
from django.core.paginator import Paginator, EmptyPage

# Create your views here.
from django.views import View


class IndexView(View):
    """首页广告"""

    def get(self, request):

        # 获取所有分类信息
        categories = ArticleCategory.objects.all()

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



