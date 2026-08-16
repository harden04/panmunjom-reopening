# 다시 여는 판문점 — 판문점 일반견학 재개 설계 엔진

통일부가 공공데이터포털에 개방한 **판문점견학 설문 주관식 응답 4,517건**을 LLM으로 구조화 분석하여,
2023년 7월부터 중단된 판문점 일반견학이 재개될 때 무엇부터 개선해야 하는지를 데이터로 설계한 프로젝트입니다.

**대시보드**: https://harden04.github.io/panmunjom-reopening/ — 우선 개선 과제 Top 10, 연도별 추이(2024년 공백 = 중단의 기록),
일반견학기 vs 특별견학기 비교, 주제별 드릴다운, 2단 재개 설계.

## 핵심 발견

- 견학 중단(2023.7)은 데이터 공백으로 남아 있다: 2024년 응답 0건
- 재개 요구는 지배적 신호다: 주제 비중 5.1%(2021~23) → 33.3%(2025 특별견학기)
- 견학이 없어도 설문은 쌓였다: 2025년 홈페이지 설문 1,165건 = 대기 수요
- 재개 시 우선 개선 1위는 '시간 배분'(288건) — 98%가 운영 개선만으로 즉시 실행 가능
- 만족 65% / 제안 27% / 불만 8% — 경험은 자산, 결핍은 '기회'

## 방법론

1. 수집: data.go.kr 개방 데이터 4종 — 재현 스크립트 [analysis/fetch_datago.py](analysis/fetch_datago.py)
2. 전처리·비식별: 4,517행 전량 보존, 실질 응답 4,227건 선별, 실명 노출 마스킹 — [analysis/preprocess.py](analysis/preprocess.py)
3. LLM 분류: 주제 12종 × 감성 3종 × 실행 난이도 — 분류 정의서 [analysis/taxonomy.md](analysis/taxonomy.md)
4. 블라인드 검증: 독립 재분류 200건, 주제 일치율 93.5% / 감성 98.5% — [analysis/validation_report.md](analysis/validation_report.md)
5. 집계·랭킹: score = 빈도 × 불만 강도 × 실행 난이도 가중 — [analysis/aggregate.py](analysis/aggregate.py)

## 데이터 출처 및 이용허락

| 데이터셋 | 제공 | 이용허락 |
|---|---|---|
| [통일부_판문점견학 설문 주관식 응답 결과](https://www.data.go.kr/data/15150927/fileData.do) | 통일부 | 제한 없음 |
| [통일부_판문점견학 설문 응답 집계](https://www.data.go.kr/data/15150900/fileData.do) | 통일부 | 제한 없음 |
| [통일부_판문점견학 설문정보](https://www.data.go.kr/data/15150827/fileData.do) | 통일부 | 제한 없음 |
| [경기도 파주시_DMZ평화관광이용현황](https://www.data.go.kr/data/15153986/fileData.do) | 파주시 | 공공데이터포털 참조 |

- 이 저장소는 **집계 결과(data.js)만 포함**하며 원본 CSV는 재배포하지 않습니다 — 위 링크에서 직접 받을 수 있습니다.
- 대시보드의 인용문은 비식별 처리되었습니다.
- 분류에 생성형 AI(Claude)를 활용했으며, 검증 절차는 `analysis/validation_report.md`에 공개되어 있습니다.

## 라이선스

코드: MIT. 데이터: 각 원 제공기관의 이용허락 조건을 따릅니다.

---
2026년 통일부 공공데이터 활용 공모전 출품을 위해 제작된 비공식 분석입니다.
