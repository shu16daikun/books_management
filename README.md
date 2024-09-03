# ポートフォリオ
# 1.分散型図書管理システム

## プロジェクトの概要
#### プロジェクトの内容  
本プロジェクトは、ビル内で分散して保管されている図書情報を管理するものです。図書の登録、貸出、返却などの機能を提供します。
#### プロジェクトの行程
* 開発開始　2024/07/12
* 設計　~2024/07/19
* 開発　~2024/08/09
* デザイン　~2024/08/20
* テスト　~2024/09/03現在作業中

## 開発環境

本プロジェクトは、WindowsOSのローカル環境で開発しました。

推奨ブラウザはGoogle Chromeです。

#### 使用言語（フレームワーク・ライブラリ）
* Python（Django）
* JavaScript（jQuery、Quagga、fullcalendar）
* HTML/CSS、Bootstrap

#### セットアップ方法
1. リポジトリのクローンを作成します。
   ```
   git clone https://github.com/shu16daikun/books_management.git
   ```
2. 必要なライブラリをインストールします。
   ```
   pip install -r requirements.txt
   ```
3. projectディレクトリ内のsetting.pyで、データベースの設定を行います。本プロジェクトではMySQLを使用。
4. マイグレーションを実行します。
   ```
   python manage.py migrate
   ```
5. MySQL Serverを起動。
   ```
   mysqld --standalone
   ```
6. 管理者アカウントの作成。
   管理者アカウントでログインする際は、下記コードを用いて作成
   ```
   py manage.py createsuperuser
   #ユーザー名、E-mailアドレス、パスワードを設定する
   
7. ローカルサーバーを起動します。
   ```
   py manage.py runserver
   ```
8. ブラウザで下記URLにアクセス。
   ```
   http://127.0.0.1:8000/
   ```
9. 「サインアップ」でユーザーアカウントを作成でき、管理者アカウントでログインする場合は「ログイン」を選択する。

## 機能

#### 管理者側
* ISBNから図書情報を取得し、登録
* 図書の管理
* 保管場所の管理
* レビューの管理
* 貸出、返却の管理

#### ユーザー側
* 図書の検索
* 図書の予約、予約キャンセル
* 図書のレンタル、返却
* 図書のレビューを書く
 
## デモ

#### 本の登録

図書を新規登録する画面です。デバイスカメラから本のISBNコードを読み取り、GoogleBooksAPIsを用いて図書情報を自動入力できます。

![本の登録](docs/image/book_create.png)

#### ユーザー本棚

ユーザーが登録されている図書を閲覧・検索できる画面です。図書画像を選択することで詳細画面や、貸出画面に進むことができます。

![本棚](docs/image/bookshelf.png)

#### 貸出状況管理画面

貸出状況に応じて図書情報を閲覧できる画面です。下記画像は、現在貸出中のものの画面です。

![貸出状況管理画面](docs/image/lending_management.png)

## 著者
 
* 作成者：代 脩一郎(Dai Shuichiro）
* 所属：就労移行支援施設Kaien大宮　訓練生
