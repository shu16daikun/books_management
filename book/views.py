from django.forms import BaseModelForm
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View, TemplateView, DetailView, ListView, CreateView, DeleteView, UpdateView
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.http import urlencode
from django.contrib import messages
from django.http import HttpResponseBadRequest
from datetime import datetime, timedelta
from .forms import *
from .utils import get_book_info
from .models import *
import json
import os
from django.conf import settings

class IndexView(TemplateView):
    """ ホームビュー """
    template_name = "index.html"
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

class InformationView(TemplateView):
    template_name = "book/information.html"
    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        if user.is_authenticated:
            no_storage = Books.objects.filter(
                storage__isnull=True,
            )
            context['no_storage'] = no_storage
        return context

class StorageListView(ListView):
    template_name = "book/storage_list.html"
    model = Storage
    ordering = ['floor', 'area']
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

class StorageCreateView(CreateView):
    model = Storage
    template_name = "book/storage_create.html"
    form_class = StorageForm
    success_url = reverse_lazy('book:storage_list')
    def form_valid(self, form):
        return super().form_valid(form)

class StorageUpdateView(UpdateView):
    model = Storage
    fields = '__all__'
    template_name = 'book/storage_update.html'
    success_url = reverse_lazy('book:storage_list')
    def form_valid(self, form):
        return super().form_valid(form)

class StorageDeleteView(DeleteView):
    model = Storage
    template_name = "book/storage_delete.html"
    success_url = reverse_lazy('book:storage_list')
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

class BookManagementListView(ListView):
    template_name = "book/books_list.html"
    model = Books
    paginate_by = 20
    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('query')
        if query:
            # モデルのフィールドを取得
            book_fields = [field.name for field in Books._meta.get_fields() if field.get_internal_type() in ['CharField', 'TextField', 'BooleanField']]
            # Storageモデルのフィールドを取得
            storage_fields = ['storage__floor', 'storage__area']
            # OR条件を作成
            q_objects = Q()
            for field in book_fields:
                if field == 'is_lend_out':
                    if '貸出中' in query:
                        q_objects |= Q(is_lend_out=True)
                    elif '貸出可' in query:
                        q_objects |= Q(is_lend_out=False)
                else:
                    q_objects |= Q(**{f"{field}__icontains": query})
            for field in storage_fields:
                if field == 'storage__floor':
                    try:
                        # '階'を含む部分を処理
                        if '階' in query:
                            floor = int(query.split('階')[0].strip())
                            q_objects |= Q(**{f"{field}": floor})
                    except ValueError:
                        pass
                elif field == 'storage__area':
                    q_objects |= Q(**{f"{field}__icontains": query})
            # クエリセットをフィルタリング
            queryset = queryset.filter(q_objects)
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

class BookCreateView(CreateView):
    model = Books
    form_class = BookForm
    template_name = 'book/books_create.html'
    success_url = reverse_lazy('book:books_list')

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

class BookDeleteView(DeleteView):
    model = Books
    template_name = "book/books_delete.html"
    success_url = reverse_lazy('book:books_list')

class BookUpdateView(UpdateView):
    model = Books
    fields = '__all__'
    template_name = 'book/books_update.html'
    success_url = reverse_lazy('book:books_list')
    def form_valid(self, form):
        return super().form_valid(form)

class LendingManagementView(TemplateView):
    template_name = "book/lending_management.html"

class LendingReservationView(ListView):
    template_name = "book/lending_reservation.html"
    model = Lending
    paginate_by = 30
    context_object_name = 'lendings'
    def get_queryset(self):
        return Lending.objects.filter(
            reservation_checkout_date__isnull=False,
            cancel_date__isnull=True
        ).order_by('reservation_checkout_date')

class LendingCancelView(ListView):
    template_name = "book/lending_cancel.html"
    model = Lending
    paginate_by = 30
    context_object_name = 'lendings'
    def get_queryset(self):
        return Lending.objects.filter(
            reservation_checkout_date__isnull=False,
            cancel_date__isnull=False
        ).order_by('-cancel_date')
    
class LendingNowView(ListView):
    template_name = "book/lending_now.html"
    model = Lending
    paginate_by = 30
    context_object_name = 'lendings'
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

class LendingReturnView(ListView):
    template_name = "book/lending_return.html"
    model = Lending
    paginate_by = 30
    context_object_name = 'lendings'
    def get_queryset(self):
        return Lending.objects.filter(
            return_date__isnull=False
        ).order_by('-return_date')

class LendingOverdueView(ListView):
    template_name = "book/lending_Overdue.html"
    model = Lending
    paginate_by = 30
    context_object_name = 'lendings'
    def get_queryset(self):
        today = datetime.today().date()
        return Lending.objects.filter(
            return_date__isnull=True,
            scheduled_return_date__lt=today
        ).order_by('scheduled_return_date')

