from django.urls import path
from . import views

app_name = "book"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path('management/', views.InformationView.as_view(), name="management"),
    path('management/books/create/', views.BookCreateView.as_view(), name="books_create"),
    path('management/books/delete/<int:pk>/', views.BookDeleteView.as_view(), name="books_delete"),
    path('management/books/retrieve_book/', views.retrieve_book, name='retrieve_book'),
    path('management/books/update/<int:pk>/', views.BookUpdateView.as_view(), name="books_update"),
    path('management/books/list/', views.BookManagementListView.as_view(), name="books_list"),
    path('management/reviews/', views.ReviewListView.as_view(), name="reviews_list"),
    path('management/reviews/delete/<int:pk>/', views.ReviewDeleteView.as_view(), name="reviews_delete"),
    path('management/storage/', views.StorageListView.as_view(), name="storage_list"),
    path('management/storage/create/', views.StorageCreateView.as_view(), name="storage_create"),
    path('management/storage/update/<int:pk>/', views.StorageUpdateView.as_view(), name="storage_update"),
    path('management/storage/delete/<int:pk>/', views.StorageDeleteView.as_view(), name="storage_delete"),
    path('management/lending/', views.LendingManagementView.as_view(), name="lending_management"),
    path('management/lending/reservation/', views.LendingReservationView.as_view(), name="lending_reservation"),
    path('management/lending/cancel/', views.LendingCancelView.as_view(), name="lending_cancel"),
    path('management/lending/now/', views.LendingNowView.as_view(), name="lending_now"),
    path('management/lending/return/', views.LendingReturnView.as_view(), name="lending_return"),
    path('management/lending/overdue/', views.LendingOverdueView.as_view(), name="lending_overdue"),
    path('bookshelf/', views.BookshelfView.as_view(), name="bookshelf"),
    path('search/', views.BookSearchView.as_view(), name="book_search"),
    path('<int:pk>/', views.BookDetailView.as_view(), name="book_detail"),
    path('reservation/<int:book_pk>/', views.BookReservationView.as_view(), name="book_reservation"),
    path('reservation/<int:book_pk>/done/<int:pk>/<str:user_token>/<str:url_token>/', views.BookReservationDoneView.as_view(), name="book_reservation_done"),
    path('rent/<int:book_pk>/', views.BookRentView.as_view(), name="book_rent"),
    path('rent/<int:book_pk>/done/<int:pk>/<str:user_token>/<str:url_token>/', views.BookRentDoneView.as_view(), name="book_rent_done"),
    path('rent/list/', views.RentListView.as_view(), name='rent_list'),
    path('return/<int:pk>/<str:user_token>/<str:url_token>/', views.ReturnBookView.as_view(), name="return_book"),
    path('cancel/<int:pk>/<str:user_token>/<str:url_token>/', views.CancelReservationView.as_view(), name="cancel_reservation"),
    path('review/<int:pk>/<str:user_token>/<str:url_token>/', views.ReviewView.as_view(), name='review'),
    path('review/<int:pk>/done/<str:user_token>/<str:url_token>/', views.ReviewDoneView.as_view(), name="review_done"),
]