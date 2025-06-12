# redownloader.py

import os
import requests
import json
import time
import random

from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from bs4 import BeautifulSoup

def redownload_missing_images():
    TARGET_URL = 'https://blacktoon373.com'
    JSON_FILE = 'webtoons.json'

    # 1. JSON 파일 로드 및 누락된 이미지 목록 생성
    print(f"1. '{JSON_FILE}' 파일을 읽어 누락된 이미지를 찾습니다...")
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            all_webtoons = json.load(f)
    except FileNotFoundError:
        print(f"[오류] '{JSON_FILE}' 파일이 없습니다. 먼저 downloader.py를 실행하세요.")
        return

    missing_items = []
    for entry in all_webtoons:
        # json에 기록된 상대 경로를 로컬 파일 시스템 경로로 변환
        # 예: "/static/images/123.jpg" -> "static\images\123.jpg" (Windows 기준)
        local_path = os.path.join(*entry['thumbnail'].strip('/').split('/'))
        
        if not os.path.exists(local_path):
            missing_items.append(entry)

    if not missing_items:
        print("-> 모든 이미지가 이미 존재합니다. 작업을 종료합니다.")
        return

    print(f"-> 총 {len(missing_items)}개의 이미지가 누락되었습니다. 다운로드를 시작합니다.")

    # 2. 누락된 이미지가 있을 경우에만 드라이버 실행
    driver = None
    try:
        print("\n2. Selenium 드라이버를 설정합니다...")
        edge_options = Options()
        edge_options.add_argument("--headless")
        edge_options.add_argument("--no-sandbox")
        edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0")
        
        service = Service(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service=service, options=edge_options)
        
        # 3. 세션 동기화 (403 오류 방지)
        print("3. 사이트에 접속하여 세션 정보를 동기화합니다...")
        driver.get(TARGET_URL)
        time.sleep(3) # 사이트 접속 및 쿠키 생성을 위한 대기

        session_for_images = requests.Session()
        ua = driver.execute_script("return navigator.userAgent;")
        session_for_images.headers.update({"User-Agent": ua, "Referer": TARGET_URL})
        for cookie in driver.get_cookies():
            session_for_images.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])
        print("-> 세션 정보 동기화 완료.")

        # 4. 누락된 이미지 다운로드 시작
        print("\n4. 누락된 이미지의 상세 페이지를 방문하여 다운로드를 시작합니다.")
        for idx, item in enumerate(missing_items):
            try:
                print(f"   ({idx+1}/{len(missing_items)}) '{item['title']}' 이미지 재다운로드 중...")
                
                # 상세 페이지 방문
                driver.get(item['url'])
                time.sleep(random.uniform(0.5, 1.5))
                detail_soup = BeautifulSoup(driver.page_source, 'html.parser')

                # 상세 페이지에서 이미지 주소 다시 추출
                header_div = detail_soup.find('div', class_='card-fluid')
                img_tag = header_div.find('img') if header_div else None
                thumbnail_url = img_tag.get('data-src') or img_tag.get('src') if img_tag else None

                if not thumbnail_url:
                    print("      -> 썸네일 URL을 찾지 못해 건너뜁니다.")
                    continue
                
                if thumbnail_url.startswith('/'):
                    thumbnail_url = TARGET_URL + thumbnail_url
                
                save_path = os.path.join(*item['thumbnail'].strip('/').split('/'))
                
                # 이미지 다운로드
                img_response = session_for_images.get(thumbnail_url, stream=True, timeout=15)
                if img_response.status_code == 200:
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    with open(save_path, 'wb') as f:
                        for chunk in img_response.iter_content(1024):
                            f.write(chunk)
                    print(f"      -> 저장 성공: {save_path}")
                else:
                    print(f"      -> 다운로드 실패 (상태 코드: {img_response.status_code})")

            except Exception as e:
                print(f"   -> 처리 중 오류 발생: {e}")

    except Exception as e:
        print(f"전체 작업 중 오류 발생: {e}")
    finally:
        if driver:
            driver.quit()
            print("\n드라이버를 종료했습니다.")
        print("모든 작업을 완료했습니다.")


if __name__ == '__main__':
    redownload_missing_images()