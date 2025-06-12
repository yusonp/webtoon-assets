import os
from flask import Flask, jsonify, render_template
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re
import time

app = Flask(__name__)
CORS(app)  # CORS 정책 해결

def extract_episode_count(text):
    """텍스트에서 화수 추출"""
    if not text:
        return 0
    
    # 숫자 패턴 찾기
    numbers = re.findall(r'\d+', text)
    if numbers:
        return int(numbers[0])  # 마지막 숫자를 화수로 사용
    return 0

# webtoon_backend.py

def get_webtoon_data():
    """웹툰 데이터를 크롤링하고 썸네일을 로컬에 저장합니다."""
    try:
        TARGET_URL = 'https://blacktoon373.com' # 실제 접속 가능한 주소
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': TARGET_URL
        }
        
        response = requests.get(TARGET_URL, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        webtoons = []
        
        # 1. 이미지 저장 경로 설정 및 폴더 생성
        save_dir = os.path.join('static', 'images')
        os.makedirs(save_dir, exist_ok=True)
        
        list_container = soup.find('div', id='toonbook_list')
        if not list_container:
            return []

        webtoon_items = list_container.find_all('div', id=re.compile(r'^toon_'))

        for item in webtoon_items:
            try:
                webtoon_id = int(item['id'].replace('toon_', ''))
                link_tag = item.find('a', class_='toon-link')
                if not link_tag: continue

                relative_url = link_tag['href']
                url = TARGET_URL + relative_url
                title = link_tag.get('title', '제목 없음').strip()

                img_tag = item.find('img', class_='lazyload')
                thumbnail_url = img_tag.get('data-original') if img_tag else ''

                author_tag = item.find('p', class_='text-muted mt-1').find('span') if item.find('p', class_='text-muted mt-1') else None
                author = author_tag.get_text(strip=True) if author_tag else '작가 미상'
                
                episode_p_tag = item.find('h3').find_next_sibling('p')
                episode_text = episode_p_tag.get_text(strip=True) if episode_p_tag else '0'
                episodes = extract_episode_count(episode_text)

                # 2. 썸네일 다운로드 및 로컬 경로 생성
                local_thumbnail_path = ''
                if thumbnail_url:
                    # 파일 확장자를 가져오거나 .jpg로 통일
                    file_ext = os.path.splitext(thumbnail_url)[1] or '.jpg'
                    filename = f"{webtoon_id}{file_ext}"
                    save_path = os.path.join(save_dir, filename)
                    
                    # 3. 파일이 존재하지 않으면 다운로드
                    if not os.path.exists(save_path):
                        img_response = requests.get(thumbnail_url, headers=headers, stream=True)
                        if img_response.status_code == 200:
                            with open(save_path, 'wb') as f:
                                for chunk in img_response.iter_content(1024):
                                    f.write(chunk)
                            print(f"{filename} 다운로드 완료.")
                    
                    # 4. 프론트엔드에 전달할 로컬 경로 설정
                    local_thumbnail_path = f"/static/images/{filename}"

                webtoons.append({
                    'id': webtoon_id,
                    'title': title,
                    'author': author,
                    'episodes': episodes,
                    'thumbnail': local_thumbnail_path, # !! 원본 URL 대신 로컬 경로 전달 !!
                    'url': url
                })
            except Exception as e:
                print(f'개별 웹툰 파싱/저장 오류: {e}')
                continue
        
        return webtoons
        
    except Exception as e:
        print(f'크롤링 전체 오류: {e}')
        return []
        
@app.route('/api/webtoons')
def get_webtoons():
    """웹툰 목록 API"""
    try:
        webtoons = get_webtoon_data()
        
        # 100화 이상만 필터링
        filtered_webtoons = [w for w in webtoons if w['episodes'] >= 100]
        
        # 화수 순으로 정렬
        sorted_webtoons = sorted(filtered_webtoons, key=lambda x: x['episodes'], reverse=True)
        
        return jsonify({
            'success': True,
            'data': sorted_webtoons,
            'total': len(sorted_webtoons)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/webtoon/<int:webtoon_id>')
def get_webtoon_detail(webtoon_id):
    """특정 웹툰 상세 정보"""
    # 실제로는 데이터베이스나 캐시에서 가져와야 함
    return jsonify({
        'success': True,
        'data': {
            'id': webtoon_id,
            'title': '웹툰 제목',
            'episodes': 150
        }
    })

# webtoon_backend.py 파일에 추가

# requests 모듈이 상단에 import 되어 있는지 확인하세요.
# import requests

@app.route('/api/image-proxy')
def image_proxy():
    # 프론트엔드에서 'url' 파라미터로 전달한 이미지 주소를 받습니다.
    img_url = requests.args.get('url')
    if not img_url:
        # URL이 없으면 404 에러 반환
        return 'Image not found', 404

    try:
        # 핫링킹을 우회하기 위해 헤더를 설정합니다.
        headers = {
            'Referer': 'https://blacktoon373.com', # 이미지가 원래 있던 사이트 주소
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # requests를 이용해 이미지를 가져옵니다.
        response = requests.get(img_url, headers=headers, stream=True)
        response.raise_for_status()
        
        # 이미지의 Content-Type을 그대로 전달하여 브라우저가 이미지로 인식하게 합니다.
        content_type = response.headers.get('Content-Type', 'image/jpeg')
        
        return response.content, 200, {'Content-Type': content_type}

    except requests.exceptions.RequestException as e:
        print(f"이미지 프록시 오류: {e}")
        return 'Failed to fetch image', 500
        
@app.route('/')
def index():
    # 이 이름과 실제 파일 이름이 정확히 같아야 합니다.
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)