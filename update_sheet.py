# update_sheet.py (퍼센트 인코딩 방지 수정)

import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import os
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

# --- 설정 부분 ---
script_dir = os.path.dirname(os.path.abspath(__file__))
CREDS_FILE = os.path.join(script_dir, 'credentials.json')
JSON_FILE = os.path.join(script_dir, 'webtoons.json')
SPREADSHEET_NAME = 'Webtoons' # 실제 스프레드시트 이름으로 수정하세요.


def update_google_sheet():
    """webtoons.json 파일의 내용을 구글 스프레드시트로 업데이트합니다."""
    try:
        print("1. 구글 시트 인증을 시작합니다...")
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, scope)
        gc = gspread.authorize(creds)
        print("-> 인증 성공!")

        print(f"2. '{SPREADSHEET_NAME}' 스프레드시트를 엽니다...")
        sh = gc.open(SPREADSHEET_NAME) 
        worksheet = sh.get_worksheet(0)
        print("-> 시트 열기 성공!")

        print(f"3. '{JSON_FILE}' 파일을 읽어옵니다...")
        df = pd.read_json(JSON_FILE)
        
        if df.empty:
            print("-> JSON 파일에 데이터가 없습니다. 시트를 비우고 종료합니다.")
            worksheet.clear()
            return
            
        data_to_upload = [df.columns.values.tolist()] + df.values.tolist()
        print("-> 데이터 변환 완료!")
        
        print("4. 시트의 모든 내용을 지우고 새 데이터로 업데이트합니다...")
        worksheet.clear()
        
        # [수정된 부분] value_input_option을 'RAW'로 변경
        worksheet.update(range_name='A1', values=data_to_upload, value_input_option='RAW')
        
        print("-> 업데이트 완료!")

        print(f"\n작업 성공! 총 {len(df)}개의 웹툰 데이터가 '{SPREADSHEET_NAME}' 시트에 업데이트되었습니다.")
        
    except FileNotFoundError as e:
        print(f"[오류] 파일을 찾을 수 없습니다: {e.filename}")
        print("   -> 파일 이름과 경로가 정확한지 확인하세요.")
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"[오류] '{SPREADSHEET_NAME}' 스프레드시트를 찾을 수 없습니다.")
        print("   1. 파일 이름을 정확히 입력했는지 확인하세요.")
        print(f"   2. 서비스 계정 이메일에 해당 시트를 '편집자'로 공유했는지 확인하세요.")
    except Exception as e:
        print(f"알 수 없는 오류가 발생했습니다: {e}")

if __name__ == '__main__':
    update_google_sheet()