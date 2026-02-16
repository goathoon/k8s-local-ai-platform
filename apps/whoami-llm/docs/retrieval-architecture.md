# whoami-llm Retrieval Architecture

`whoami-llm`는 기본적으로 FAISS 기반 semantic retrieval을 사용합니다.  
다만 "이 개발자는 어떤 생각을 가지고 있는가?" 같은 성향/철학형 질문은 단일 유사도 검색만으로는 근거가 편향되기 쉬워, `auto`/`persona` 모드에서 보강 전략을 적용합니다.

## 목표

- 단일 주제 유사 청크 반복을 줄인다.
- 의사결정/회고/트레이드오프 문장을 더 잘 회수한다.
- LLM이 "개발자 프로필"을 추론할 때 필요한 다각도 근거를 확보한다.

## Retrieval Modes

- `semantic`
  - 기존 방식. 질의 1개를 임베딩해 top-k 반환.
  - 키워드성/사실성 질의에 유리.
- `auto`
  - 질의 패턴을 보고 성향형 질문이면 `persona` 로직 사용.
  - 그 외에는 `semantic` 사용.
- `persona`
  - 성향/철학/의사결정 질문용 로직을 강제 적용.

## Persona Retrieval Pipeline

1. 질의 확장 (query expansion)
- 원 질의에 아래 관점 suffix를 추가해 다중 질의 생성
- 예: `가치관 원칙`, `왜 그렇게 설계했는지`, `트레이드오프 의사결정`, `회고 배운 점 실수`, `협업 테스트 운영 관점`

2. 다중 검색
- 확장된 각 질의를 동일 임베딩 모델로 인코딩
- 각 질의별로 FAISS top-N 후보를 검색

3. RRF 융합
- Reciprocal Rank Fusion으로 질의별 랭킹을 통합
- 하나의 질의에서만 높게 나온 문서 편향을 완화

4. 회고성 단서 가중치
- 제목/본문에 `왜`, `교훈`, `실수`, `트레이드오프`, `판단` 등 단서가 있으면 소폭 보정
- 본 유사도보다 과도하게 앞서지 않도록 상한을 둠

5. MMR 다양성 선택
- 최종 top-k를 고를 때 문서 간 중복도를 패널티로 반영
- 비슷한 청크 반복 대신 서로 다른 맥락 근거를 우선 선택

## 코드 위치

- 핵심 구현: `apps/whoami-llm/src/whoami_llm/search/faiss_searcher.py`
- CLI 옵션 노출: `apps/whoami-llm/src/whoami_llm/cli.py`

## 사용 예시

```bash
whoami-llm rag "이 개발자는 어떤 생각을 가지고 있는가?" \
  --blog https://velog.io/@<username>/posts \
  --retrieval-mode auto \
  --top-k 8
```

```bash
whoami-llm search "이 개발자의 의사결정 스타일은?" \
  --blog https://velog.io/@<username>/posts \
  --retrieval-mode persona \
  --top-k 8
```

## 튜닝 포인트

- `top-k`
  - 너무 작으면 관점 다양성 부족, 너무 크면 프롬프트 노이즈 증가
- `candidate_k` (코드 파라미터)
  - Persona 후보 풀 크기
- `diversity_lambda` (코드 파라미터)
  - MMR에서 관련도 vs 다양성 균형

## 알려진 한계

- RSS description 본문 품질에 크게 의존한다.
- 회고성 단서 키워드는 언어/표현 습관에 따라 민감도가 달라진다.
- persona 모드는 semantic-only 대비 계산량이 증가한다.

## 검증 권장 방식

같은 질의로 아래 2개를 비교:

1. `--retrieval-mode semantic`
2. `--retrieval-mode auto`

비교 기준:
- 근거 문맥의 다양성
- 성향/판단 관련 문장 포함률
- 최종 답변의 "근거 기반 추론" 품질
