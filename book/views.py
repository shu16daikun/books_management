from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View,TemplateView, DetailView, ListView, CreateView, DeleteView, UpdateView
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from django.http import  HttpRequest, HttpResponse, JsonResponse
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from datetime import datetime, timedelta
from .forms import *
from .utils import get_book_info
from .models import *
from accounts.models import UserToken
from urllib.parse import urlparse
import secrets
import json

def generate_user_token(user):
    # トークンを生成し、データベースに保存
    token = secrets.token_urlsafe()  # URLセーフなトークンを生成
    UserToken.objects.update_or_create(user=user, defaults={'token': token})
    return token

def get_user_token(user):
    # ユーザーに関連付けられたトークンを取得
    try:
        user_token = UserToken.objects.get(user=user)
        return user_token.token
    except UserToken.DoesNotExist:
        return None  # トークンが存在しない場合は None を返す

def search_user_token(user):
    db_token = get_user_token(user)
    if not db_token:
        generate_user_token(user)
        db_token = get_user_token(user)
    return db_token 

class BaseView(LoginRequiredMixin, View):
    def check_token(self, request, user, session_token, url_token):
        
        db_token = search_user_token(user)
        print(f"User: {user}, DB Token: {db_token}")

        if db_token is not None:
            user_token =  self.request.session.get('user_token')
            print(f"URL User Token from DB: {user_token}")
            user_token = UserToken.objects.filter(token=user_token).first()
            print(f"User Token from DB: {user_token}")
            if user_token is None or user.id != user_token.user_id:
                print(f"Token mismatch or invalid user. User ID: {user.id}, Token User ID: {user_token.user_id if user_token else 'None'}")
                return HttpResponseForbidden("不正なアクセスです。")
        else:
            print("DB Token is None")
            return HttpResponseForbidden("不正なアクセスです。")

        if not session_token or session_token != url_token:
            print(f"Session Token: {session_token}, URL Token: {url_token}")
            return HttpResponseForbidden("不正なアクセスです。")

        return None  # トークンチェックが成功した場合はNoneを返す
    
    
class IndexView(TemplateView):
    """ ホームビュー """
    template_name = "index.html"

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            session_token = secrets.token_urlsafe()
            self.request.session['session_token'] = session_token  # トークンをセッションに保存
            print(self.request.session.get('session_token'))#デバック
            
            user_token = search_user_token(user)
            self.request.session['user_token'] = user_token
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        if user.is_authenticated:
            user = self.request.user
            today = datetime.today().date()
            # 「返却期限が過ぎている物」
            overdue_lendings = Lending.objects.filter(
                user=user,
                return_date__isnull=True,
                scheduled_return_date__lt=today
            )
            # 「予約中のもので返却がまだされていないもの」
            not_returned = Lending.objects.filter(
                user=user,
                reservation_checkout_date__lte=today,
                cancel_date__isnull=True,
            )
            context['overdue_lendings'] = overdue_lendings
            context['not_returned'] = not_returned
        return context

class InformationView(LoginRequiredMixin, TemplateView):
    template_name = "book/information.html"
    login_url = 'accounts:login' 

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            session_token = secrets.token_urlsafe()
            self.request.session['session_token'] = session_token  # トークンをセッションに保存
            print(self.request.session.get('session_token'))#デバック
            user = self.request.user
            user_token = search_user_token(user)
            self.request.session['user_token'] = user_token
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        if user.is_authenticated:
            no_storage = Books.objects.filter(
                storage__isnull=True,
            )
            context['no_storage'] = no_storage
        return context

class StorageListView(LoginRequiredMixin, ListView):
    template_name = "book/storage_list.html"
    login_url = 'accounts:login' 
    model = Storage
    ordering = ['floor', 'area']

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            session_token = secrets.token_urlsafe()
            self.request.session['session_token'] = session_token  # トークンをセッションに保存
            print(self.request.session.get('session_token'))#デバック
            user = self.request.user
            user_token = search_user_token(user)
            self.request.session['user_token'] = user_token
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        storages = Storage.objects.all()
        storage_usage = []
        for storage in storages:
            is_used = Books.objects.filter(storage=storage).exists()
            if is_used:
                storage_usage.append(storage.pk)
        print("Storage:", storage_usage)
        if user.is_authenticated:
            context['storage_usage'] = storage_usage
        return context

