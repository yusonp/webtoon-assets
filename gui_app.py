import tkinter as tk
from tkinter import scrolledtext
import subprocess
import threading

def run_script(script_name, log_widget):
    def target():
        log_widget.insert(tk.END, f"'{script_name}' 실행 중...\n")
        log_widget.see(tk.END)
        try:
            # 외부 스크립트 실행 및 표준 출력/에러 캡처
            result = subprocess.run(
                ["python", script_name],
                capture_output=True,
                text=True,
                check=True,
                encoding='utf-8' # 인코딩 명시
            )
            log_widget.insert(tk.END, f"--- '{script_name}' 결과 ---\n")
            log_widget.insert(tk.END, result.stdout)
            if result.stderr:
                log_widget.insert(tk.END, f"--- '{script_name}' 에러 ---\n")
                log_widget.insert(tk.END, result.stderr)
            log_widget.insert(tk.END, f"'{script_name}' 실행 완료.\n\n")
        except subprocess.CalledProcessError as e:
            log_widget.insert(tk.END, f"--- '{script_name}' 실행 에러 ---\n")
            log_widget.insert(tk.END, f"Return Code: {e.returncode}\n")
            log_widget.insert(tk.END, f"Output: {e.stdout}\n")
            log_widget.insert(tk.END, f"Error: {e.stderr}\n\n")
        except FileNotFoundError:
            log_widget.insert(tk.END, f"오류: '{script_name}' 파일을 찾을 수 없습니다.\n\n")
        except Exception as e:
            log_widget.insert(tk.END, f"예상치 못한 오류 발생: {e}\n\n")
        log_widget.see(tk.END)

    # 스레드를 사용하여 GUI가 멈추지 않도록 함
    thread = threading.Thread(target=target)
    thread.daemon = True # 메인 프로그램 종료 시 스레드도 종료
    thread.start()

def create_gui():
    root = tk.Tk()
    root.title("스크립트 실행 도구")

    # 버튼 프레임
    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)

    # 로그 화면
    log_text = scrolledtext.ScrolledText(root, width=80, height=20, wrap=tk.WORD)
    log_text.pack(padx=10, pady=10)

    # 버튼 정의 (실행할 파이썬 파일명으로 교체하세요)
    scripts = [
        ("제외목록 갱신", "sync_ignore_list.py"),
        ("다운로드", "downloadv3.py"),
        ("구글시트 업데이트", "update_sheet.py"),
        ("깃허브 동기화", "github_sync.py")
    ]

    for text, script_name in scripts:
        button = tk.Button(button_frame, text=text,
                           command=lambda s=script_name: run_script(s, log_text))
        button.pack(side=tk.LEFT, padx=5)

    root.mainloop()

if __name__ == "__main__":
    create_gui()