"""
SAFEG-Lexia 산업안전보건 위험성평가 감소대책 일러스트 자동 생성
==========================================================
페어 정보를 자연어 텍스트로 입력하면 자동 파싱하여 일러스트(SVG+PNG)를 생성합니다.

【 사용법 】

방법 1) 텍스트 직접 전달
  python _scripts/_generate_safety_illustration.py PAIR-0003 << 'EOF'
  위험분류 : 기계적 요인
  세부분류 : 협착위험 부분(감김,끼임)
  유해위험요인 : 지하 소방펌프실 모터 구동부 방호덮개 미설치로 인한 작업자 끼임 위험
  위험관련근거 : 안전보건규칙 제87조(원동기ㆍ회전축등의 위험방지)
  감소대책 : 구동부 방호덮개 설치
  회사 : 강릉농협
  연도 : 2025
  EOF

방법 2) 파일 입력
  python _scripts/_generate_safety_illustration.py PAIR-0003 -f pair_info.txt

방법 3) Python 모듈로 import
  from _scripts._generate_safety_illustration import generate_from_text
  generate_from_text('''
  위험분류 : 기계적 요인
  세부분류 : 협착위험 ...
  ''', pair_id='PAIR-0003')

【 자동 처리 사항 】
  ✅ 라벨: "위험분류 / 세부분류 / 유해위험요인 / 위험관련근거 / 감소대책" 등 자동 인식
  ✅ scene 자동 판단 (위험분류 + 키워드 기반)
  ✅ SVG + PNG 동시 생성 (1280×960)
  ✅ 파일명: AI-{pair_id}.{svg,png}
  ✅ 저장 경로: images/_ai_recommended/

【 지원 scene 분류 】
  chemical    : 화학물질·MSDS·유기용제·세제
  mechanical  : 기계·방호덮개·회전체·벨트·모터·펌프
  electrical  : 전기·감전·콘센트 (향후 확장)
  fall        : 추락·난간·개구부·옥상 (향후 확장)
  construction: 굴삭기·신호수·건설 (향후 확장)
  storage     : 창고·적재 (향후 확장)
  cleaning    : 청소·세제 (향후 확장)
"""

import os, sys, re, argparse, subprocess
from pathlib import Path

# ─────────────────────────────────────────────────────────────
# 1. 자연어 입력 파서
# ─────────────────────────────────────────────────────────────

FIELD_ALIASES = {
    'risk_class':      ['위험분류', '분류', '위험구분'],
    'risk_subclass':   ['세부분류', '세부', '분류 세부'],
    'hazard':          ['유해위험요인', '유해', '위험요인', '유해 위험요인'],
    'basis':           ['위험관련근거', '관련근거', '법적근거', '근거'],
    'measure':         ['감소대책', '위험성 감소대책', '대책', '개선방안'],
    'company':         ['회사', '사업장'],
    'year':            ['연도', '연도', 'year'],
    'page':            ['페이지', '출처페이지', '출처 페이지'],
    'admin_no':        ['관리번호'],
    'task_name':       ['세부작업명'],
}

def parse_pair_text(text):
    """자연어 텍스트에서 페어 정보 자동 추출
    
    인식 패턴 (라벨 자동 인식):
      - "위험분류 : 기계적 요인"
      - "세부분류: 협착위험 부분"
      - "유해위험요인 - 지하 소방펌프실 ..."
      - "감소대책 : 구동부 방호덮개 설치"
    """
    result = {k: '' for k in FIELD_ALIASES}
    
    # 라벨 키워드 → 필드명 매핑
    label_to_field = {}
    for field, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            label_to_field[alias.replace(' ','')] = field
    
    # 라인별 파싱 (라벨: 값 형태)
    lines = text.strip().splitlines()
    current_field = None
    current_value = []
    
    for line in lines:
        line = line.strip().lstrip('-').lstrip('•').strip()
        if not line: continue
        
        # 라벨 패턴: "키 : 값" 또는 "키: 값" 또는 "키 = 값"
        m = re.match(r'^([가-힣\s]+?)\s*[:：=]\s*(.*)$', line)
        if m:
            label = m.group(1).strip().replace(' ','')
            value = m.group(2).strip()
            # 라벨이 알려진 필드인지 확인
            if label in label_to_field:
                # 이전 필드 마무리
                if current_field and current_value:
                    result[current_field] = ' '.join(current_value).strip()
                current_field = label_to_field[label]
                current_value = [value] if value else []
                continue
        
        # 라벨 매칭 안 되면 이전 필드의 연속된 줄로 처리
        if current_field:
            current_value.append(line)
    
    # 마지막 필드 마무리
    if current_field and current_value:
        result[current_field] = ' '.join(current_value).strip()
    
    return result