class StorageCreateView(LoginRequiredMixin, CreateView):
    model = Storage
    template_name = "book/storage_create.html"
    login_url = 'accounts:login' 
    form_class = StorageForm
    success_url = reverse_lazy('book:storage_list')
    def form_valid(self, form):
        return super().form_valid(form)
    
    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            session_token = secrets.token_urlsafe()
            self.request.session['session_token'] = session_token  # トークンをセッションに保存
            print(self.request.session.get('session_token'))#デバック
            user = self.request.user
            user_token = search_user_token(user)
            self.request.session['user_token'] = user_token
        return super().dispatch(request, *args, **kwargs)

class StorageUpdateView(LoginRequiredMixin, UpdateView):
    model = Storage
    fields = '__all__'
    template_name = 'book/storage_update.html'
    login_url = 'accounts:login' 
    success_url = reverse_lazy('book:storage_list')
    def form_valid(self, form):
        return super().form_valid(form)
    
    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            session_token = secrets.token_urlsafe()
            self.request.session['session_token'] = session_token  # トークンをセッションに保存
            print(self.request.session.get('session_token'))#デバック
            user = self.request.user
            user_token = search_user_token(user)
            self.request.session['user_token'] = user_token
        return super().dispatch(request, *args, **kwargs)

class StorageDeleteView(LoginRequiredMixin, DeleteView):
    model = Storage
    template_name = "book/storage_delete.html"
    login_url = 'accounts:login' 
    success_url = reverse_lazy('book:storage_list')

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            session_token = secrets.token_urlsafe()
            self.request.session['session_token'] = session_token  # トークンをセッションに保存
            print(self.request.session.get('session_token'))#デバック
            user = self.request.user
            user_token = search_user_token(user)
            self.request.session['user_token'] = user_token
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        # オブジェクトを取得
        obj = super().get_object(queryset)
        if not obj:
            messages("このオブジェクトは既に削除済みです")
        return obj
    
    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        storages = Storage.objects.all()
        storage_usage = []
        for storage in storages:
            is_used = Books.objects.filter(storage=storage).exists()
            if is_used:
                storage_usage.append(storage.pk)
        if user.is_authenticated:
            context['object_name'] = f'{self.object.floor}階 {self.object.area}'
            context['storage_usage'] = storage_usage
        return context

class BookManagementListView(LoginRequiredMixin, ListView):
    template_name = "book/books_list.html"
    login_url = 'accounts:login' 
    model = Books
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            session_token = secrets.token_urlsafe()
            self.request.session['session_token'] = session_token  # トークンをセッションに保存
            print(self.request.session.get('session_token'))#デバック
            user = self.request.user
            user_token = search_user_token(user)
            self.request.session['user_token'] = user_token
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = super().get_queryset().order_by('id')
        query = self.request.GET.get('query')
        if query:
            book_fields = [field.name for field in Books._meta.get_fields() if field.get_internal_type() in ['CharField', 'TextField', 'IntegerField', 'DateField', 'BooleanField']]
            storage_fields = ['storage__floor', 'storage__area']
            
            q_objects = Q()
            q_objects_floor = Q()
            q_objects_area = Q()
            
            for field in book_fields:
                if field == 'publication_date' or field == 'purchase_date':
                    if '年' in query and '月' in query and '日' in query:
                        try:
                            year, month, day = query.replace('年', '-').replace('月', '-').replace('日', '').split('-')
                            formatted_date = f"{year}-{int(month):02}-{int(day):02}"
                            formatted_date = datetime.strptime(formatted_date, '%Y-%m-%d').date()
                            q_objects |= Q(**{f"{field}__exact": formatted_date})
                        except ValueError as e:
                            # エラーメッセージを出力して処理を続行
                            print(f"Invalid date format: {query}. Error: {e}")
                elif field == 'price' or field == 'edition':
                    try:
                        num = int(query)
                        q_objects |= Q(**{f"{field}": num})
                    except ValueError as e:
                        # エラーメッセージを出力して処理を続行
                        print(f"Invalid number format: {query}. Error: {e}")
                elif field == 'is_lend_out':
                    if '貸出中' in query:
                        q_objects |= Q(is_lend_out=True)
                    elif '貸出可' in query:
                        q_objects |= Q(is_lend_out=False)
                else:
                    q_objects |= Q(**{f"{field}__icontains": query})

            for field in storage_fields:
                if '階' in query:
                    parts = query.split('階', 1)
                    if len(parts) > 1:
                        try:
                            floor = int(parts[0].strip())
                            area = parts[1].strip()
                            
                            q_objects_floor = Q(**{"storage__floor": floor})
                            
                            if area == "":
                                q_objects |= q_objects_floor
                            else:
                                q_objects_area = Q(**{"storage__area__icontains": area})
                        except ValueError as e:
                            # エラーメッセージを出力して処理を続行
                            print(f"Invalid floor format: {query}. Error: {e}")
                else:
                    q_objects |= Q(**{f"storage__area": query})

            # AND条件を & で結びつける
            if q_objects_floor and q_objects_area:
                queryset = queryset.filter(q_objects_floor & q_objects_area)
            else:
                queryset = queryset.filter(q_objects).order_by('id')
        return queryset
    
    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        books = Books.objects.all()
        book_usage = []
        for book in books:
            if book.is_lend_out:
                book_usage.append(book.pk)
        if user.is_authenticated:
            no_storage = Books.objects.filter(
                storage__isnull=True,
            )
            context['no_storage'] = no_storage
            context['book_usage'] = book_usage
        return context