class ReviewListView(ListView):
    template_name = "book/reviews_list.html"
    model = Review
    context_object_name = 'reviews'
    paginate_by = 30
    ordering = ['-pk']

class ReviewDeleteView(DeleteView):
    model = Review
    template_name = "book/reviews_delete.html"
    success_url = reverse_lazy('book:reviews_list')
    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        if user.is_authenticated:
            context['object_name'] = f'{self.object.user}-「{self.object.books.title}」-"{self.object.comment}"'
        return context

class BookshelfView(ListView):
    template_name = "book/bookshelf.html"
    model = Books
    paginate_by = 100

class BookSearchView(ListView):
    template_name = "book/book_search.html"
    model = Books
    paginate_by = 100
    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('query')
        if query:
            # モデルのフィールドを取得
            book_fields = [field.name for field in Books._meta.get_fields() if field.get_internal_type() in ['CharField', 'TextField', 'BooleanField']]
            # OR条件を作成
            q_objects = Q()
            for field in book_fields:
                if field == 'is_lend_out':
                    if '貸出中' in query:
                        q_objects |= Q(is_lend_out=True)
                    elif '貸出可' in query:
                        q_objects |= Q(is_lend_out=False)
                else:
                    q_objects |= Q(**{f"{field}__icontains": query})
            # クエリセットをフィルタリング
            queryset = queryset.filter(q_objects)
        return queryset

class BookDetailView(DetailView):
    template_name = "book/book_detail.html"
    model = Books
    context_object_name = 'book'
    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        if user.is_authenticated:
            book = self.get_object()
            context['reviews'] = Review.objects.filter(books=book)
        return context

class BookReservationView(CreateView):
    model = Lending
    form_class = BookReservationForm
    template_name = 'book/book_reservation.html'
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
            print("Book:", book)
            print("Today:", today)
            print("End date:", end_date)
            lendings = Lending.objects.filter(
                books=book, 
                reservation_checkout_date__lte=end_date
            ) | Lending.objects.filter(
                books=book, 
                checkout_date__lte=end_date
            )
            print("Lendings:", lendings)  # デバッグ出力
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
        return reverse('book:book_reservation_done', kwargs={'book_pk': self.kwargs['book_pk'], 'pk': self.object.pk})

class BookReservationDoneView(DetailView):
    template_name = "book/book_reservation_done.html"
    model = Lending
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

class BookRentView(CreateView):
    model = Lending
    form_class = BookRentForm
    template_name = 'book/book_rent.html'
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
            # デバッグ用にフィルタ条件を確認
            print("Book:", book)
            print("Today:", today)
            print("End date:", end_date)

            # 指定された期間内の Lending オブジェクトを取得
            lendings = Lending.objects.filter(
                books=book, 
                reservation_checkout_date__lte=end_date
            ) | Lending.objects.filter(
                books=book, 
                checkout_date__lte=end_date
            )
            print("Lendings:", lendings)  # デバッグ出力
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
        return reverse('book:book_rent_done', kwargs={'book_pk': self.kwargs['book_pk'], 'pk': self.object.pk})

class BookRentDoneView(DetailView):
    template_name = "book/book_rent_done.html"
    model = Lending
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

class RentListView(ListView):
    template_name = "book/rent_list.html"
    model = Lending
    def get_queryset(self):
        user = self.request.user
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

            context['overdue_lendings'] = overdue_lendings
            context['returned_lendings'] = returned_lendings
            context['renting_lendings'] = renting_lendings
            context['reserved_lendings'] = reserved_lendings
            context['today'] = today
        return context

class ReturnBookView(UpdateView):
    model = Lending
    fields = ['return_date']
    template_name = 'book/return_book.html'
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
        print("Lendings:", lendings)  # デバッグ出力
        book.is_lend_out = False
        book.save()
        print("Books.is_lend_out:", book.is_lend_out)
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
        return reverse('book:review', kwargs={'pk': self.object.pk})

class ReviewView(CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'book/review.html'
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
        return reverse('book:review_done', kwargs={'pk': self.object.pk})


class ReviewDoneView(DetailView):
    template_name = "book/review_done.html"
    model = Review
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

class CancelReservationView(UpdateView):
    model = Lending
    fields = ['cancel_date']
    template_name = 'book/cancel_reservation.html'
    success_url = reverse_lazy('book:rent_list')
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
        print("Lendings:", lendings)
        if not lendings:
            book.is_lend_out = False
            book.save()
        print("Books.is_lend_out:", book.is_lend_out)
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