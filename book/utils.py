import requests
import json
def get_book_info(isbn):
    api_key = "AIzaSyB7rNc6Xo04DcfeZs0EgX-iA4bqw8uPIWM"
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}&key={api_key}"
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response JSON: {data}")  # 受け取ったJSONレスポンスを確認
        if 'items' in data:
            volume_info = data['items'][0]['volumeInfo']
            published_date = volume_info.get('publishedDate', '')
            if len(published_date) == 7:
                published_date += "-01"  # 年と月の場合、日を1日に設定
            elif len(published_date) == 4:
                published_date += "-01-01"  
            book_info = {
                'title': volume_info.get('title', ''),
                'authors': ', '.join(volume_info.get('authors', [])),
                'publisher':volume_info.get('publisher', ''),
                'publication_date': published_date,
                'category': ', '.join(volume_info.get('categories', [])),
                'image_link': volume_info.get('imageLinks', {}).get('thumbnail', ''),
                'price' : volume_info.get('price', ''),
                'edition' : volume_info.get('edition', ''),
            }
            return book_info
        return None
    elif response.status_code == 429:
        return {'error': 'APIクォータが超過しました。しばらく待ってから再試行してください。'}
    else:
        return {'error': f"エラーが発生しました。ステータスコード: {response.status_code}"}
