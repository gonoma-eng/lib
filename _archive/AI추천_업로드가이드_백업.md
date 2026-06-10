# AI 추천 일러스트 — 사용자 직접 업로드 가이드

## 📂 저장 위치

```
D:\AI\lexia.safeg\위험성평가 Lexia 표준 템플릿 코드 정규화\SAFEG-lexia\rag_data\image_library_v2\images\_ai_recommended\
```

이 폴더에 아래 파일명 규칙으로 PNG/JPG 이미지 저장하시면 자동 적용됩니다.

## 📋 페어별 권장 검색 키워드 + 파일명

| 페어 | 의미 | 권장 검색 키워드 | 저장 파일명 |
|---|---|---|---|
| PAIR-0010 | 백호우 작업 + 2인 1조 + 신호수 | "굴삭기 신호수", "construction signal worker" | `AI-PAIR-0010.png` |
| PAIR-0011 | 식당 미끄럼 + 논슬립 + 안전장화 | "미끄럼방지 테이프", "wet floor sign safety" | `AI-PAIR-0011.png` |
| PAIR-0012 | 조속기 방호덮개 + 제거금지 표지 | "방호덮개 안전표지", "machine guard warning" | `AI-PAIR-0012.png` |
| PAIR-0013 | 옥상 유기용제 MSDS | "MSDS 안전보건자료", "chemical safety data" | `AI-PAIR-0013.png` |
| PAIR-0014 | 핸드그라인더 방호덮개 + PPE | "그라인더 안전모", "angle grinder PPE" | `AI-PAIR-0014.png` |
| PAIR-0015 | V-벨트 동력전달부 방호울 | "벨트 방호울", "V-belt safety guard" | `AI-PAIR-0015.png` |
| PAIR-0016 | 옥상 안전난간 + 안전대 | "옥상 안전난간", "rooftop guardrail" | `AI-PAIR-0016.png` |
| PAIR-0017 | 자재창고 안전표기 + MSDS | "화학 창고 라벨", "chemical warehouse label" | `AI-PAIR-0017.png` |
| PAIR-0018 | 개구부 덮개 + 안전표지 | "개구부 덮개", "floor hole cover safety" | `AI-PAIR-0018.png` |
| PAIR-0019 | 청소 세제 MSDS + 보호구 | "청소 보호장갑 MSDS", "cleaning chemical PPE" | `AI-PAIR-0019.png` |

## 🔒 추천 사이트 (저작권 안전)

### 1. KOSHA 한국산업안전보건공단 ⭐ 가장 권장
- URL: https://www.kosha.or.kr → 안전보건자료실
- 라이센스: KOGL Type-1 (공공저작물 - 출처표시 필수)
- 한국형 안전보건 일러스트가 가장 풍부

### 2. Pixabay
- URL: https://pixabay.com
- 라이센스: Pixabay License (출처표시 권장)
- 상업 사용 가능

### 3. Pexels
- URL: https://www.pexels.com  
- 라이센스: Pexels License (출처표시 없이도 가능)
- 상업 사용 가능

## ⚙ 자동 매핑 실행

이미지 파일을 폴더에 저장한 후, 다음 중 하나로 자동 매핑:

### 방법 A: Python 스크립트 실행
```bash
cd "D:\AI\lexia.safeg\위험성평가 Lexia 표준 템플릿 코드 정규화\SAFEG-lexia\rag_data\image_library_v2"
python _scripts/_apply_user_images.py
```

### 방법 B: 저에게 요청
"AI 추천 이미지 매핑 갱신해주세요"라고 말씀하시면 자동 실행해드립니다.

## ✅ 확인 방법

1. 브라우저에서 `index.html` 새로고침
2. 강릉시 페어 클릭 → 라이트박스
3. **✦ AI 추천** 탭 클릭
4. 업로드하신 이미지 표시 확인

## ⚠ 주의사항

- 파일명 정확히 입력 (대소문자, 하이픈 위치)
- 권장 사이즈: 1280×960 또는 비슷한 비율 (16:12)
- 파일 형식: PNG, JPG, JPEG, WebP (자동 인식)
- 모든 페어를 한 번에 업로드 안 해도 됩니다 (1건씩 점진적 가능)
