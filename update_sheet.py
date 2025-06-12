# update_sheet.py

import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

# --- 설정 부분 ---
# 1. 구글 인증 JSON 파일 경로
CREDS_FILE = 'credentials.json' 
# 2. 연동할 구글 스프레드시트 이름
SPREADSHEET_NAME = '나의 웹툰 목록' # 실제 스프레드시트 이름을 입력하세요.
# 3. 크롤링 데이터가 담긴 JSON 파일
JSON_FILE = 'webtoons.json'

def update_google_sheet():
    """webtoons.json 파일의 내용을 구글 스프레드시트로 업데이트합니다."""
    try:
        print("1. 구글 시트 인증을 시작합니다...")
        # API 접근 권한 범위 설정
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, scope)
        gc = gspread.authorize(creds)
        print("-> 인증 성공!")

        print(f"2. '{SPREADSHEET_NAME}' 스프레드시트를 엽니다...")
        # 이름으로 스프레드시트 열기
        sh = gc.open(SPREADSHEET_NAME) 
        # 첫 번째 워크시트 선택
        worksheet = sh.get_worksheet(0)
        print("-> 시트 열기 성공!")

        print(f"3. '{JSON_FILE}' 파일을 읽어옵니다...")
        # pandas를 사용하여 json 파일을 DataFrame으로 변환
        df = pd.read_json(JSON_FILE)
        
        # DataFrame 헤더(id, title 등)와 데이터를 리스트 형태로 변환
        # [[헤더1, 헤더2], [값1, 값2], [값3, 값4], ...]
        data_to_upload = [df.columns.values.tolist()] + df.values.tolist()
        print("-> 데이터 변환 완료!")
        
        print("4. 시트의 모든 내용을 지우고 새 데이터로 업데이트합니다...")
        worksheet.clear() # 기존 내용 모두 삭제
        worksheet.update('A1', data_to_upload, value_input_option='USER_ENTERED')
        print("-> 업데이트 완료!")

        print(f"\n작업 성공! 총 {len(df)}개의 웹툰 데이터가 '{SPREADSHEET_NAME}' 시트에 업데이트되었습니다.")
        
    except FileNotFoundError:
        print(f"[오류] '{CREDS_FILE}' 또는 '{JSON_FILE}' 파일을 찾을 수 없습니다. 경로를 확인하세요.")
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"[오류] '{SPREADSHEET_NAME}' 스프레드시트를 찾을 수 없습니다.")
        print("1. 파일 이름을 정확히 입력했는지 확인하세요.")
        print(f"2. 서비스 계정 이메일에 해당 시트를 '편집자'로 공유했는지 확인하세요.")
    except Exception as e:
        print(f"알 수 없는 오류가 발생했습니다: {e}")

if __name__ == '__main__':
    update_google_sheet()