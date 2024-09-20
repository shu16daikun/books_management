from django.db import models
from project import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
import re

class Storage(models.Model):
    floor = models.IntegerField(verbose_name="階数", null=True)
    area = models.CharField(max_length=30, verbose_name='エリア', null=True)
    def __str__(self):
        return f"{self.floor}階 {self.area}"
    class Meta:
        ordering = ['floor', 'area']
        constraints = [
            models.UniqueConstraint(fields=['floor', 'area'], name='unique_floor_area')
        ]
    
    def clean(self):
        # 禁止文字が含まれているかチェック
        if re.search(r"[;'\"]", self.area):
            raise ValidationError("不正な文字が含まれています。")
        return super().clean()

class Books(models.Model):
    isbn = models.CharField(
        max_length=13,
        verbose_name='ISBN',
        validators=[
            RegexValidator(
                regex=r'^97\d{11}$',
                message='ISBNは「97」で始まる13桁の数字である必要があります。',
            )
        ],
        blank=False
    )
    title = models.CharField(max_length=100, verbose_name='タイトル', blank=False)
    author = models.CharField(max_length=100, verbose_name='著者' , blank=False)
    publisher = models.CharField(max_length=100, verbose_name='出版社', null=True, blank=True)
    publication_date = models.DateField(verbose_name='出版日', null=True, blank=True)
    category = models.CharField(max_length=100, verbose_name='カテゴリー', null=True, blank=True)
    image_link = models.URLField(verbose_name='画像リンク', null=True, blank=True)
    price = models.IntegerField(verbose_name='価格', null=True, blank=True)
    edition = models.IntegerField(verbose_name='版数', null=True, blank=True)
    purchase_date = models.DateField(verbose_name='購入日',null=True, blank=True)
    storage = models.ForeignKey(Storage, on_delete=models.SET_NULL,verbose_name='保管場所' ,null=True, blank=False)
    is_lend_out = models.BooleanField(
        verbose_name=('貸出状況'),
        default=False
    )
    
    def __str__(self):
        return self.title
    
class Review(models.Model):
    books = models.ForeignKey(Books, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comment = models.TextField(verbose_name="レビュー内容")
    def clean(self):
        # 禁止文字が含まれているかチェック
        if re.search(r"[;'\"]", self.comment):
            raise ValidationError("不正な文字が含まれています。")
        return super().clean()

    def __str__(self):
        return f"{self.user} - {self.books.title}"

class Lending(models.Model):
    books = models.ForeignKey(Books, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reservation_checkout_date = models.DateField(verbose_name='予約貸出日',null=True, blank=True)
    reservation_scheduled_return_date = models.DateField(verbose_name='予約返却予定日',null=True, blank=True)
    checkout_date = models.DateField(verbose_name='貸出日',null=True, blank=True)
    scheduled_return_date = models.DateField(verbose_name='返却予定日',null=True, blank=True)
    return_date = models.DateField(verbose_name='返却日',null=True, blank=True)
    cancel_date = models.DateField(verbose_name='予約キャンセル日', null=True, blank=True)
    def __str__(self):
        return f"{self.user} - {self.books.title}-{self.reservation_checkout_date}-{self.reservation_scheduled_return_date}-{self.checkout_date}-{self.scheduled_return_date}-{self.return_date}-{self.cancel_date}"