def detect_scene(info):
    """위험분류 + 키워드 기반 scene 자동 판단"""
    rc = info.get('risk_class', '')
    rs = info.get('risk_subclass', '')
    haz = info.get('hazard', '')
    mea = info.get('measure', '')
    all_text = f'{rc} {rs} {haz} {mea}'.lower()
    
    # 우선순위 키워드 매칭
    scene_keywords = {
        'chemical':    ['화학', '유기용제', 'msds', '용제', '세제', '오일', '인화성', '독성', '경고표시', '경고표지', '화학물질', '청소'],
        'electrical':  ['감전', '전기', '콘센트', '누전', '전선', '절연'],
        'fall':        ['추락', '난간', '개구부', '옥상', '떨어짐', '높은', '집수정'],
        'construction':['굴삭기', '백호우', '신호수', '건설', '지게차', '중장비'],
        'storage':     ['창고', '적재', '보관', '선반'],
        'mechanical':  ['방호덮개', '회전체', '벨트', '모터', '펌프', '구동부', '협착', '감김', '끼임', '회전축', '풀리', '기어', '그라인더'],
    }
    
    scores = {}
    for scene, kws in scene_keywords.items():
        scores[scene] = sum(1 for k in kws if k in all_text)
    
    # 가장 높은 점수의 scene
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else 'chemical'  # fallback

# ─────────────────────────────────────────────────────────────
# 2. SVG 빌더 (재사용 컴포넌트)
# ─────────────────────────────────────────────────────────────

COMMON_DEFS = '''
  <defs>
    <linearGradient id="bgSoft" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#f0fdf4"/><stop offset="100%" stop-color="#dcfce7"/>
    </linearGradient>
    <linearGradient id="vestGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#fb923c"/><stop offset="100%" stop-color="#c2410c"/>
    </linearGradient>
    <linearGradient id="helmetYellow" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#fde047"/><stop offset="100%" stop-color="#a16207"/>
    </linearGradient>
    <linearGradient id="pantsGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#475569"/><stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
    <radialGradient id="skinGrad" cx="0.4" cy="0.4" r="0.7">
      <stop offset="0%" stop-color="#fed7aa"/><stop offset="100%" stop-color="#f59e0b"/>
    </radialGradient>
    <filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur in="SourceAlpha" stdDeviation="4"/>
      <feOffset dx="0" dy="4"/>
      <feComponentTransfer><feFuncA type="linear" slope="0.25"/></feComponentTransfer>
      <feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <marker id="arrowR" markerWidth="14" markerHeight="14" refX="11" refY="7" orient="auto">
      <path d="M0,0 L12,7 L0,14 Z" fill="#dc2626"/>
    </marker>
  </defs>
'''

SCENE_RENDERERS = {}
def register_scene(name):
    def deco(fn): SCENE_RENDERERS[name] = fn; return fn
    return deco

