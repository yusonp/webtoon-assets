# sync_ignore_list.py

import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
import os

# --- 설정 부분 ---
script_dir = os.path.dirname(os.path.abspath(__file__))
CREDS_FILE = os.path.join(script_dir, 'credentials.json')
# 데이터를 저장할 로컬 JSON 파일
JSON_FILE = os.path.join(script_dir, 'exclude_list.json')

# 구글 스프레드시트 정보
SPREADSHEET_NAME = 'Webtoons' # 실제 스프레드시트 이름을 입력하세요.
IGNORE_SHEET_NAME = '제외목록'    # 제외 목록이 있는 시트 이름

def sync_ignore_list_from_sheet():
    """'Ignore' 시트의 내용을 로컬 exclude_list.json 파일로 저장합니다."""
    try:
        print("1. 구글 시트 인증을 시작합니다...")
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, scope)
        gc = gspread.authorize(creds)
        print("-> 인증 성공!")

        print(f"2. '{SPREADSHEET_NAME}' 스프레드시트의 '{IGNORE_SHEET_NAME}' 시트를 엽니다...")
        sh = gc.open(SPREADSHEET_NAME)
        worksheet = sh.worksheet(IGNORE_SHEET_NAME)
        print("-> 시트 열기 성공!")

        print("3. 제외 목록 데이터를 가져옵니다...")
        # A열의 모든 데이터를 리스트로 가져옴
        raw_list = worksheet.col_values(1)
        # 빈 셀은 제외하고 깔끔한 리스트로 만듦
        exclude_list = [title for title in raw_list if title]
        print(f"-> 총 {len(exclude_list)}개의 제외 항목을 찾았습니다.")

        print(f"4. '{JSON_FILE}' 파일에 저장합니다...")
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(exclude_list, f, ensure_ascii=False, indent=2)
        print("-> 저장 완료!")

        print(f"\n[성공] '{IGNORE_SHEET_NAME}' 시트의 내용이 '{JSON_FILE}'에 동기화되었습니다.")

    except FileNotFoundError as e:
        print(f"[오류] 파일을 찾을 수 없습니다: {e.filename}")
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"[오류] '{SPREADSHEET_NAME}' 스프레드시트를 찾을 수 없습니다.")
    except gspread.exceptions.WorksheetNotFound:
        print(f"[오류] '{IGNORE_SHEET_NAME}' 시트를 찾을 수 없습니다.")
    except Exception as e:
        print(f"알 수 없는 오류가 발생했습니다: {e}")

if __name__ == '__main__':
    sync_ignore_list_from_sheet()
