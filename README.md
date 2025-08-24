# Bank Transaction Analyzer

이 프로젝트는 카카오뱅크 거래내역 CSV 파일을 불러와서 일별 입출금 내역과 누적 통계를 Streamlit 앱으로 보여주는 도구입니다.

## 사용법

### 1. 데이터 준비
1. **카카오뱅크 앱/웹**에서 거래내역을 다운로드합니다.  
2. 다운로드한 **엑셀 파일**을 열어, 거래내역이 있는 행과 열만 선택하여 `.csv` 파일로 내보냅니다.  
   - 인코딩은 `UTF-8` 혹은 `UTF-8-SIG`로 저장하는 것을 권장합니다.  
3. 내보낸 `.csv` 파일을 **프로젝트 루트 폴더**에 `bank.csv` 이름으로 저장합니다.  

### 2. 실행하기
```bash
# 가상환경 활성화 (필요시)
conda activate <your_env>

# Streamlit 앱 실행
streamlit run app.py
```

실행하면 터미널에 아래와 같이 주소가 출력됩니다:
```
Local URL: http://localhost:8501
Network URL: http://<IP>:8501
```
브라우저에서 해당 주소로 접속하면 앱이 열립니다.

### 3. 앱 기능
- 거래내역을 불러와 Pandas로 전처리합니다.
- `deposit`, `withdraw`, `net` (순이익), `last_balance` (일별 잔고) 등을 계산합니다.
- 내부이체(본인 이름 포함)는 자동으로 `is_internal`로 표시합니다.
- 일자별 누적 입출금 및 요약을 확인할 수 있습니다.

### 4. 데이터 가공법 (전처리 과정)
- 요약
1. 카카오뱅크 에서 거래내역 다운로드 하기
2. 엑셀을 열어, 거래내역이 있는 행과 열만 뽑아 .csv 로 내보내기
3. 프로젝트 파일 위치에 넣기

- `datetime`: 문자열을 `YYYY.MM.DD HH:MM:SS` 형식으로 변환 → 날짜와 시간 파싱
- `amount`, `balance`: 콤마 제거 후 숫자로 변환, 결측치는 0으로 채움
- `deposit`: 양수 금액
- `withdraw`: 음수 금액의 절댓값
- 일별 합계 및 누적치 계산
- 각 거래내역에 대해 `[SELF]` 태그로 내부이체 여부 표시

---

## 필요 패키지
- pandas
- streamlit
- pathlib

## 추가 팁
- MacOS에서 `watchdog` 모듈을 설치하면 Streamlit 핫리로드 속도가 개선됩니다:
```bash
pip install watchdog
```