@register_scene('chemical')
def render_chemical(info):
    measure = info.get('measure','')
    return f'''
  <rect width="1280" height="960" fill="#fefce8"/>
  <rect x="0" y="700" width="1280" height="260" fill="#a8a29e"/>
  <!-- 휘발유 통 (좌측) -->
  <g transform="translate(180, 420)" filter="url(#softShadow)">
    <ellipse cx="100" cy="320" rx="110" ry="14" fill="#000" opacity="0.25"/>
    <rect x="30" y="80" width="140" height="240" rx="8" fill="#dc2626" stroke="#7f1d1d" stroke-width="3"/>
    <ellipse cx="100" cy="80" rx="70" ry="14" fill="#ef4444" stroke="#7f1d1d" stroke-width="3"/>
    <ellipse cx="100" cy="74" rx="68" ry="12" fill="#fca5a5"/>
    <rect x="80" y="50" width="40" height="30" rx="6" fill="#7f1d1d"/>
    <rect x="40" y="130" width="120" height="160" fill="white" stroke="#dc2626" stroke-width="4"/>
    <path d="M100,145 L155,200 L100,255 L45,200 Z" fill="white" stroke="#dc2626" stroke-width="3"/>
    <g transform="translate(100, 200)">
      <path d="M0,-25 Q-10,-10 -8,5 Q-15,10 -10,22 Q-5,8 0,18 Q5,8 10,22 Q15,10 8,5 Q10,-10 0,-25" fill="#dc2626"/>
    </g>
    <text x="100" y="278" text-anchor="middle" font-size="14" font-weight="900" fill="#dc2626" style="font-family:sans-serif">⚠ 인화성</text>
  </g>
  <!-- 거대 경고 라벨 -->
  <g transform="translate(640, 280)" filter="url(#softShadow)">
    <rect x="0" y="0" width="480" height="440" rx="14" fill="white" stroke="#0f172a" stroke-width="5"/>
    <rect x="0" y="0" width="480" height="80" rx="14" fill="#dc2626"/>
    <text x="240" y="40" text-anchor="middle" font-size="28" font-weight="900" fill="white" style="font-family:sans-serif">⚠ DANGER · 위험</text>
    <text x="240" y="65" text-anchor="middle" font-size="13" font-weight="600" fill="white" letter-spacing="3" style="font-family:sans-serif">HAZARDOUS CHEMICAL</text>
    <g transform="translate(80, 130)"><path d="M0,0 L70,70 L0,140 L-70,70 Z" fill="white" stroke="#dc2626" stroke-width="4"/><g transform="translate(0, 70)"><path d="M0,-30 Q-12,-10 -8,8 Q-18,15 -12,30 Q-6,12 0,25 Q6,12 12,30 Q18,15 8,8 Q12,-10 0,-30" fill="#dc2626"/></g><text x="0" y="170" text-anchor="middle" font-size="12" font-weight="700" fill="#0f172a" style="font-family:sans-serif">인화성</text></g>
    <g transform="translate(240, 130)"><path d="M0,0 L70,70 L0,140 L-70,70 Z" fill="white" stroke="#dc2626" stroke-width="4"/><g transform="translate(0, 70)" stroke="#dc2626" stroke-width="3" fill="none"><circle cx="0" cy="-8" r="14"/><line x1="-25" y1="20" x2="25" y2="20"/><path d="M-12,-5 Q0,8 12,-5"/></g><text x="0" y="170" text-anchor="middle" font-size="12" font-weight="700" fill="#0f172a" style="font-family:sans-serif">건강유해성</text></g>
    <g transform="translate(400, 130)"><path d="M0,0 L70,70 L0,140 L-70,70 Z" fill="white" stroke="#dc2626" stroke-width="4"/><text x="0" y="80" text-anchor="middle" font-size="36" font-weight="900" fill="#dc2626" style="font-family:sans-serif">!</text><text x="0" y="170" text-anchor="middle" font-size="12" font-weight="700" fill="#0f172a" style="font-family:sans-serif">자극성</text></g>
    <g transform="translate(40, 310)" font-family="sans-serif">
      <rect x="0" y="0" width="400" height="25" fill="#fef3c7"/><text x="10" y="17" font-size="13" font-weight="800" fill="#92400e">신호어: 위험</text>
      <rect x="0" y="35" width="400" height="25" fill="#fef3c7"/><text x="10" y="52" font-size="13" font-weight="800" fill="#92400e">유해문구: 인화성 액체, 건강유해성</text>
      <rect x="0" y="70" width="400" height="25" fill="#fef3c7"/><text x="10" y="87" font-size="13" font-weight="800" fill="#92400e">예방: 화기·점화원 차단, 보호구 착용</text>
    </g>
  </g>
  <!-- 안전 라벨 -->
  <g transform="translate(280, 200)" filter="url(#softShadow)">
    <rect x="-120" y="-32" width="240" height="64" rx="10" fill="#fde047" stroke="#1e293b" stroke-width="3"/>
    <text x="0" y="-5" text-anchor="middle" font-size="18" font-weight="900" fill="#1e293b" style="font-family:&apos;Pretendard&apos;,sans-serif">유해·위험성</text>
    <text x="0" y="22" text-anchor="middle" font-size="18" font-weight="900" fill="#1e293b" style="font-family:&apos;Pretendard&apos;,sans-serif">경고표지 부착</text>
    <path d="M0,35 L20,240" stroke="#dc2626" stroke-width="4" fill="none" marker-end="url(#arrowR)"/>
  </g>
'''

