"""
사용자가 KOSHA/Pixabay/Pexels 등에서 다운로드한 이미지를
images/_ai_recommended/ 폴더에 저장하면 자동으로 매핑합니다.

파일명 규칙:
  AI-PAIR-0010.png  (또는 .jpg)
  AI-PAIR-0011.png
  ... 
  AI-PAIR-0019.png

저작권 안전 권장:
  ✅ KOSHA 안전보건자료실 (KOGL Type-1 출처표시 시 OK)
     - https://www.kosha.or.kr → 자료실 → 다운로드
  ✅ Pixabay (Pixabay License — CC0 유사, 상업사용 OK, 출처표시 권장)
     - https://pixabay.com
  ✅ Pexels (Pexels License — 무료, 상업사용 OK)
     - https://www.pexels.com
  ✅ Wikimedia Commons (CC0 / Public Domain 카테고리만)

  ⚠ Freepik 무료 라이센스는 출처표시 필수
  ❌ Google 이미지 검색 결과 직접 사용 금지 (저작권 위반 위험)
"""
import json, os, sys

FOLDER = 'images/_ai_recommended'
PAIRS = [f'PAIR-00{i}' for i in range(10, 20)]

with open('image_library_v2_paired.json','r',encoding='utf-8') as f:
    data = json.load(f)

# 폴더 스캔
existing = os.listdir(FOLDER) if os.path.isdir(FOLDER) else []

print('=== 사용자 업로드 이미지 자동 매핑 ===\n')
mapped = 0
for pid in PAIRS:
    # PNG → JPG → SVG 순으로 우선 적용
    for ext in ['png', 'jpg', 'jpeg', 'webp']:
        candidate = f'AI-{pid}.{ext}'
        if candidate in existing:
            new_path = f'{FOLDER}/{candidate}'
            for r in data['records']:
                if r['pair_id'] == pid:
                    old = r.get('ai_measure_photo','')
                    r['ai_measure_photo'] = new_path
                    print(f'✅ {pid}: {old.split("/")[-1]} → {candidate}')
                    mapped += 1
                    break
            break

if mapped == 0:
    print('업로드된 이미지 없음 — 현재 자체 SVG 그대로 유지')
else:
    with open('image_library_v2_paired.json','w',encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # HTML 재인라인
    import re
    inline = json.dumps(data['records'], ensure_ascii=False, separators=(',',':'))
    with open('index.html','r',encoding='utf-8') as f:
        html = f.read()
    html_new, _ = re.subn(r'const LIBRARY_DATA = \[.*?\];', f'const LIBRARY_DATA = {inline};', html, count=1, flags=re.DOTALL)
    with open('index.html','w',encoding='utf-8') as f:
        f.write(html_new)
    print(f'\n✅ {mapped}건 매핑 완료 + HTML 재인라인')

print('\n💡 출처 표시 필요 시 README.md 또는 갤러리 푸터에 명시 권장')
