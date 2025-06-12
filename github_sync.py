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

def sync_to_github():
    """로컬 Git 저장소의 변경사항을 원격 저장소(GitHub)와 동기화합니다."""
    try:
        # 1. Git 저장소 열기
        repo = git.Repo(REPO_PATH)
        print(f"Git 저장소를 열었습니다: {REPO_PATH}")

        # 2. 원격 저장소의 변경사항을 먼저 받아옵니다 (git pull)
        # 충돌을 방지하기 위한 중요한 단계입니다.
        origin = repo.remote(name=REMOTE_NAME)
        print(f"원격 저장소({REMOTE_NAME})의 변경사항을 pull 합니다...")
        origin.pull()
        print("-> pull 완료.")

        # 3. 새로 추가/변경된 모든 파일을 추가합니다 (git add .)
        # Untracked 파일(새 이미지)을 포함한 모든 변경사항을 스테이징합니다.
        print("새로 추가/변경된 파일을 git add 합니다...")
        repo.git.add(A=True)
        print("-> add 완료.")

        # 4. 변경사항이 있을 때만 커밋을 진행합니다.
        if repo.is_dirty(untracked_files=True):
            print("변경사항을 커밋합니다...")
            repo.index.commit(COMMIT_MESSAGE)
            print(f"-> 커밋 완료: {COMMIT_MESSAGE}")
        else:
            print("새롭게 커밋할 변경사항이 없습니다.")
            return # 변경 없으면 종료

        # 5. 원격 저장소로 푸시합니다 (git push)
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