@register_scene('mechanical')
def render_mechanical(info):
    return '''
  <rect width="1280" height="960" fill="#fef9c3"/>
  <rect x="0" y="0" width="1280" height="650" fill="#e0e7ff" opacity="0.4"/>
  <g stroke="#64748b" stroke-width="6" fill="none" opacity="0.5">
    <line x1="0" y1="120" x2="1280" y2="120"/><line x1="0" y1="180" x2="1280" y2="180"/>
    <line x1="120" y1="0" x2="120" y2="650"/><line x1="1180" y1="0" x2="1180" y2="650"/>
  </g>
  <rect x="0" y="650" width="1280" height="310" fill="#94a3b8"/>
  <!-- 소방펌프 + 모터 + 방호덮개 -->
  <g transform="translate(360, 360)" filter="url(#softShadow)">
    <ellipse cx="280" cy="380" rx="320" ry="20" fill="#000" opacity="0.3"/>
    <rect x="-20" y="320" width="600" height="60" fill="#1e293b"/>
    <rect x="-40" y="370" width="640" height="20" fill="#0f172a"/>
    <g transform="translate(20, 100)">
      <rect x="0" y="80" width="180" height="180" rx="10" fill="#dc2626" stroke="#7f1d1d" stroke-width="3"/>
      <rect x="0" y="80" width="180" height="40" rx="10" fill="#ef4444"/>
      <circle cx="90" cy="180" r="50" fill="#1e293b" stroke="#7f1d1d" stroke-width="2"/>
      <circle cx="90" cy="180" r="35" fill="#475569" stroke="#fbbf24" stroke-width="2"/>
      <text x="90" y="60" text-anchor="middle" font-size="14" font-weight="900" fill="#7f1d1d" style="font-family:sans-serif">FIRE PUMP</text>
    </g>
    <g transform="translate(360, 130)">
      <rect x="0" y="80" width="200" height="170" rx="10" fill="#64748b" stroke="#1e293b" stroke-width="3"/>
      <rect x="0" y="80" width="200" height="35" rx="10" fill="#94a3b8"/>
      <text x="100" y="105" text-anchor="middle" font-size="14" font-weight="900" fill="#fbbf24" letter-spacing="2" style="font-family:sans-serif">MOTOR</text>
      <g fill="#0f172a"><rect x="20" y="135" width="6" height="100"/><rect x="40" y="135" width="6" height="100"/><rect x="60" y="135" width="6" height="100"/><rect x="80" y="135" width="6" height="100"/><rect x="100" y="135" width="6" height="100"/><rect x="120" y="135" width="6" height="100"/><rect x="140" y="135" width="6" height="100"/><rect x="160" y="135" width="6" height="100"/></g>
    </g>
    <!-- 방호덮개 -->
    <g transform="translate(200, 230)">
      <rect x="0" y="0" width="160" height="120" rx="8" fill="none" stroke="#10b981" stroke-width="6"/>
      <rect x="0" y="0" width="160" height="120" rx="8" fill="#10b981" opacity="0.1"/>
      <g stroke="#10b981" stroke-width="3" opacity="0.7" fill="none">
        <line x1="0" y1="30" x2="160" y2="30"/><line x1="0" y1="60" x2="160" y2="60"/><line x1="0" y1="90" x2="160" y2="90"/>
        <line x1="40" y1="0" x2="40" y2="120"/><line x1="80" y1="0" x2="80" y2="120"/><line x1="120" y1="0" x2="120" y2="120"/>
      </g>
      <circle cx="40" cy="60" r="22" fill="#475569" stroke="#1e293b" stroke-width="2"/><circle cx="40" cy="60" r="6" fill="#fbbf24"/>
      <circle cx="120" cy="60" r="22" fill="#475569" stroke="#1e293b" stroke-width="2"/><circle cx="120" cy="60" r="6" fill="#fbbf24"/>
      <path d="M40,38 L120,38 M40,82 L120,82" stroke="#1e293b" stroke-width="8"/>
      <rect x="40" y="-25" width="80" height="20" rx="10" fill="#10b981"/>
      <text x="80" y="-10" text-anchor="middle" font-size="11" font-weight="900" fill="white" letter-spacing="1" style="font-family:sans-serif">SAFETY GUARD</text>
    </g>
  </g>
  <!-- 작업자 -->
  <g transform="translate(960, 460)" filter="url(#softShadow)">
    <ellipse cx="0" cy="280" rx="60" ry="9" fill="#000" opacity="0.25"/>
    <path d="M-22,150 L-25,278 L-15,280 L-10,160 Z" fill="url(#pantsGrad)" stroke="#0f172a" stroke-width="1.5"/>
    <path d="M10,160 L15,280 L25,278 L22,150 Z" fill="url(#pantsGrad)" stroke="#0f172a" stroke-width="1.5"/>
    <ellipse cx="-20" cy="282" rx="20" ry="6" fill="#0f172a"/><ellipse cx="20" cy="282" rx="20" ry="6" fill="#0f172a"/>
    <path d="M-40,70 L40,70 L42,160 L-42,160 Z" fill="url(#vestGrad)" stroke="#9a3412" stroke-width="2"/>
    <rect x="-40" y="105" width="80" height="5" fill="#fef3c7"/><rect x="-40" y="135" width="80" height="5" fill="#fef3c7"/>
    <path d="M-40,75 Q-58,40 -70,0 L-58,-5 L-30,80 Z" fill="url(#vestGrad)" stroke="#9a3412" stroke-width="2"/>
    <path d="M40,75 Q50,100 48,140 L38,143 L28,80 Z" fill="url(#vestGrad)" stroke="#9a3412" stroke-width="2"/>
    <circle cx="-65" cy="0" r="10" fill="url(#skinGrad)" stroke="#9a3412" stroke-width="1.5"/>
    <circle cx="42" cy="143" r="9" fill="url(#skinGrad)" stroke="#9a3412" stroke-width="1.5"/>
    <ellipse cx="0" cy="32" rx="26" ry="29" fill="url(#skinGrad)" stroke="#9a3412" stroke-width="2"/>
    <ellipse cx="-9" cy="33" rx="2.5" ry="3" fill="#1e293b"/><ellipse cx="9" cy="33" rx="2.5" ry="3" fill="#1e293b"/>
    <path d="M-5,46 Q0,49 5,46" fill="none" stroke="#9a3412" stroke-width="2" stroke-linecap="round"/>
    <path d="M-30,30 Q-30,-6 0,-12 Q30,-6 30,30 L30,34 L-30,34 Z" fill="url(#helmetYellow)" stroke="#1e293b" stroke-width="2"/>
    <ellipse cx="0" cy="6" rx="32" ry="6" fill="#f59e0b"/>
    <path d="M-30,34 L-34,40 L34,40 L30,34 Z" fill="#92400e" stroke="#1e293b" stroke-width="1.5"/>
  </g>
  <!-- 라벨: 방호덮개 설치 -->
  <g transform="translate(440, 240)" filter="url(#softShadow)">
    <rect x="-110" y="-32" width="220" height="64" rx="10" fill="#fde047" stroke="#1e293b" stroke-width="3"/>
    <text x="0" y="-5" text-anchor="middle" font-size="20" font-weight="900" fill="#1e293b" style="font-family:&apos;Pretendard&apos;,sans-serif">구동부</text>
    <text x="0" y="22" text-anchor="middle" font-size="20" font-weight="900" fill="#1e293b" style="font-family:&apos;Pretendard&apos;,sans-serif">방호덮개 설치</text>
    <path d="M0,35 L120,180" stroke="#dc2626" stroke-width="4" fill="none" marker-end="url(#arrowR)"/>
  </g>
  <!-- 끼임 경고 표지 -->
  <g transform="translate(180, 460)" filter="url(#softShadow)">
    <rect x="-8" y="160" width="16" height="160" fill="#525252"/>
    <ellipse cx="0" cy="325" rx="30" ry="6" fill="#525252"/>
    <path d="M0,0 L100,160 L-100,160 Z" fill="#fde047" stroke="#dc2626" stroke-width="6" stroke-linejoin="round"/>
    <g transform="translate(0, 90)">
      <path d="M-30,-10 L-15,-20 L0,-20 L5,-5 L0,10 L-20,17 L-35,10 Z" fill="#fde68a" stroke="#7c2d12" stroke-width="2"/>
      <circle cx="25" cy="0" r="20" fill="#475569" stroke="#1e293b" stroke-width="2"/>
      <g fill="#475569"><rect x="22" y="-28" width="6" height="10"/><rect x="22" y="18" width="6" height="10"/><rect x="-3" y="-3" width="10" height="6"/><rect x="48" y="-3" width="10" height="6"/></g>
      <circle cx="25" cy="0" r="6" fill="#1e293b"/>
    </g>
    <text x="0" y="135" text-anchor="middle" font-size="16" font-weight="900" fill="#1e293b" style="font-family:&apos;Pretendard&apos;,sans-serif">⚠ 끼임 위험</text>
  </g>
'''

