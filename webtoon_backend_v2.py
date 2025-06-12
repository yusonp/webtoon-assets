# webtoon_backend.py

import os
import json
from flask import Flask, jsonify, render_template

app = Flask(__name__)

# 루트 경로: HTML 페이지 서비스
@app.route('/')
def index():
    return render_template('index.html')

# API 경로: 저장된 JSON 파일 서비스
@app.route('/api/webtoons')
def get_webtoons():
    try:
        # downloader.py가 생성한 webtoons.json 파일을 읽습니다.
        with open('webtoons.json', 'r', encoding='utf-8') as f:
            webtoons_data = json.load(f)
        
        return jsonify({
            'success': True,
            'data': webtoons_data,
            'total': len(webtoons_data)
        })
        
    except FileNotFoundError:
        return jsonify({
            'success': False,
            'error': "'webtoons.json' 파일을 찾을 수 없습니다. downloader.py를 먼저 실행해주세요."
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)