class BookCreateView(LoginRequiredMixin, CreateView):
    model = Books
    form_class = BookForm
    template_name = 'book/books_create.html'
    login_url = 'accounts:login' 
    success_url = reverse_lazy('book:books_list')

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            session_token = secrets.token_urlsafe()
            self.request.session['session_token'] = session_token  # トークンをセッションに保存
            print(self.request.session.get('session_token'))#デバック
            user = self.request.user
            user_token = search_user_token(user)
            self.request.session['user_token'] = user_token
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        isbn = form.cleaned_data.get('isbn')
        if Books.objects.filter(isbn=isbn).exists():
            messages.warning(self.request, "すでにこのISBNは登録されていますが、追加で登録いたしますか？")
            # ここで追加の確認を行い、OKなら登録処理を続行します
            if 'confirm' in self.request.POST:
                return super().form_valid(form)
            else:
                return self.render_to_response(self.get_context_data(form=form))
        return super().form_valid(form)
    
def retrieve_book(request):
    if request.method == 'POST':
        isbn = request.POST.get('isbn')
        print("ISBN:", isbn)#デバック用
        book_info = get_book_info(isbn)
        if book_info:
            print(f"Book info retrieved: {book_info}")  # 取得された本の情報を確認
            return JsonResponse(book_info)
        else:
            return JsonResponse({'error': '本の情報が見つかりませんでした。'})
    return JsonResponse({'error': '無効なリクエストです。'})

class BookDeleteView(LoginRequiredMixin, DeleteView):
    model = Books
    template_name = "book/books_delete.html"
    login_url = 'accounts:login' 
    success_url = reverse_lazy('book:books_list')

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            session_token = secrets.token_urlsafe()
            self.request.session['session_token'] = session_token  # トークンをセッションに保存
            print(self.request.session.get('session_token'))#デバック
            user = self.request.user
            user_token = search_user_token(user)
            self.request.session['user_token'] = user_token
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        # オブジェクトを取得
        obj = super().get_object(queryset)
        if not obj:
            messages("このオブジェクトは既に削除済みです")
        return obj

class BookUpdateView(LoginRequiredMixin, UpdateView):
    model = Books
    fields = '__all__'
    template_name = 'book/books_update.html'
    login_url = 'accounts:login' 
    success_url = reverse_lazy('book:books_list')

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            session_token = secrets.token_urlsafe()
            self.request.session['session_token'] = session_token  # トークンをセッションに保存
            print(self.request.session.get('session_token'))#デバック
            user = self.request.user
            user_token = search_user_token(user)
            self.request.session['user_token'] = user_token
        return super().dispatch(request, *args, **kwargs)

class LendingManagementView(LoginRequiredMixin, TemplateView):
    template_name = "book/lending_management.html"
    login_url = 'accounts:login' 

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            session_token = secrets.token_urlsafe()
            self.request.session['session_token'] = session_token  # トークンをセッションに保存
            print(self.request.session.get('session_token'))#デバック
            user = self.request.user
            user_token = search_user_token(user)
            self.request.session['user_token'] = user_token
        return super().dispatch(request, *args, **kwargs)

class LendingReservationView(LoginRequiredMixin, ListView):
    template_name = "book/lending_reservation.html"
    login_url = 'accounts:login' 
    model = Lending
    paginate_by = 30
    context_object_name = 'lendings'

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            session_token = secrets.token_urlsafe()
            self.request.session['session_token'] = session_token  # トークンをセッションに保存
            print(self.request.session.get('session_token'))#デバック
            user = self.request.user
            user_token = search_user_token(user)
            self.request.session['user_token'] = user_token
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return Lending.objects.filter(
            reservation_checkout_date__isnull=False,
            cancel_date__isnull=True
        ).order_by('reservation_checkout_date')
    
    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        if user.is_authenticated:
            today = datetime.today().date()
            context['today'] = today
        return context

