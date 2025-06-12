# downloader.py (최종 개선판)

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
    """텍스트에서 마지막 숫자를 추출하여 정수로 반환합니다."""
    if not text:
        return 0
    numbers = re.findall(r'\d+', text)
    if numbers:
        return int(numbers[-1])
    return 0

def run_downloader():
    """웹툰 크롤러 메인 함수"""
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
        
        # --- [설정] 프록시 서버 (필요시 주소 입력) ---
        # PROXY = "203.243.63.16:80" # 예: "123.45.67.89:8080"
        
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0'
        ]
        
        edge_options = Options()
        # edge_options.add_argument(f'--proxy-server={PROXY}') # 프록시 사용 시 이 줄의 주석(#)을 제거하세요.
        edge_options.add_argument(f"user-agent={random.choice(user_agents)}")
        
        # --- [설정] 헤드리스 모드 (백그라운드 실행) ---
        # 디버깅 시에는 아래 줄을 주석(#) 처리하여 브라우저 창을 직접 보세요.
        edge_options.add_argument("--headless")
        
        edge_options.add_argument("--no-sandbox")
        edge_options.add_argument("--disable-dev-shm-usage")
        edge_options.add_argument("--disable-gpu")

        service = Service(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service=service, options=edge_options)
        
        # 3. 메인 페이지 접속 및 목록 로딩 대기
        print(f"메인 페이지({TARGET_URL})에 접속합니다...")
        driver.get(TARGET_URL)
        
        try:
            print("웹툰 목록 컨테이너가 나타날 때까지 최대 20초 대기합니다...")
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "toonbook_list"))
            )
            print("컨테이너 로딩 완료.")
        except Exception:
            print("오류: 지정된 시간 내에 웹툰 목록 컨테이너를 찾지 못했습니다.")
            print("HTML 구조가 변경되었거나 페이지 로드에 실패했을 수 있습니다. 'error.png' 파일을 확인하세요.")
            driver.save_screenshot('error.png')
            driver.quit()
            return

        initial_soup = BeautifulSoup(driver.page_source, 'html.parser')
        webtoon_items = initial_soup.select('div#toonbook_list div[id^="toon_"]')
        
        if not webtoon_items:
            print("[오류] 개별 웹툰 아이템을 찾지 못했습니다.")
            driver.quit()
            return
            
        # 4. 1차 필터링 (효율적인 후보 선정)
        print(f"총 {len(webtoon_items)}개 웹툰 발견. 100화 이상 또는 '시즌' 포함 웹툰을 기준으로 1차 필터링을 시작합니다...")
        
        candidate_items = []
        for item in webtoon_items:
            # .card-body 안의 모든 p 태그를 리스트로 가져옴
            p_tags = item.select(".card-body p")
            
            episode_text = ''
            # 모든 p 태그를 순회하며 '화'가 포함된 텍스트를 찾음
            for p_tag in p_tags:
                if '화' in p_tag.get_text(strip=True):
                    episode_text = p_tag.get_text(strip=True)
                    break # 찾았으면 반복 중단
            
            episode_num = extract_episode_count(episode_text)
            
            if (episode_num >= 100) or ('시즌' in episode_text):
                candidate_items.append(item)
        
        print(f"-> {len(candidate_items)}개의 후보 웹툰을 찾았습니다.")
        
        # 5. 상세 정보 수집 (2차 필터링)
        print("\n후보 웹툰들의 상세 페이지를 방문하여 최종 정보를 수집합니다.")
        newly_added_list = []
        session_for_images = requests.Session()

        for idx, item in enumerate(candidate_items):
            try:
                webtoon_id = int(item['id'].replace('toon_', ''))
                
                if webtoon_id in existing_ids:
                    continue

                title = item.find('a', class_='toon-link').get('title', '제목 없음').strip()
                detail_page_url = TARGET_URL + item.find('a', class_='toon-link')['href']
                
                print(f"   ({idx+1}/{len(candidate_items)}) '{title}' 확인 중...")
                
                driver.get(detail_page_url)
                time.sleep(random.uniform(0.5, 1.5)) # 불규칙한 대기
                detail_soup = BeautifulSoup(driver.page_source, 'html.parser')

                count_span = detail_soup.find('span', id='count_list')
                episodes = int(count_span.get_text(strip=True)) if count_span else 0
                
                if episodes >= 100:
                    print(f"   -> {episodes}화 확인. 신규 웹툰으로 추가합니다.")
                    
                    header_div = detail_soup.find('div', class_='card-fluid')
                    img_tag = header_div.find('img') if header_div else None
                    thumbnail_url = img_tag['src'] if img_tag and img_tag.has_attr('src') else None
                    if not thumbnail_url: continue

                    filename = f"{webtoon_id}{os.path.splitext(thumbnail_url)[1] or '.jpg'}"
                    save_path = os.path.join('static', 'images', filename)
                    
                    if not os.path.exists(save_path):
                        img_response = session_for_images.get(thumbnail_url, headers={'Referer': TARGET_URL}, stream=True, timeout=10)
                        if img_response.status_code == 200:
                            os.makedirs(os.path.dirname(save_path), exist_ok=True)
                            with open(save_path, 'wb') as f:
                                for chunk in img_response.iter_content(1024): f.write(chunk)
                    
                    newly_added_list.append({
                        'id': webtoon_id,
                        'title': title,
                        'author': item.find('p', class_='text-muted mt-1').find('span').get_text(strip=True) if item.find('p', class_='text-muted mt-1') else '작가 미상',
                        'episodes': episodes,
                        'thumbnail': f"/static/images/{filename}",
                        'url': detail_page_url
                    })
            except Exception as e:
                print(f"   ID {item.get('id')} 처리 중 오류: {e}")
        
        # 6. 최종 데이터 저장
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
