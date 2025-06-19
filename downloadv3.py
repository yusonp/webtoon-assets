# downloader.py (제외 목록 기능 추가)

import os
import requests
import re
import json
import time
import random

from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from bs4 import BeautifulSoup

# (extract_episode_count 함수는 기존과 동일하게 유지)
def extract_episode_count(text):
    if not text: return 0
    numbers = re.findall(r'\d+', text)
    return int(numbers[-1]) if numbers else 0

def run_downloader():
    TARGET_URL = 'https://blacktoon374.com'

    # --- 기존 데이터 로드 ---
    try:
        with open('webtoons.json', 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = []
    
    existing_ids = {item['id'] for item in existing_data}
    print(f"기존에 저장된 웹툰 {len(existing_ids)}개를 불러왔습니다.")

    # ======================== [추가된 부분 시작] ========================
    # 제외 목록 로드
    try:
        with open('exclude_list.json', 'r', encoding='utf-8') as f:
            exclude_titles = set(json.load(f)) # 빠른 조회를 위해 set으로 변환
        print(f"제외 목록에 있는 {len(exclude_titles)}개의 웹툰을 불러왔습니다.")
    except (FileNotFoundError, json.JSONDecodeError):
        exclude_titles = set() # 파일이 없으면 빈 set으로 시작
        print("제외 목록 파일(exclude_list.json)이 없거나 비어있습니다.")
    # ========================= [추가된 부분 끝] =========================

    driver = None # 드라이버 객체를 미리 None으로 초기화
    try:
        # --- (드라이버 설정, 스크롤, 세션 동기화 로직은 기존과 동일) ---
        print("\nSelenium Edge 드라이버를 설정합니다...")
        edge_options = Options()
        edge_options.add_argument("--headless")
        edge_options.add_argument("--no-sandbox")
        edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0")
        service = Service(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service=service, options=edge_options) # 드라이버 객체 할당
        
        print(f"메인 페이지({TARGET_URL})에 접속 및 스크롤합니다...")
        driver.get(TARGET_URL)
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height: break
            last_height = new_height
        print("-> 스크롤 완료.")
        
        session_for_images = requests.Session()
        ua = driver.execute_script("return navigator.userAgent;")
        session_for_images.headers.update({"User-Agent": ua, "Referer": TARGET_URL})
        for cookie in driver.get_cookies():
            session_for_images.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])

        # --- (1차 필터링 로직은 기존과 동일) ---
        print("\n1차 필터링을 시작합니다...")
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
        
        # --- 상세 정보 수집 루프 ---
        print("\n후보 웹툰들의 상세 페이지를 방문하여 최종 정보를 수집합니다.")
        newly_added_list = []
        for idx, item in enumerate(candidate_items):
            try:
                webtoon_id = int(item['id'].replace('toon_', ''))
                title = item.find('a', class_='toon-link').get('title', '제목 없음').strip()

                # ======================== [추가된 부분 시작] ========================
                # 제외 목록 확인
                if title in exclude_titles:
                    print(f"   ({idx+1}/{len(candidate_items)}) '{title}'는 제외 목록에 있으므로 건너뜁니다.")
                    continue
                # ========================= [추가된 부분 끝] =========================

                # 기존 중복 확인
                if webtoon_id in existing_ids:
                    continue
                
                detail_page_url = TARGET_URL + item.find('a', class_='toon-link')['href']
                print(f"   ({idx+1}/{len(candidate_items)}) '{title}' 확인 중...")
                
                driver.get(detail_page_url)
                time.sleep(random.uniform(0.5, 1.5))
                detail_soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                count_span = detail_soup.find('span', id='count_list')
                episodes = int(count_span.get_text(strip=True)) if count_span else 0
                
                if episodes >= 100:
                    print(f"   -> {episodes}화 확인. 신규 웹툰으로 추가합니다.")
                    header_div = detail_soup.find('div', class_='card-fluid')
                    img_tag = header_div.find('img') if header_div else None
                    thumbnail_url = img_tag.get('data-src') or img_tag.get('src') if img_tag else None
                    if thumbnail_url and thumbnail_url.startswith('/'):
                        thumbnail_url = TARGET_URL + thumbnail_url
                    
                    if thumbnail_url:
                        filename = f"{webtoon_id}{os.path.splitext(thumbnail_url)[1].split('?')[0] or '.jpg'}"
                        save_path = os.path.join('static', 'images', filename)
                        
                        if not os.path.exists(save_path):
                            # *** 이 부분에 이미지 다운로드 로직이 들어가야 합니다. ***
                            try:
                                # static/images 디렉토리가 없으면 생성
                                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                                
                                # 이미지 다운로드
                                img_data = session_for_images.get(thumbnail_url).content
                                with open(save_path, 'wb') as handler:
                                    handler.write(img_data)
                                print(f"      썸네일 다운로드 완료: {save_path}")
                            except Exception as img_e:
                                print(f"      썸네일 다운로드 실패 ({thumbnail_url}): {img_e}")
                                save_path = None # 다운로드 실패 시 경로 None으로 설정
                    else:
                        save_path = None # 썸네일 URL이 없는 경우
                        
                    newly_added_list.append({
                        'id': webtoon_id,
                        'title': title,
                        'episodes': episodes,
                        'thumbnail': save_path, # 다운로드 성공 시 경로, 실패 시 None
                        'url': detail_page_url
                    })
            except Exception as e:
                print(f"   ID {item.get('id')} 처리 중 오류: {e}")
        
        # --- (최종 데이터 저장 로직) ---
        if newly_added_list:
            existing_data.extend(newly_added_list)
            try:
                with open('webtoons.json', 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, ensure_ascii=False, indent=4)
                print(f"\n총 {len(newly_added_list)}개의 신규 웹툰 정보가 webtoons.json에 추가되었습니다.")
            except Exception as e:
                print(f"webtoons.json 저장 중 오류 발생: {e}")
        else:
            print("\n새롭게 추가된 웹툰 정보가 없습니다.")


    except Exception as e:
        print(f"전체 작업 중 치명적인 오류 발생: {e}")
    finally:
        if driver: 
            driver.quit()
            print("드라이버를 종료했습니다.")

if __name__ == '__main__':
    run_downloader()