# ─────────────────────────────────────────────────────────────
# 3. 일러스트 생성 (메인 API)
# ─────────────────────────────────────────────────────────────

def build_svg(info, pair_id, scene=None):
    """페어 정보 → 전체 SVG 조립"""
    if scene is None:
        scene = detect_scene(info)
    renderer = SCENE_RENDERERS.get(scene, SCENE_RENDERERS['chemical'])
    body = renderer(info)
    
    title = info.get('measure') or info.get('hazard') or pair_id
    if len(title) > 50: title = title[:48] + '…'
    footer_bits = [f'SAFEG-Lexia · {pair_id}']
    if info.get('company'): footer_bits.append(info['company'])
    if info.get('year'): footer_bits.append(info['year'])
    if info.get('basis'): footer_bits.append('📋 ' + info['basis'][:50])
    footer = ' · '.join(footer_bits)
    
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 960" width="1280" height="960">
{COMMON_DEFS}
{body}
  <!-- 상단 라벨 -->
  <g transform="translate(640, 55)">
    <rect x="-300" y="-26" width="600" height="52" rx="26" fill="white" stroke="#5b47eb" stroke-width="3" filter="url(#softShadow)"/>
    <text x="0" y="7" text-anchor="middle" font-size="20" font-weight="700" fill="#5b47eb" style="font-family:&apos;Pretendard&apos;,sans-serif">✦ {title}</text>
  </g>
  <!-- AI 마크 -->
  <g transform="translate(20, 20)">
    <rect x="0" y="0" width="90" height="28" rx="14" fill="#5b47eb"/>
    <text x="45" y="20" text-anchor="middle" font-size="12" font-weight="700" fill="white" letter-spacing="1.5" style="font-family:sans-serif">AI ✦ SAFEG</text>
  </g>
  <!-- 푸터 -->
  <g transform="translate(640, 920)">
    <rect x="-460" y="-22" width="920" height="40" rx="20" fill="rgba(0,0,0,0.55)"/>
    <text x="0" y="5" text-anchor="middle" font-size="13" font-weight="500" fill="white" style="font-family:&apos;Pretendard&apos;,sans-serif">{footer}</text>
  </g>