class LendingCancelView(LoginRequiredMixin, ListView):
    template_name = "book/lending_cancel.html"
    login_url = 'accounts:login' 
    model = Lending
    paginate_by = 30
    context_object_name = 'lendings'

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            session_token = secrets.token_urlsafe()
            self.request.session['session_token'] = session_token  # トークンをセッションに保存
            print(self.request.session.get('session_token'))#デバック
            user = self.request.user
            user_token = search_user_token(user)
            self.request.session['user_token'] = user_token
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return Lending.objects.filter(
            reservation_checkout_date__isnull=False,
            cancel_date__isnull=False
        ).order_by('-cancel_date')
    
class LendingNowView(LoginRequiredMixin, ListView):
    template_name = "book/lending_now.html"
    login_url = 'accounts:login' 
    model = Lending
    paginate_by = 30
    context_object_name = 'lendings'

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            session_token = secrets.token_urlsafe()
            self.request.session['session_token'] = session_token  # トークンをセッションに保存
            print(self.request.session.get('session_token'))#デバック
            user = self.request.user
            user_token = search_user_token(user)
            self.request.session['user_token'] = user_token
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return Lending.objects.filter(
            return_date__isnull=True,
            checkout_date__isnull=False,
        ).order_by('scheduled_return_date')
    
    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        if user.is_authenticated:
            today = datetime.today().date()
            context['today'] = today
        return context

class LendingReturnView(LoginRequiredMixin, ListView):
    template_name = "book/lending_return.html"
    login_url = 'accounts:login' 
    model = Lending
    paginate_by = 30
    context_object_name = 'lendings'

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            session_token = secrets.token_urlsafe()
            self.request.session['session_token'] = session_token  # トークンをセッションに保存
            print(self.request.session.get('session_token'))#デバック
            user = self.request.user
            user_token = search_user_token(user)
            self.request.session['user_token'] = user_token
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return Lending.objects.filter(
            return_date__isnull=False
        ).order_by('-return_date')

class LendingOverdueView(LoginRequiredMixin, ListView):
    template_name = "book/lending_Overdue.html"
    login_url = 'accounts:login' 
    model = Lending
    paginate_by = 30
    context_object_name = 'lendings'

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            session_token = secrets.token_urlsafe()
            self.request.session['session_token'] = session_token  # トークンをセッションに保存
            print(self.request.session.get('session_token'))#デバック
            user = self.request.user
            user_token = search_user_token(user)
            self.request.session['user_token'] = user_token
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        today = datetime.today().date()
        return Lending.objects.filter(
            return_date__isnull=True,
            scheduled_return_date__lt=today
        ).order_by('scheduled_return_date')

class ReviewListView(LoginRequiredMixin, ListView):
    template_name = "book/reviews_list.html"
    login_url = 'accounts:login' 
    model = Review
    context_object_name = 'reviews'
    paginate_by = 30
    ordering = ['-pk']

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            session_token = secrets.token_urlsafe()
            self.request.session['session_token'] = session_token  # トークンをセッションに保存
            print(self.request.session.get('session_token'))#デバック
            user = self.request.user
            user_token = search_user_token(user)
            self.request.session['user_token'] = user_token
        return super().dispatch(request, *args, **kwargs)

class ReviewDeleteView(LoginRequiredMixin, DeleteView):
    model = Review
    template_name = "book/reviews_delete.html"
    login_url = 'accounts:login' 
    success_url = reverse_lazy('book:reviews_list')

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            session_token = secrets.token_urlsafe()
            self.request.session['session_token'] = session_token  # トークンをセッションに保存
            print(self.request.session.get('session_token'))#デバック
            user = self.request.user
            user_token = search_user_token(user)
            self.request.session['user_token'] = user_token
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        # オブジェクトを取得
        obj = super().get_object(queryset)
        if not obj:
            messages("このオブジェクトは既に削除済みです")
        return obj

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        if user.is_authenticated:
            context['object_name'] = f'{self.object.user}-「{self.object.books.title}」-"{self.object.comment}"'
        return context

class BookshelfView(LoginRequiredMixin, ListView):
    template_name = "book/bookshelf.html"
    login_url = 'accounts:login' 
    model = Books
    paginate_by = 100

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            session_token = secrets.token_urlsafe()
            self.request.session['session_token'] = session_token  # トークンをセッションに保存
            print(self.request.session.get('session_token'))#デバック
            user = self.request.user
            user_token = search_user_token(user)
            self.request.session['user_token'] = user_token
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return Books.objects.order_by('id') 

