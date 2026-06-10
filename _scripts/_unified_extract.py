import json, os, sys, re, pdfplumber, unicodedata
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

def is_form_image_smart(crop):
    """채도 고려 form 판정 — 컬러 도식은 form으로 분류 안 함"""
    gray = crop.convert('L')
    pixels = list(gray.getdata())
    wr = sum(1 for p in pixels if p>235)/len(pixels)
    stat = ImageStat.Stat(gray)
    hsv = crop.convert('HSV')
    hsv_px = list(hsv.getdata())
    sat = sum(p[1] for p in hsv_px) / len(hsv_px)
    # form: 흰 배경 75% 이상 + 낮은 대비 + 채도 매우 낮음
    return wr > 0.75 and stat.stddev[0] < 50 and stat.mean[0] > 215 and sat < 12

company, year = sys.argv[1], sys.argv[2]
key = (company, year)
if key not in PDF_MAP:
    print(f'❌ PDF MAP에 없음: {key}')
    sys.exit(1)

with open('image_library_v2_paired.json','r',encoding='utf-8') as f:
    data = json.load(f)
recs = data['records']

# 회사 페어 모두
co_recs = [r for r in recs if r['company']==company and r['year']==year]
if not co_recs:
    print(f'⏭️  {company}/{year}: 페어 없음')
    sys.exit(0)

folder = unicodedata.normalize('NFC', f'{company}_{year}')
prefix = PREFIX[key]

# 폴더의 마지막 seq 추출 (새 파일은 _U 접미사로 통합 표시)
os.makedirs(folder, exist_ok=True)
existing = [f for f in os.listdir(folder) if f.endswith('.jpg')]
# 통합 이미지 명명: SAFEG-{prefix}-U-{seq:04d}.jpg
u_files = [f for f in existing if '-U-' in f]
max_u = 0
for f in u_files:
    m = re.search(r'-U-(\d+)\.jpg$', f)
    if m: max_u = max(max_u, int(m.group(1)))
next_u = max_u + 1

pdf_path = os.path.join(PDF_DIR, PDF_MAP[key])
print(f'>>> {company}/{year} 시작 (페어 {len(co_recs)}건)')

new_assigns = []  # {pair_id, hazard_photo, measure_photo}
skip_count = 0
with pdfplumber.open(pdf_path) as pdf:
    # 페이지별 그룹화 (같은 페이지 1번 렌더)
    page_groups = {}
    for r in co_recs:
        p = r['source_pdf_page']
        page_groups.setdefault(p, []).append(r)
    
    for pno in sorted(page_groups.keys()):
        if pno < 1 or pno > len(pdf.pages): continue
        page = pdf.pages[pno-1]
        big = [im for im in page.images if im['width']>80 and im['height']>60]
        if not big: continue
        
        left_imgs = [im for im in big if im['x0']+im['width']/2 < page.width/2]
        right_imgs = [im for im in big if im['x0']+im['width']/2 >= page.width/2]
        
        # 같은 페이지에 페어가 여러 개 있을 수 있음 — 일단 첫 페어만 처리 (대부분 페이지당 1페어)
        # 페어별로 동일한 통합 영역 사용
        pim = page.to_image(resolution=180)
        pimg = pim.original
        scale = pimg.size[0] / page.width
        
        def make_crop(imgs):
            if not imgs: return None
            x0 = min(im['x0'] for im in imgs)
            x1 = max(im['x1'] for im in imgs)
            y0 = min(im['top'] for im in imgs)
            y1 = max(im['bottom'] for im in imgs)
            pad = 6
            cx0 = max(0, int((x0-pad)*scale))
            cy0 = max(0, int((y0-pad)*scale))
            cx1 = min(pimg.size[0], int((x1+pad)*scale))
            cy1 = min(pimg.size[1], int((y1+pad)*scale))
            crop = pimg.crop((cx0, cy0, cx1, cy1))
            cw, ch = crop.size
            if cw < 80 or ch < 60: return None
            # form 필터 비활성화 — 영역에 이미지 있으면 무조건 통합 추출
            # 거의 완전 빈 흰색 영역만 제외 (안전장치)
            from PIL import ImageStat as _IS
            _g = crop.convert('L')
            _stat = _IS.Stat(_g)
            if _stat.mean[0] > 248: return None  # 거의 완전 빈 흰색
            # 가로 800px 리사이즈
            if cw > 800:
                ratio = 800 / cw
                crop = crop.resize((800, int(ch*ratio)), Image.LANCZOS)
            return crop
        
        left_crop = make_crop(left_imgs)
        right_crop = make_crop(right_imgs)
        
        for r in page_groups[pno]:
            new_h = r.get('hazard_photo') or ''
            new_m = r.get('measure_photo') or ''
            
            if left_crop is not None:
                fn = f'SAFEG-{prefix}-U-{next_u:04d}.jpg'
                fp = os.path.join(folder, fn)
                left_crop.convert('RGB').save(fp, 'JPEG', quality=78, optimize=True)
                new_h = f'{folder}/{fn}'
                next_u += 1
            
            if right_crop is not None:
                fn = f'SAFEG-{prefix}-U-{next_u:04d}.jpg'
                fp = os.path.join(folder, fn)
                right_crop.convert('RGB').save(fp, 'JPEG', quality=78, optimize=True)
                new_m = f'{folder}/{fn}'
                next_u += 1
            
            new_assigns.append({
                'pair_id': r['pair_id'],
                'hazard_photo': new_h,
                'measure_photo': new_m,
            })
            # 같은 페이지 페어가 여러 개일 때는 같은 통합 이미지 공유 → 한 번 저장 후 동일 경로 사용
            # 위 로직은 페이지마다 새 파일 생성 → 페이지당 페어가 1개면 OK
            # 페어가 여러 개일 가능성 적지만 안전을 위해 첫 페어만 새 파일, 이후는 동일 경로
            left_crop = None
            right_crop = None

out_file = f'_unified_assignments_{company}_{year}.json'
with open(out_file,'w',encoding='utf-8') as f:
    json.dump(new_assigns, f, ensure_ascii=False, indent=2)
print(f'<<< {company}/{year} 완료: {len(new_assigns)}건 페어 갱신, skip={skip_count}')
