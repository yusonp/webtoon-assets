# downloader.py (모든 기능 통합 최종판)

import os
import requests
import re
import json
import time
import random

from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from bs4 import BeautifulSoup

def extract_episode_count(text):
    if not text: return 0
    numbers = re.findall(r'\d+', text)
    return int(numbers[-1]) if numbers else 0

def run_downloader():
    TARGET_URL = 'https://blacktoon373.com'

    # 1. 기존 데이터 로드
    try:
        with open('webtoons.json', 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = []
    
    existing_ids = {item['id'] for item in existing_data}
    print(f"기존에 저장된 웹툰 {len(existing_ids)}개를 불러왔습니다.")

    try:
        # 2. Selenium 드라이버 설정
        print("Selenium Edge 드라이버를 설정합니다...")
        edge_options = Options()
        edge_options.add_argument("--headless")
        edge_options.add_argument("--no-sandbox")
        edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0")
        
        service = Service(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service=service, options=edge_options)
        
        # 3. 메인 페이지 접속 및 Lazy Loading 해결을 위한 스크롤
        print(f"메인 페이지({TARGET_URL})에 접속합니다...")
        driver.get(TARGET_URL)
        
        print("페이지의 모든 이미지를 로드하기 위해 맨 아래까지 스크롤합니다...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height: break
            last_height = new_height
        print("-> 스크롤 완료.")

        # 4. 이미지 다운로드를 위한 세션 동기화 (User-Agent, 쿠키 복사)
        print("드라이버의 세션 정보를 이미지 다운로더에 복사합니다...")
        session_for_images = requests.Session()
        ua = driver.execute_script("return navigator.userAgent;")
        session_for_images.headers.update({"User-Agent": ua, "Referer": TARGET_URL})
        for cookie in driver.get_cookies():
            session_for_images.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])
        print("-> 세션 정보 복사 완료.")

        # 5. 1차 필터링
        print("1차 필터링을 시작합니다...")
        initial_soup = BeautifulSoup(driver.page_source, 'html.parser')
        webtoon_items = initial_soup.select('div#toonbook_list div[id^="toon_"]')
        
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
        print(f"-> {len(candidate_items)}개의 후보 웹툰을 찾았습니다.")
        
        # 6. 상세 정보 수집 및 최종 필터링
        print("\n후보 웹툰들의 상세 페이지를 방문하여 최종 정보를 수집합니다.")
        newly_added_list = []

        for idx, item in enumerate(candidate_items):
            try:
                webtoon_id = int(item['id'].replace('toon_', ''))
                
                # [디버깅 시] 이 부분을 잠시 주석처리 하세요.
                if webtoon_id in existing_ids:
                    continue

                title = item.find('a', class_='toon-link').get('title', '제목 없음').strip()
                detail_page_url = TARGET_URL + item.find('a', class_='toon-link')['href']
                print(f"   ({idx+1}/{len(candidate_items)}) '{title}' 확인 중...")
                
                driver.get(detail_page_url)
                time.sleep(random.uniform(0.5, 1.5))
                detail_soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                # [수정 확인 필요] 아래 코드가 상세페이지 회차를 제대로 가져오는지 확인해야 합니다.
                count_span = detail_soup.find('span', id='count_list')
                episodes = int(count_span.get_text(strip=True)) if count_span else 0
                print(f"      -> [디버깅] 상세 페이지에서 확인된 회차: {episodes}화") # 디버깅용 로그

                if episodes >= 100:
                    print(f"   -> {episodes}화 확인. 신규 웹툰으로 추가합니다.")
                    
                    # [통합된 이미지 처리 로직]
                    header_div = detail_soup.find('div', class_='card-fluid')
                    img_tag = header_div.find('img') if header_div else None
                    thumbnail_url = img_tag.get('data-src') or img_tag.get('src') if img_tag else None

                    if thumbnail_url and thumbnail_url.startswith('/'):
                        thumbnail_url = TARGET_URL + thumbnail_url

                    if thumbnail_url:
                        filename = f"{webtoon_id}{os.path.splitext(thumbnail_url)[1].split('?')[0] or '.jpg'}"
                        save_path = os.path.join('static', 'images', filename)
                        
                        if not os.path.exists(save_path):
                            img_response = session_for_images.get(thumbnail_url, stream=True, timeout=15)
                            if img_response.status_code == 200:
                                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                                with open(save_path, 'wb') as f:
                                    for chunk in img_response.iter_content(1024): f.write(chunk)
                                print(f"      -> 이미지 저장 성공: {save_path}")
                            else:
                                print(f"      -> 이미지 다운로드 실패 (상태 코드: {img_response.status_code})")
                        
                        newly_added_list.append({
                            'id': webtoon_id, 'title': title,
                            'author': item.find('p', class_='text-muted mt-1').find('span').get_text(strip=True) if item.find('p', class_='text-muted mt-1') else '작가 미상',
                            'episodes': episodes, 'thumbnail': f"https://cdn.jsdelivr.net/gh/yusonp/webtoon-assets/{filename}",
                            'url': detail_page_url
                        })
            except Exception as e:
                print(f"   ID {item.get('id')} 처리 중 오류: {e}")
        
        # 7. 최종 데이터 저장
        print("\n최종 데이터 병합, 정렬 및 JSON 파일 저장...")
        final_webtoon_list = existing_data + newly_added_list
        final_webtoon_list.sort(key=lambda x: x['episodes'], reverse=True)

        with open('webtoons.json', 'w', encoding='utf-8') as f:
            json.dump(final_webtoon_list, f, ensure_ascii=False, indent=4)
            
        print(f"\n작업 완료! {len(newly_added_list)}개의 새로운 웹툰을 추가하여 총 {len(final_webtoon_list)}개 데이터를 'webtoons.json' 파일에 저장했습니다.")

    except Exception as e:
        print(f"전체 작업 중 치명적인 오류 발생: {e}")
    finally:
        if 'driver' in locals() and driver:
            driver.quit()
            print("드라이버를 종료했습니다.")

if __name__ == '__main__':
    run_downloader()
