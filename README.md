# 인천굿데이마사지 (인천 출장마사지·홈타이)

인천 전지역 방문 건강관리(마사지·홈타이) 예약 안내 정적 웹사이트입니다.
순수 HTML + 인라인 CSS/JS로 구성되어 **런타임 의존성이 0개**이며, 빌드 없이 그대로 배포할 수 있습니다.
지역 SEO 블루프린트(다크 럭스 디자인 · 전용 페이지 링크아웃 · 도어웨이 회피)를 인천 구조에 맞게 이식했습니다.

- 예약전화: **0508-202-4743**
- 현재 인천 **2군·8구** 기준으로 제작했으며, **2026-07-01** 제물포구·영종구·검단구 출범(2군·9구)에 맞춘 메뉴/리다이렉트 전환을 준비합니다.

## 사이트 구조 (총 226페이지)

```
/                                홈 (허브)
/incheon/                        인천 출장마사지·홈타이 대표 랜딩 (핵심 키워드)
/incheon/hometai/                인천 홈타이 안내
/incheon/area/                   지역별 안내 (허브)
/incheon/<구·군>/                 10개 구·군 페이지
/incheon/<구·군>/<대표동>/         83개 대표 동 페이지
/incheon/stations/               지하철역별 안내 (허브)
/incheon/stations/<노선>/         6개 노선 페이지
/incheon/stations/<역>/           86개 역 상세 페이지 (환승역은 단일 URL)
/incheon/hours| checklist| safety| faq/   인천 공통 안내 (링크아웃 대상)
/theme/  /theme/<테마>/            테마 허브 + 14개 테마
/course/ /course/<코스>/           코스 허브 + 8개 코스(피로회복·아로마·스포츠·홈타이·커플가족·기업단체·가격·가이드)
/reservation/ /guide/ /reviews/ /customer/ /about/
/privacy/ /terms/ /youth/         정책 3종
sitemap.xml  robots.txt  site.webmanifest  favicon.svg  <KEY>.txt
```

### 도어웨이·중복 방지 규칙 (적용 완료)
- **지역+역+테마 조합 페이지 생성 안 함** — 테마는 단독 페이지로만 운영.
- **역 1개당 1페이지** — 환승역(부평·주안·인천시청·계양·검암·원인재·부평구청·석남·인천)은 단일 URL.
- **대표 동 1개당 1페이지** — 주안1~8동→주안동, 송도1~5동→송도동 등 숫자 행정동은 대표 동으로 통합.
- 출구별/“추천·24시·근처” 조합 페이지 없음. 푸터에 지역명·역명 대량 나열 안 함.
- 동·역 페이지는 슬러그 기반 **결정적 변형**(문장 풀·주력 테마·링크 순서 셔플)으로 본문을 차별화.
- 공통 정보(예약시간·준비물·위생·요금)는 본문 반복 대신 전용 페이지로 **링크아웃**.

### 품질 점검 결과 (`python3 tools/build.py` 후)
- 동 페이지 4-gram 유사도: 평균 ~25% / 최대 ~37%
- 역 페이지 4-gram 유사도: 평균 ~28% / 최대 ~40% (목표 40% 이하 충족)
- title·description **100% 고유**, JSON-LD 파싱 오류 0, 깨진 내부 링크 0.
- **얇은 콘텐츠 자동 noindex**: 본문이 짧은 유틸리티/정책 페이지(약관·개인정보·1:1문의 등)는
  robots `noindex,follow` 처리 + sitemap 제외. 핵심 콘텐츠 페이지(지역·동·역·테마·코스)는 모두 색인.
  (임계값은 `tools/build.py`의 `THIN_THRESHOLD`. 2,000자 규칙을 엄격히 강제하려면 2000으로 올리세요.)

## 빌드 (선택)

배포에는 빌드가 필요 없습니다. 공통 헤더/푸터/SEO/데이터를 일괄 수정할 때만 사용합니다.

```bash
python3 tools/build.py      # 모든 HTML + sitemap/robots/manifest + IndexNow 키 파일 생성
python3 tools/gen_icons.py  # 파비콘 / PWA 아이콘 / OG 이미지 생성 (Pillow 필요)
```

## 배포 전 교체할 항목 (`tools/build.py` 상단 상수)

| 상수 | 현재 값 | 비고 |
|---|---|---|
| `BASE_URL` | `https://incheon-swedish-massage.pages.dev` | 실제 배포 도메인으로 교체 |
| `BRAND` / `PHONE_DISP` | 인천굿데이마사지 / 0508-202-4743 | 확정값 |
| `COMPANY` (대표·사업자번호·주소·통신판매신고·개인정보책임자) | **플레이스홀더(`OOO`, `000-00-00000`)** | 실제 정보로 교체 |
| `INDEXNOW_KEY` | 32자리 키 | 도메인 변경 시 새로 생성 권장 |

> ⚠️ `COMPANY`의 사업자 정보는 플레이스홀더입니다. 실제 사업자 정보가 확정되기 전까지
> 푸터·`LocalBusiness` 스키마에 노출되며, 허위 후기 구조화 데이터(aggregateRating)는 넣지 않았습니다.

## 색인 즉시 통보 (IndexNow)

- 인증 키 파일은 빌드 시 루트에 자동 생성됩니다(`<KEY>.txt`).
- 수동 제출: `python3 tools/indexnow.py --all | --changed | <URL> [--dry-run]`
- `.github/workflows/indexnow.yml`: `main` 푸시(페이지/사이트맵 변경) 시 자동 제출.
- 네이버 서치어드바이저 + Bing 웹마스터에 사이트 등록 및 sitemap 1회 제출, Google Search Console 등록 권장.
