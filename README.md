# SAFEG 감소대책 RAG 이미지 라이브러리 v2

위험성평가 보고서 24개 PDF에서 추출한 페어(유해위험요인 + 감소대책) 이미지·텍스트 RAG 데이터.

## 📂 폴더 구조

```
image_library_v2/
├── index.html                          ← 갤러리 (브라우저로 열기)
├── index2.html                         ← 리다이렉트 (→ index.html)
├── image_library_v2_paired.json        ← RAG 메타데이터 (405 페어)
├── README.md                           ← 이 파일
│
├── 📁 images/                          ← 회사별 이미지 24개 폴더 통합
│   ├── 강원대_2023/
│   ├── 강원대_2024/
│   ├── 알펜시아_2021/
│   ├── 도로공사_2022/
│   ├── ...
│   ├── gangneungsi_2022/               ← ASCII (WSL 한글 정규화 우회)
│   └── gangneungsuhup_2025/
│
├── 📁 _archive/                        ← 옛 데이터 / 백업 (10 items)
├── 📁 _scripts/                        ← 추출 Python 스크립트 (4 items)
└── 📁 _workspace/                      ← 작업 중간물 / 캐시 (73 items)
```

## 🚀 사용 방법

### A. 갤러리 보기
- `index.html` 더블클릭 → 브라우저에서 405 페어 확인
- 업종 16종 / 위험분류 / 세부분류 / 키워드 필터
- 페어 클릭 → 3단 라이트박스 (위험성평가 사진 | 감소대책 사진 | 상세 정보)
- 이미지 클릭 → 원본 크기 새 탭 보기
- ⬇ 사진 다운로드 (file:// 호환 Blob URL 방식)

### B. RAG 데이터 (image_library_v2_paired.json)
```json
{
  "pair_id": "PAIR-0088",
  "company": "강원대",
  "year": "2024",
  "industry": "교육서비스/대학교",
  "industry_code": "85302",
  "source_pdf_page": 311,
  "hazard_photo": "images/강원대_2024/SAFEG-KU-2024-U-0001.jpg",
  "measure_photo": "images/강원대_2024/SAFEG-KU-2024-U-0002.jpg",
  "hazard": "법학도서관 외부계단 난간 부자재 일부 탈락…",
  "basis": "안전보건규칙 제13조 (안전난간의 구조 및 설치요건)",
  "measure": "외부계단 난간 일부 탈락 부자재 부착 시공",
  "risk_class": "기계적 요인",
  "risk_subclass": "추락위험 부분 (개구부 등)",
  "admin_no": "06-1-4",
  "task_name": "시설관리"
}
```

## 📊 현재 통계

| 항목 | 수치 |
|---|---|
| 페어 | 405건 |
| 양쪽 사진 모두 | 354건 |
| 좌측만 (위험성평가) | 25건 |
| 우측만 (감소대책) | 26건 |
| 회사 | 24개 |
| 업종구분 | 16종 |
| 총 jpg | 2,071장 |

## 🏢 회사 폴더 명명 규칙 (`images/` 하위)

```
images/{회사명}_{연도}/SAFEG-{prefix}-{연도}-U-{seq:4자리}.jpg
```

- `prefix`: GR(강릉시), GNH(강릉농협), MED(강릉의료원), KU(강원대),
  ALP(알펜시아), DC(도로공사), CC(춘천교도소), CNH(춘천농협),
  SH(평창산림조합), SUH(강릉시수협), RT(알앤투), MSD(만석닭강정),
  YJ(영진철강), DH(동해광희고), MT(마트), GS(공업사), 등
- `U`: Unified (영역 통합 크롭)
- ASCII 폴더 (`gangneungsi_2022`, `gangneungsuhup_2025`): WSL 한글 정규화 이슈로 분리 저장

## 📚 _archive/ — 보관용 (참고)

| 파일 | 설명 |
|---|---|
| `image_library_v2_batch1~4.json` | 1차~4차 추출 배치 (회사 단위) |
| `image_library_v2_merged.json` | batch 통합본 (페어 구조 전) |
| `image_library_v2_v1merged.json` | v1(99장) + v2 병합 단계 |
| `image_library_v2_paired.bak_22swaps.json` | hazard/measure 22 swap 적용 후 백업 |
| `_removed_form_ids.json` | 양식 필터로 제거된 100건 ID |
| `index - 사업장 기준 샘플.html` | 사업장 필터 백업 (이전 index.html) |

## 🛠 _scripts/ — 추출 스크립트

| 스크립트 | 역할 |
|---|---|
| `_build_cache.py` | 페이지 해시 캐시 빌드 (좌/우 매칭용) |
| `_extract_missing.py` | 누락 이미지 영역 보강 추출 |
| `_unified_extract.py` | 좌/우 영역 통합 1장 크롭 추출 |
| `_text_reextract.py` | PDF 표 셀 단위로 측정·근거 등 텍스트 재추출 |

## 🗑 _workspace/ — 작업 중간물 (안전하게 삭제 가능)

- `_cache/`: 페이지별 해시·위치 캐시 (24개)
- `_page_renders/`: 페이지 렌더 임시 png
- `_new_assignments_*.json`: 1차 보강 추출 결과
- `_unified_assignments_*.json`: 통합 추출 결과
- `_text_reextract_*.json`: 텍스트 재추출 결과
- `_missing_extraction.json`, `_pair_position_check.json`, `_remap_log.json` 등: 작업 로그

## 🔁 처리 흐름 (이력)

1. PDF 24개 → pdfimages로 객체 단위 추출 (1~4차 배치)
2. 99장 v1 라이브러리 병합
3. 양식 이미지 100건 자동 필터링
4. 페어 구조 재정리
5. hazard/measure swap 보정 (perceptual hash 매칭)
6. 누락 영역 1차 보강 (186건)
7. **좌/우 영역 전체를 통합 1장 크롭 재추출** (현재 상태)
8. PDF 표 셀 단위 텍스트 재추출 (measure 등)
9. "ü" 체크표시 → 줄바꿈 불릿 변환 (렌더링 시점)
10. **회사 폴더 24개를 `images/`로 통합 + JSON 경로 일괄 갱신**

## 🌐 갤러리 기능

- **업종 16종 필터** (교육서비스/리조트/제조 등)
- 위험분류·세부분류 칩 필터
- 키워드 검색 (hazard·basis·measure·company 통합)
- localStorage 기반 삭제 (원본 보존)
- 3단 라이트박스 (1280px 최적화)
- XHR Blob 다운로드 (file:// 호환)
- "ü" 줄바꿈 자동 불릿 변환