</svg>'''

def svg_to_png(svg_path, png_path, size=(1280,960)):
    """SVG → PNG 변환"""
    try:
        import cairosvg
        cairosvg.svg2png(url=svg_path, write_to=png_path, output_width=size[0], output_height=size[1])
        return True
    except ImportError: pass
    try:
        subprocess.run(['rsvg-convert','-w',str(size[0]),'-h',str(size[1]),'-o',png_path,svg_path], check=True)
        return True
    except Exception: pass
    return False

def generate_from_text(text, pair_id, scene=None, out_dir='images/_ai_recommended', verbose=True):
    """자연어 텍스트로 일러스트 생성 (메인 API)
    
    Args:
        text: 페어 정보가 담긴 자연어 텍스트
        pair_id: PAIR-XXXX 형식의 페어 ID
        scene: 강제 scene 지정 (None이면 자동 판단)
        out_dir: 출력 폴더
        verbose: 진행 메시지 출력
    
    Returns:
        dict: {'svg': '...svg', 'png': '...png', 'info': {...}, 'scene': '...'}
    """
    info = parse_pair_text(text)
    if not scene: scene = detect_scene(info)
    
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    svg_path = out / f'AI-{pair_id}.svg'
    png_path = out / f'AI-{pair_id}.png'
    
    svg = build_svg(info, pair_id, scene)
    svg_path.write_text(svg, encoding='utf-8')
    if verbose: print(f'✅ SVG 생성: {svg_path} ({len(svg):,} bytes)')
    
    if svg_to_png(str(svg_path), str(png_path)):
        if verbose: print(f'✅ PNG 변환: {png_path} ({png_path.stat().st_size:,} bytes)')
    else:
        if verbose: print(f'⚠ PNG 변환 도구 없음 (cairosvg 설치 권장)')
    
    if verbose:
        print(f'\n📋 인식된 정보:')
        for k, v in info.items():
            if v: print(f'   {k}: {v[:80]}')
        print(f'   → scene: {scene}')
    
    return {'svg': str(svg_path), 'png': str(png_path), 'info': info, 'scene': scene}

# ─────────────────────────────────────────────────────────────
# 4. CLI 진입점
# ─────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description='SAFEG-Lexia 산업안전 일러스트 생성 (자연어 입력)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
사용 예시:
  # 1) 텍스트 직접 입력 (heredoc)
  python _scripts/_generate_safety_illustration.py PAIR-0003 << 'EOF'
  위험분류 : 기계적 요인
  세부분류 : 협착위험 부분(감김,끼임)
  유해위험요인 : 지하 소방펌프실 모터 구동부 방호덮개 미설치
  감소대책 : 구동부 방호덮개 설치
  회사 : 강릉농협
  연도 : 2025
  EOF
  
  # 2) 파일 입력
  python _scripts/_generate_safety_illustration.py PAIR-0003 -f pair.txt
  
  # 3) scene 강제 지정
  python _scripts/_generate_safety_illustration.py PAIR-0003 -f pair.txt --scene mechanical
        '''
    )
    ap.add_argument('pair_id', help='페어 ID (예: PAIR-0003)')
    ap.add_argument('-f', '--file', help='페어 정보 텍스트 파일 (지정 안 하면 stdin에서 읽음)')
    ap.add_argument('--scene', choices=list(SCENE_RENDERERS.keys()), help='scene 강제 지정')
    ap.add_argument('--out-dir', default='images/_ai_recommended')
    args = ap.parse_args()
    
    # 텍스트 입력
    if args.file:
        text = Path(args.file).read_text(encoding='utf-8')
    else:
        if sys.stdin.isatty():
            print('페어 정보를 입력하세요 (입력 끝나면 Ctrl+D, Windows는 Ctrl+Z + Enter):')
        text = sys.stdin.read()
    
    if not text.strip():
        print('❌ 입력된 페어 정보가 없습니다.'); sys.exit(1)
    
    generate_from_text(text, args.pair_id, scene=args.scene, out_dir=args.out_dir)

if __name__ == '__main__':
    main()