class BookSearchView(LoginRequiredMixin, ListView):
    template_name = "book/book_search.html"
    login_url = 'accounts:login' 
    model = Books
    paginate_by = 100

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            session_token = secrets.token_urlsafe()
            self.request.session['session_token'] = session_token  # トークンをセッションに保存
            print(self.request.session.get('session_token'))#デバック
            user = self.request.user
            user_token = search_user_token(user)
            self.request.session['user_token'] = user_token
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('query')
        if query:
            # モデルのフィールドを取得
            book_fields = [field.name for field in Books._meta.get_fields() if field.get_internal_type() in ['CharField', 'TextField', 'IntegerField', 'DateField', 'BooleanField']]
            # OR条件を作成
            q_objects = Q()
            for field in book_fields:
                if field == 'publication_date' or field == 'purchase_date':
                    if '年' in query and '月' in query and '日' in query:
                        try:
                            year, month, day = query.replace('年', '-').replace('月', '-').replace('日', '').split('-')
                            formatted_date = f"{year}-{int(month):02}-{int(day):02}"
                            formatted_date = datetime.strptime(formatted_date, '%Y-%m-%d').date()
                            q_objects |= Q(**{f"{field}__exact": formatted_date})
                        except ValueError as e:
                            # エラーメッセージを出力して処理を続行
                            print(f"Invalid date format: {query}. Error: {e}")
                elif field == 'price' or field == 'edition':
                    try:
                        num = int(query)
                        q_objects |= Q(**{f"{field}": num})
                    except ValueError as e:
                        # エラーメッセージを出力して処理を続行
                        print(f"Invalid number format: {query}. Error: {e}")
                elif field == 'is_lend_out':
                    if '貸出中' in query:
                        q_objects |= Q(is_lend_out=True)
                    elif '貸出可' in query:
                        q_objects |= Q(is_lend_out=False)
                else:
                    q_objects |= Q(**{f"{field}__icontains": query})
            # クエリセットをフィルタリング
            queryset = queryset.filter(q_objects).order_by('id') 
        return queryset

class BookDetailView(LoginRequiredMixin, DetailView):
    template_name = "book/book_detail.html"
    login_url = 'accounts:login' 
    model = Books
    context_object_name = 'book'

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            session_token = secrets.token_urlsafe()
            self.request.session['session_token'] = session_token  # トークンをセッションに保存
            print(self.request.session.get('session_token'))#デバック
            user = self.request.user
            user_token = search_user_token(user)
            self.request.session['user_token'] = user_token
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        if user.is_authenticated:
            book = self.get_object()
            context['reviews'] = Review.objects.filter(books=book)
        return context

