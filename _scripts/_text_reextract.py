import json, os, sys, re, pdfplumber, unicodedata
import warnings
warnings.filterwarnings('ignore')

PDF_DIR = '/sessions/sleepy-focused-heisenberg/mnt/uploads'
PDF_MAP = {
    ('춘천교도소','2023'): '공공기관_2023년 춘천교도소 위험성평가 보고서.pdf',
    ('춘천교도소','2025'): '공공기관_2025년_춘천교도소 위험성평가 보고서.pdf',
    ('도로공사','2022'): '공기업_2022년_한국도로공사 강릉지사_위험성평가 보고서.pdf',
    ('도로공사','2023'): '공기업_2023년_한국도로공사 강릉지사_ 위험성평가 보고서.pdf',
    ('강릉농협','2025'): '농업협동조합_2025년_강릉농협 위험성평가 결과보고서 v5_검토본.pdf',
    ('춘천농협','2025'): '농업협동조합_2025년_춘천농협 위험성평가 보고서.pdf',
    ('강원대','2023'): '대학교_2023년_강원대학교 위험성평가 보고서 (최종).pdf',
    ('강원대','2024'): '대학교_2024년_강원대학교 위험성평가 보고서 (최종).pdf',
    ('알펜시아','2021'): '리조트_2021년_알펜시아 위험성평가 보고서.pdf',
    ('레미콘','2026'): '비금속광물제조업_레미콘_2026년_위험성평가 시범실시_레미콘.pdf',
    ('평창산림조합','2025'): '산림조합_2025년 평창군 산림조합 위험성평가 결과보고서.pdf',
    ('강릉시수협','2025'): '수산업협동조합_2025년_강릉시수산업협동조합 위험성평가 보고서_최종본.pdf',
    ('공업사','2026'): '수송용기계기구제조업_공업_사2026년_위험성평가 시범실시_공업사.pdf',
    ('삼천리1차아파트','2025'): '시설관리업_아파트관리사무소_2025년_삼천리1차 아파트_위험성평가_2509.pdf',
    ('서초아파트','2025'): '시설관리업_아파트관리사무소_2025년_서초아파트_위험성평가_2508.pdf',
    ('마트','2025'): '유통업_마트_2025년_위험성평가 시범실시(강릉식자재마트).pdf',
    ('알앤투동탄','2022'): '제조업_소재제조_2022년 알앤투 위험성평가보고서(동탄)v1.pdf',
    ('알앤투','2022'): '제조업_소재제조_2022년 알앤투 위험성평가보고서.pdf',
    ('만석닭강정','2023'): '제조업_식료품제조_2023년_(주)만석닭강정(제조) 위험성평가 보고서_최종.pdf',
    ('영진철강','2023'): '제조업_철근가공업_2023년 영진철강 위험성평가 보고서.pdf',
    ('강릉의료원','2025'): '종합병원_2025년_강릉의료원 위험성평가 보고서.pdf',
    ('강릉시','2022'): '지자체_2022년_강릉시 위험성평가 보고서.pdf',
    ('동해광희고','2024'): '초중고교_2024년_동해광희고등학교 위험성평가 보고서.pdf',
    ('동해광희고','2025'): '초중고교_2025년_동해광희고등학교 위험성평가 보고서(인쇄본).pdf',
}

def clean(s):
    if not s: return ''
    s = str(s).replace('\\n', ' ').replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    s = re.sub(r'^\s*[üv✓✔]+\s*', '', s)  # 체크 마크 제거
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def find_value(table, label_keywords):
    """표에서 라벨 키워드를 포함한 셀을 찾고 그 옆 셀 값 반환"""
    for row in table:
        for ci, cell in enumerate(row):
            if not cell: continue
            cell_clean = clean(cell)
            for kw in label_keywords:
                if kw in cell_clean:
                    # 같은 행에서 우측 첫 비어있지 않은 셀
                    for nxt_i in range(ci+1, len(row)):
                        nxt = row[nxt_i]
                        if nxt and clean(nxt):
                            v = clean(nxt)
                            # 빈 라벨이나 다른 라벨과 일치하면 패스
                            if v in label_keywords: continue
                            if any(k in v for k in label_keywords if k != kw and len(k)>2):
                                continue
                            return v
    return ''

company, year = sys.argv[1], sys.argv[2]
key = (company, year)
if key not in PDF_MAP:
    print(f'❌ {key} not in PDF_MAP'); sys.exit(1)

with open('image_library_v2_paired.json','r',encoding='utf-8') as f:
    data = json.load(f)
recs = data['records']
co_recs = [r for r in recs if r['company']==company and r['year']==year]
if not co_recs:
    print(f'⏭️ {company}/{year}: 0 records'); sys.exit(0)

print(f'>>> {company}/{year}: {len(co_recs)}건 처리 중...')

pdf_path = os.path.join(PDF_DIR, PDF_MAP[key])
updates = []
with pdfplumber.open(pdf_path) as pdf:
    by_page = {}
    for r in co_recs:
        by_page.setdefault(r['source_pdf_page'], []).append(r)
    
    for pno in sorted(by_page.keys()):
        if pno < 1 or pno > len(pdf.pages): continue
        page = pdf.pages[pno-1]
        try:
            tables = page.extract_tables()
        except Exception as e:
            continue
        if not tables: continue
        
        # 가장 큰 표 사용 (셀 수 기준)
        table = max(tables, key=lambda t: sum(1 for row in t for c in row if c))
        
        # 각 필드 추출
        hazard = find_value(table, ['유해위험요인', '유해위험\n요인', '유해위험'])
        basis = find_value(table, ['법적근거', '관련근거'])
        measure = find_value(table, ['위험성 감소대책', '위험성\n감소대책', '감소대책'])
        risk_class = find_value(table, ['위험분류'])
        risk_subclass = find_value(table, ['세부분류'])
        # 관리번호 + 세부작업명 → 별도 메타
        admin_no = find_value(table, ['관리번호'])
        task_name = find_value(table, ['세부작업명'])
        
        # 같은 페이지 모든 페어에 적용 (대부분 1페어/1페이지)
        for r in by_page[pno]:
            updates.append({
                'pair_id': r['pair_id'],
                'hazard': hazard,
                'basis': basis,
                'measure': measure,
                'risk_class': risk_class,
                'risk_subclass': risk_subclass,
                'admin_no': admin_no,
                'task_name': task_name,
            })

out_file = f'_text_reextract_{company}_{year}.json'
with open(out_file,'w',encoding='utf-8') as f:
    json.dump(updates, f, ensure_ascii=False, indent=2)
print(f'<<< {company}/{year}: {len(updates)}건 갱신')
