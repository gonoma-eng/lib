import json, os, sys, pdfplumber
from PIL import Image, ImageStat
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
PREFIX = {
    ('춘천교도소','2023'): 'CC-2023', ('춘천교도소','2025'): 'CC-2025',
    ('도로공사','2022'): 'DC-2022', ('도로공사','2023'): 'DC-2023',
    ('강릉농협','2025'): 'GNH-2025', ('춘천농협','2025'): 'CNH-2025',
    ('강원대','2023'): 'KU-2023', ('강원대','2024'): 'KU-2024',
    ('알펜시아','2021'): 'ALP-2021', ('레미콘','2026'): 'REM-2026',
    ('평창산림조합','2025'): 'SH-2025', ('강릉시수협','2025'): 'SUH-2025',
    ('공업사','2026'): 'GS-2026', ('삼천리1차아파트','2025'): 'SC-2025',
    ('서초아파트','2025'): 'SCH-2025', ('마트','2025'): 'MT-2025',
    ('알앤투동탄','2022'): 'RT-D-2022', ('알앤투','2022'): 'RT-2022',
    ('만석닭강정','2023'): 'MSD-2023', ('영진철강','2023'): 'YJ-2023',
    ('강릉의료원','2025'): 'MED-2025', ('강릉시','2022'): 'GR-2022',
    ('동해광희고','2024'): 'DH-2024', ('동해광희고','2025'): 'DH-2025',
}

company, year = sys.argv[1], sys.argv[2]
print(f'>>> {company}/{year} 시작')

# 누락 데이터 로드
with open('_missing_extraction.json','r',encoding='utf-8') as f:
    missing = json.load(f)

# 회사 페어 분리
left_cases = [m for m in missing['left_missing'] if m['company']==company and m['year']==year]
right_cases = [m for m in missing['right_missing'] if m['company']==company and m['year']==year]
print(f'  좌측 누락: {len(left_cases)}, 우측 누락: {len(right_cases)}')

if not left_cases and not right_cases:
    print('  변경 없음')
    sys.exit(0)

# 회사 폴더의 마지막 seq
folder = f'{company}_{year}'
prefix = PREFIX[(company,year)]
existing = sorted([f for f in os.listdir(folder) if f.endswith('.jpg')])
# 마지막 seq 추출 (LMxxx, V1xxx 등 다양한 prefix 처리)
import re
max_seq = 0
for f in existing:
    name = f.replace('.jpg','').replace(f'SAFEG-{prefix}-','')
    # 숫자만 추출
    m = re.search(r'(\d+)$', name)
    if m:
        max_seq = max(max_seq, int(m.group(1)))
print(f'  최대 seq: {max_seq}')

# PDF 로드 + 페이지 캐싱
pdf_path = os.path.join(PDF_DIR, PDF_MAP[(company,year)])
new_assignments = []  # {pair_id, slot('hazard'/'measure'), filename}

# 페이지별로 그룹화 (동일 페이지 좌+우 한 번만 렌더)
from collections import defaultdict
pages_to_render = defaultdict(lambda: {'left': None, 'right': None})
for m in left_cases:
    pages_to_render[m['page']]['left'] = m
for m in right_cases:
    pages_to_render[m['page']]['right'] = m

next_seq = max_seq + 1

with pdfplumber.open(pdf_path) as pdf:
    for pno, sides in sorted(pages_to_render.items()):
        page = pdf.pages[pno-1]
        # 렌더링 (180dpi)
        pim = page.to_image(resolution=180)
        pimg = pim.original
        scale = pimg.size[0] / page.width
        
        for side_name, m in sides.items():
            if not m: continue
            box = m[f'{side_name}_box']
            # 사진 영역만 살짝 padding 두고 크롭
            pad = 8  # PDF pt 기준 padding
            x0 = max(0, (box['x0'] - pad) * scale)
            y0 = max(0, (box['y0'] - pad) * scale)
            x1 = min(pimg.size[0], (box['x1'] + pad) * scale)
            y1 = min(pimg.size[1], (box['y1'] + pad) * scale)
            crop = pimg.crop((int(x0), int(y0), int(x1), int(y1)))
            
            # 양식 이미지인지 검증 (스킵)
            gray = crop.convert('L')
            pixels = list(gray.getdata())
            wr = sum(1 for p in pixels if p>235)/len(pixels)
            stat = ImageStat.Stat(gray)
            is_form = wr > 0.65 and stat.stddev[0] < 65 and stat.mean[0] > 200
            if is_form:
                print(f'  ⏭️ skip form: p{pno} {side_name}')
                continue
            
            # 너무 작거나 비율 이상한 경우 스킵
            cw, ch = crop.size
            if cw < 80 or ch < 60:
                print(f'  ⏭️ skip too small: p{pno} {side_name} {cw}x{ch}')
                continue
            
            # 가로 800px 기준 resize
            if cw > 800:
                ratio = 800 / cw
                crop = crop.resize((800, int(ch*ratio)), Image.LANCZOS)
            
            # 저장
            fname = f'SAFEG-{prefix}-{next_seq:04d}.jpg'
            fpath = os.path.join(folder, fname)
            crop.convert('RGB').save(fpath, 'JPEG', quality=75, optimize=True)
            slot = 'hazard' if side_name == 'left' else 'measure'
            new_assignments.append({
                'pair_id': m['pair_id'],
                'slot': slot,
                'file': f'{folder}/{fname}',
                'size_kb': os.path.getsize(fpath) // 1024,
            })
            print(f'  ✅ {m["pair_id"]} p{pno} {slot}: {fname} ({os.path.getsize(fpath)//1024}KB)')
            next_seq += 1

# 결과 저장
out_file = f'_new_assignments_{company}_{year}.json'
with open(out_file,'w',encoding='utf-8') as f:
    json.dump(new_assignments, f, ensure_ascii=False, indent=2)
print(f'  저장: {out_file} ({len(new_assignments)}건)')
