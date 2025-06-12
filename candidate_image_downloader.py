# candidate_image_downloader.py (Lazy Loading 해결을 위한 강제 스크롤 추가)

import os
import requests
import re
import time

from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from bs4 import BeautifulSoup

def extract_episode_count(text):
    if not text: return 0
    numbers = re.findall(r'\d+', text)
    return int(numbers[-1]) if numbers else 0

def download_candidate_images():
    TARGET_URL = 'https://blacktoon373.com'
    SAVE_DIR = os.path.join('static', 'candidate_images')
    os.makedirs(SAVE_DIR, exist_ok=True)
    
    print("1. 드라이버 설정 및 메인 페이지 접속...")
    edge_options = Options()
    edge_options.add_argument("--headless")
    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0")
    
    service = Service(EdgeChromiumDriverManager().install())
    driver = webdriver.Edge(service=service, options=edge_options)
    
    driver.get(TARGET_URL)
    # 기존 time.sleep(5) 대신 스크롤 로직으로 대체
    
    # ======================== [수정된 부분 시작] ========================

    # [변경] 페이지의 모든 이미지를 로드하기 위해 맨 아래까지 스크롤합니다.
    print("2. 페이지의 모든 이미지를 로드하기 위해 맨 아래까지 스크롤합니다...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        # 맨 아래로 스크롤
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # 스크롤 후 새 이미지가 로드될 시간 대기
        time.sleep(2)
        # 새 높이를 계산하고 이전 높이와 비교
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    print("-> 스크롤 완료.")

    # ========================= [수정된 부분 끝] =========================

    print("3. 1차 필터링 시작...")
    initial_soup = BeautifulSoup(driver.page_source, 'html.parser')
    webtoon_items = initial_soup.select('div#toonbook_list div[id^="toon_"]')
    
    # ... (이후 1차 필터링 및 다운로드 로직은 이전과 동일) ...
    
    session_for_images = requests.Session()
    ua = driver.execute_script("return navigator.userAgent;")
    session_for_images.headers.update({"User-Agent": ua, "Referer": TARGET_URL})
    for cookie in driver.get_cookies():
        session_for_images.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])

    candidate_items = []
    for item in webtoon_items:
        p_tags = item.select(".card-body p")
        episode_text = ''
        for p_tag in p_tags:
            if '화' in p_tag.get_text(strip=True):
                episode_text = p_tag.get_text(strip=True)
                break
        episode_num = extract_episode_count(episode_text)
        if (episode_num >= 100) or ('시즌' in episode_text):
            candidate_items.append(item)
    
    driver.quit()
    print(f"-> {len(candidate_items)}개의 후보 웹툰을 찾았습니다. 이미지 다운로드를 시작합니다.")

    for idx, item in enumerate(candidate_items):
        try:
            webtoon_id = int(item['id'].replace('toon_', ''))
            title = item.find('a', class_='toon-link').get('title', '제목 없음').strip()
            
            img_tag = item.select_one('img')
            thumbnail_url = None
            if img_tag and 'data-src' in img_tag.attrs:
                thumbnail_url = img_tag['data-src']
            elif img_tag and 'src' in img_tag.attrs:
                thumbnail_url = img_tag['src']

            if not thumbnail_url: continue

            if thumbnail_url.startswith('/'):
                thumbnail_url = TARGET_URL + thumbnail_url
            
            filename = f"{webtoon_id}{os.path.splitext(thumbnail_url)[1].split('?')[0] or '.jpg'}"
            save_path = os.path.join(SAVE_DIR, filename)

            if not os.path.exists(save_path):
                print(f"   ({idx+1}/{len(candidate_items)}) '{title}' 이미지 다운로드 중...")
                img_response = session_for_images.get(thumbnail_url, stream=True, timeout=10)
                if img_response.status_code == 200:
                    with open(save_path, 'wb') as f:
                        for chunk in img_response.iter_content(1024): f.write(chunk)
                else:
                    print(f"   -> 다운로드 실패 (상태 코드: {img_response.status_code})")
            else:
                print(f"   ({idx+1}/{len(candidate_items)}) '{title}' 이미지는 이미 존재합니다.")
        except Exception as e:
            print(f"처리 중 오류 발생: {e}")
            
    print(f"\n작업 완료! {SAVE_DIR} 폴더를 확인해주세요.")

if __name__ == '__main__':
    download_candidate_images()
