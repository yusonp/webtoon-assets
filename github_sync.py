# github_sync.py

import git
from datetime import datetime

# --- 설정 ---
# Git 저장소의 로컬 경로 (현재 폴더이므로 '.' 사용)
REPO_PATH = '.'
# 커밋 메시지 (날짜와 시간을 포함하여 자동으로 생성)
COMMIT_MESSAGE = f" chore: Update webtoon images - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
# 원격 저장소 이름 (보통 'origin')
REMOTE_NAME = 'origin'

# sync_to_github 함수를 아래 내용으로 교체해주세요.

def sync_to_github():
    """로컬 Git 저장소의 변경사항을 원격 저장소(GitHub)와 동기화합니다."""
    try:
        repo = git.Repo(REPO_PATH)
        origin = repo.remote(name=REMOTE_NAME)
        print(f"Git 저장소를 열었습니다: {REPO_PATH}")

        # [변경] 1. 로컬 변경사항을 먼저 add/commit 합니다.
        print("새로 추가/변경된 파일을 git add 합니다...")
        repo.git.add(A=True)
        print("-> add 완료.")
        
        commit_made = False
        if repo.is_dirty(untracked_files=True):
            print("변경사항을 커밋합니다...")
            repo.index.commit(COMMIT_MESSAGE)
            print(f"-> 커밋 완료: {COMMIT_MESSAGE}")
            commit_made = True
        else:
            print("새롭게 커밋할 로컬 변경사항이 없습니다.")
            
        # [변경] 2. 그 다음 pull을 실행하여 원격 변경사항과 병합합니다.
        print(f"원격 저장소({REMOTE_NAME})의 변경사항을 pull 합니다...")
        # --rebase 옵션은 로컬 커밋을 원격 변경사항 위로 재배치하여 히스토리를 깔끔하게 유지합니다.
        origin.pull(rebase=True)
        print("-> pull 완료.")

        # [변경] 3. 로컬에서 커밋을 했거나, 원격에서 변경사항을 받아온 경우 push를 실행합니다.
        print(f"원격 저장소({REMOTE_NAME})으로 push 합니다...")
        origin.push()
        print("-> push 완료!")

        print("\n[성공] GitHub 저장소와 동기화되었습니다.")

    except git.exc.InvalidGitRepositoryError:
        print(f"[오류] '{REPO_PATH}'는 Git 저장소가 아닙니다. 경로를 확인하세요.")
    except git.exc.GitCommandError as e:
        print(f"[Git 오류] Git 명령어 실행 중 오류가 발생했습니다: \n{e}")
    except Exception as e:
        print(f"알 수 없는 오류가 발생했습니다: {e}")

if __name__ == '__main__':
    sync_to_github()