import json, os, sys, pdfplumber, imagehash
from PIL import Image
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

company, year = sys.argv[1], sys.argv[2]
cache_file = f'_cache/{company}_{year}.json'
if os.path.exists(cache_file):
    print(f'⏭️  이미 있음: {cache_file}')
    sys.exit(0)

with open('image_library_v2_paired.bak_22swaps.json','r',encoding='utf-8') as f:
    data = json.load(f)
recs = data['records']
pages = sorted(set(r['source_pdf_page'] for r in recs 
                   if r['company']==company and r['year']==year 
                   and (r.get('hazard_photo') or r.get('measure_photo'))))
print(f'페이지 {len(pages)}개')

pdf_path = os.path.join(PDF_DIR, PDF_MAP[(company,year)])
out = {}
with pdfplumber.open(pdf_path) as pdf:
    for pno in pages:
        if pno < 1 or pno > len(pdf.pages): continue
        page = pdf.pages[pno-1]
        big = sorted([im for im in page.images if im['width']>80 and im['height']>60], key=lambda im: im['x0'])
        if not big: 
            out[str(pno)] = {'big': [], 'page_w': page.width}
            continue
        pim = page.to_image(resolution=130)
        pimg = pim.original
        scale = pimg.size[0] / page.width
        bigs = []
        for idx, im in enumerate(big):
            x0 = int(im['x0']*scale); y0 = int(im['top']*scale)
            x1 = int(im['x1']*scale); y1 = int(im['bottom']*scale)
            try:
                h = str(imagehash.phash(pimg.crop((x0,y0,x1,y1))))
            except: continue
            bigs.append({'idx': idx, 'x0': float(im['x0']), 'x1': float(im['x1']), 'hash': h})
        out[str(pno)] = {'big': bigs, 'page_w': float(page.width)}

with open(cache_file,'w',encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False)
print(f'✅ 저장: {cache_file} ({len(out)} pages)')