class BookReservationView(BaseView, CreateView):
    model = Lending
    form_class = BookReservationForm
    template_name = 'book/book_reservation.html'
    login_url = 'accounts:login'

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            session_token = secrets.token_urlsafe()
            self.request.session['session_token'] = session_token  # トークンをセッションに保存
            print(self.request.session.get('session_token'))#デバック
            user = self.request.user
            user_token = search_user_token(user)
            self.request.session['user_token'] = user_token
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['initial']['books'] = get_object_or_404(Books, pk=self.kwargs['book_pk'])
        kwargs['initial']['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.books = get_object_or_404(Books, pk=self.kwargs['book_pk'])
        checkout_date = self.request.POST.get('checkout_date')
        scheduled_return_date = self.request.POST.get('scheduled_return_date')
        
        # フォームに値をセット
        today = datetime.today().date()
        book = form.instance.books
        if checkout_date == today:
            if book.is_lend_out == False:
                form.instance.reservation_checkout_date = None
                form.instance.reservation_scheduled_return_date = None
                book.is_lend_out = True
                book.save()
            else:
                form.instance.reservation_checkout_date = checkout_date
                form.instance.reservation_scheduled_return_date = scheduled_return_date
                form.instance.checkout_date = None
                form.instance.scheduled_return_date = None
        else:
            form.instance.reservation_checkout_date = checkout_date
            form.instance.reservation_scheduled_return_date = scheduled_return_date
            form.instance.checkout_date = None
            form.instance.scheduled_return_date = None
        response = super().form_valid(form)
        
        return response

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        if user.is_authenticated:
            book_pk = self.kwargs.get('book_pk')
            book = get_object_or_404(Books, pk=book_pk)
            today = datetime.today().date()
            end_date = today + timedelta(days=35)
            lendings = Lending.objects.filter(
                books=book, 
                reservation_checkout_date__lte=end_date
            ) | Lending.objects.filter(
                books=book, 
                checkout_date__lte=end_date
            )
            # 貸出不可能な日付をリストに追加
            unavailable_dates = []
            for lending in lendings:
                if not lending.return_date and not lending.cancel_date:
                    if lending.reservation_checkout_date:
                        start_date = lending.reservation_checkout_date
                        end_date = lending.reservation_scheduled_return_date
                    elif lending.checkout_date:
                        start_date = lending.checkout_date
                        end_date = lending.scheduled_return_date
                    while start_date <= end_date:
                        unavailable_dates.append(start_date.strftime('%Y-%m-%d'))
                        start_date += timedelta(days=1)
            print("Unavailable dates:", unavailable_dates)
            # コンテキストに book と unavailable_dates を追加
            context['book'] = book
            context['unavailable_dates'] = json.dumps(unavailable_dates)
        return context
    
    def get_success_url(self):
        url_token = secrets.token_urlsafe()
        self.request.session['session_token'] = url_token  # トークンをセッションに保存
        print(f'url:{self.request.session.get('session_token')}')#デバック
        user = self.request.user
        user_token = search_user_token(user)
        self.request.session['user_token'] = user_token
        print(f'User:{user_token}')
        return reverse('book:book_reservation_done', kwargs={'book_pk': self.kwargs['book_pk'], 'pk': self.object.pk, 'user_token': user_token, 'url_token': url_token})

class BookReservationDoneView(BaseView,DetailView):
    template_name = "book/book_reservation_done.html"
    login_url = 'accounts:login' 
    model = Lending

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            #許可されたURLのみ画面を表示する処理
            user = request.user
            session_token = request.session.get('session_token')
            print(self.request.session.get('session_token'))#デバック
            url_token = kwargs.get('url_token')
            print(f'URL:{url_token}')#デバック
            error_response = self.check_token(request, user, session_token, url_token)
            if error_response:
                return error_response
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        if user.is_authenticated:
            # 親クラスの get_context_data メソッドを呼び出してデフォルトのコンテキストデータを取得
            # リクエストのパラメータから book_id を取得
            book_pk = self.kwargs.get('book_pk')
            # book_id を使って特定の Books オブジェクトを取得
            book = get_object_or_404(Books, pk=book_pk)
            storage = book.storage
            # コンテキストに book を追加
            context['book'] = book
            context['storage'] = storage
        return context

class BookRentView(BaseView,CreateView):
    model = Lending
    form_class = BookRentForm
    template_name = 'book/book_rent.html'
    login_url = 'accounts:login' 

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            session_token = secrets.token_urlsafe()
            self.request.session['session_token'] = session_token  # トークンをセッションに保存
            print(self.request.session.get('session_token'))#デバック
            user = self.request.user
            user_token = search_user_token(user)
            self.request.session['user_token'] = user_token
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['initial']['books'] = get_object_or_404(Books, pk=self.kwargs['book_pk'])
        kwargs['initial']['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.books = get_object_or_404(Books, pk=self.kwargs['book_pk'])
        checkout_date = self.request.POST.get('checkout_date')
        scheduled_return_date = self.request.POST.get('scheduled_return_date')
        
        # フォームに値をセット
        today = str(datetime.today().date())
        book = form.instance.books
        if checkout_date == today:
            if book.is_lend_out == False:
                form.instance.reservation_checkout_date = None
                form.instance.reservation_scheduled_return_date = None
                book.is_lend_out = True
                book.save()
            else:
                form.instance.reservation_checkout_date = checkout_date
                form.instance.reservation_scheduled_return_date = scheduled_return_date
                form.instance.checkout_date = None
                form.instance.scheduled_return_date = None
        else:
            form.instance.reservation_checkout_date = checkout_date
            form.instance.reservation_scheduled_return_date = scheduled_return_date
            form.instance.checkout_date = None
            form.instance.scheduled_return_date = None
        response = super().form_valid(form)
        
        return response

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        if user.is_authenticated:
            # 親クラスの get_context_data メソッドを呼び出してデフォルトのコンテキストデータを取得
            # リクエストのパラメータから book_id を取得
            book_pk = self.kwargs.get('book_pk')
            # book_id を使って特定の Books オブジェクトを取得
            book = get_object_or_404(Books, pk=book_pk)
            # 今日の日付を取得
            today = datetime.today().date()
            # 今日から5週間の範囲を設定
            end_date = today + timedelta(days=35)

            # 指定された期間内の Lending オブジェクトを取得
            lendings = Lending.objects.filter(
                books=book, 
                reservation_checkout_date__lte=end_date
            ) | Lending.objects.filter(
                books=book, 
                checkout_date__lte=end_date
            )
            # 貸出不可能な日付をリストに追加
            unavailable_dates = []
            for lending in lendings:
                if not lending.return_date and not lending.cancel_date:
                    if lending.reservation_checkout_date:
                        start_date = lending.reservation_checkout_date
                        end_date = lending.reservation_scheduled_return_date
                    elif lending.checkout_date:
                        start_date = lending.checkout_date
                        end_date = lending.scheduled_return_date
                    while start_date <= end_date:
                        unavailable_dates.append(start_date.strftime('%Y-%m-%d'))
                        start_date += timedelta(days=1)
            print("Unavailable dates:", unavailable_dates)
            # コンテキストに book と unavailable_dates を追加
            context['book'] = book
            context['unavailable_dates'] = json.dumps(unavailable_dates)
        return context
    
    def get_success_url(self):
        url_token = secrets.token_urlsafe()
        self.request.session['session_token'] = url_token  # トークンをセッションに保存
        print(f'url:{self.request.session.get('session_token')}')#デバック
        user = self.request.user
        user_token = search_user_token(user)
        self.request.session['user_token'] = user_token
        print(f'User:{user_token}')
        return reverse('book:book_rent_done', kwargs={'book_pk': self.kwargs['book_pk'], 'pk': self.object.pk, 'user_token': user_token, 'url_token': url_token,})


class BookRentDoneView(BaseView,DetailView):
    template_name = "book/book_rent_done.html"
    login_url = 'accounts:login' 
    model = Lending

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            #許可されたURLのみ画面を表示する処理
            user = request.user
            session_token = request.session.get('session_token')
            print(self.request.session.get('session_token'))#デバック
            url_token = kwargs.get('url_token')
            print(f'URL:{url_token}')#デバック
            error_response = self.check_token(request, user, session_token, url_token)
            if error_response:
                return error_response
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        if user.is_authenticated:
            # 親クラスの get_context_data メソッドを呼び出してデフォルトのコンテキストデータを取得
            # リクエストのパラメータから book_id を取得
            book_pk = self.kwargs.get('book_pk')
            # book_id を使って特定の Books オブジェクトを取得
            book = get_object_or_404(Books, pk=book_pk)
            storage = book.storage
            # コンテキストに book を追加
            context['book'] = book
            context['storage'] = storage
        return context

class RentListView(BaseView, ListView):
    template_name = "book/rent_list.html"
    login_url = 'accounts:login' 
    model = Lending

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            session_token = secrets.token_urlsafe()
            self.request.session['session_token'] = session_token  # トークンをセッションに保存
            print(self.request.session.get('session_token'))#デバック
            user = self.request.user
            user_token = search_user_token(user)
            self.request.session['user_token'] = user_token
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Lending.objects.filter(user=user)

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        if user.is_authenticated:
            user = self.request.user

            today = datetime.today().date()

            # 「返却期限が過ぎている物」
            overdue_lendings = Lending.objects.filter(
                user=user,
                return_date__isnull=True,
                scheduled_return_date__lt=today
            ).order_by('scheduled_return_date')

            # 「返却済み」
            returned_lendings = Lending.objects.filter(
                user=user,
                return_date__isnull=False
            ).order_by('-return_date')[:5]

            # 「レンタル中」
            renting_lendings = Lending.objects.filter(
                user=user,
                return_date__isnull=True,
                checkout_date__isnull=False,
                scheduled_return_date__gte=today
            ).order_by('scheduled_return_date')

            # 「予約中」
            reserved_lendings = Lending.objects.filter(
                user=user,
                reservation_checkout_date__isnull=False,
                cancel_date__isnull=True,
            ).order_by('reservation_checkout_date')

            url_token = secrets.token_urlsafe()
            self.request.session['session_token'] = url_token  # トークンをセッションに保存
            kwargs['url_token'] = url_token
            print(self.request.session.get('session_token'))#デバック
            print(f'URL:{url_token}')#デバック
            user_token = search_user_token(user)

            context['overdue_lendings'] = overdue_lendings
            context['returned_lendings'] = returned_lendings
            context['renting_lendings'] = renting_lendings
            context['reserved_lendings'] = reserved_lendings
            context['today'] = today
            context['url_token'] = url_token
            context['user_token'] = user_token
        return context

class ReturnBookView(BaseView, UpdateView):
    model = Lending
    fields = ['return_date']
    template_name = 'book/return_book.html'
    login_url = 'accounts:login' 

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            #許可されたURLのみ画面を表示する処理
            user = request.user
            session_token = request.session.get('session_token')
            print(self.request.session.get('session_token'))#デバック
            url_token = kwargs.get('url_token')
            print(f'URL:{url_token}')#デバック
            error_response = self.check_token(request, user, session_token, url_token)
            if error_response:
                return error_response
        
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # 返却日を今日の日付に設定
        today = datetime.today().date()
        form.instance.return_date = today
        book = form.instance.books
        lendings = Lending.objects.filter(
            books=book,
            checkout_date__lte=today,
            scheduled_return_date__gte=today,
            return_date__isnull=True
        )
        book.is_lend_out = False
        book.save()
        response =  super().form_valid(form)
        return response 
    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        if user.is_authenticated:
            # Lendingオブジェクトを取得
            lending = self.object
            # 関連するBooksオブジェクトを取得
            book = lending.books
            context['book'] = book
        return context
    
    def get_success_url(self):
        url_token = secrets.token_urlsafe()
        self.request.session['session_token'] = url_token  # トークンをセッションに保存
        print(f'url:{self.request.session.get('session_token')}')#デバック
        user = self.request.user
        user_token = search_user_token(user)
        self.request.session['user_token'] = user_token
        print(f'User:{user_token}')
        return reverse('book:review', kwargs={'pk': self.object.pk, 'user_token': user_token, 'url_token': url_token,})

class ReviewView(BaseView, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'book/review.html'
    login_url = 'accounts:login' 

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            #許可されたURLのみ画面を表示する処理
            user = request.user
            session_token = request.session.get('session_token')
            print(self.request.session.get('session_token'))#デバック
            url_token = kwargs.get('url_token')
            print(f'URL:{url_token}')#デバック
            error_response = self.check_token(request, user, session_token, url_token)
            if error_response:
                return error_response
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        lending = get_object_or_404(Lending, pk=self.kwargs['pk'])
        form.instance.books = lending.books
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        if user.is_authenticated:
            lending = get_object_or_404(Lending, pk=self.kwargs['pk'])
            context['book'] = lending.books
            context['user'] = self.request.user
        return context

    def get_success_url(self):
        url_token = secrets.token_urlsafe()
        self.request.session['session_token'] = url_token  # トークンをセッションに保存
        print(f'url:{self.request.session.get('session_token')}')#デバック
        user = self.request.user
        user_token = search_user_token(user)
        self.request.session['user_token'] = user_token
        print(f'User:{user_token}')
        return reverse('book:review_done', kwargs={'pk': self.object.pk, 'user_token': user_token, 'url_token': url_token,})


class ReviewDoneView(BaseView, DetailView):
    template_name = "book/review_done.html"
    login_url = 'accounts:login' 
    model = Review
    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            #許可されたURLのみ画面を表示する処理
            user = request.user
            session_token = request.session.get('session_token')
            print(self.request.session.get('session_token'))#デバック
            url_token = kwargs.get('url_token')
            print(f'URL:{url_token}')#デバック
            error_response = self.check_token(request, user, session_token, url_token)
            if error_response:
                return error_response
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        if user.is_authenticated:
            # 親クラスの get_context_data メソッドを呼び出してデフォルトのコンテキストデータを取得
            review = self.get_object()
            # レビューに関連する書籍とユーザー情報をコンテキストに追加
            context['book'] = review.books
            context['user'] = review.user
            context['comment'] = review.comment
        return context

class CancelReservationView(BaseView, UpdateView):
    model = Lending
    fields = ['cancel_date']
    template_name = 'book/cancel_reservation.html'
    login_url = 'accounts:login' 
    success_url = reverse_lazy('book:rent_list')

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            #許可されたURLのみ画面を表示する処理
            user = request.user
            session_token = request.session.get('session_token')
            print(self.request.session.get('session_token'))#デバック
            url_token = kwargs.get('url_token')
            print(f'URL:{url_token}')#デバック
            error_response = self.check_token(request, user, session_token, url_token)
            if error_response:
                return error_response
            
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # 返却日を今日の日付に設定
        today = datetime.today().date()
        form.instance.cancel_date = today
        book = form.instance.books
        lendings = Lending.objects.filter(
            books= book,
            checkout_date__lte=today,
            scheduled_return_date__gte=today,
            return_date__isnull=True
        )
        if not lendings:
            book.is_lend_out = False
            book.save()
        response =  super().form_valid(form)
        return response 
    
    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        if user.is_authenticated:
            # Lendingオブジェクトを取得
            lending = self.object
            # 関連するBooksオブジェクトを取得
            book = lending.books
            context['book'] = book
        return context