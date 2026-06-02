<div align="center">

<br/>

# 📝 Auto_Readme

### 코드 분석 기반 README 자동 생성기

GitHub 저장소나 업로드한 프로젝트의 소스코드를 읽어서  
README.md를 자동으로 작성해주는 웹 애플리케이션입니다.  
단순 요약이 아니라 코드를 실제로 분석해서 문서를 만드는 것을 목표로 했고,  
분석한 코드에 대해 자유롭게 질문할 수 있는 Q&A 챗봇도 함께 붙였습니다.

<br/>

![Python](https://img.shields.io/badge/Python-3.9-3776AB?style=flat-square&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_2.5_Flash-4285F4?style=flat-square&logo=google&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=flat-square&logo=langchain&logoColor=white)
![FAISS](https://img.shields.io/badge/FAISS-0467DF?style=flat-square&logo=meta&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)

<br/>

`1인 개발`  ·  Streamlit + Gemini + LangChain RAG

</div>

<br/>

---

## 📑 목차

- [✨ 주요 기능](#-주요-기능)
- [💡 만들면서 한 선택들](#-만들면서-한-선택들)
- [🛠 기술 스택](#-기술-스택)
- [📂 프로젝트 구조](#-프로젝트-구조)
- [🚀 설치 및 실행](#-설치-및-실행)
- [📖 사용 방법](#-사용-방법)
- [📄 지원 파일 형식](#-지원-파일-형식)

<br/>

---

## ✨ 주요 기능

| 기능 | 설명 |
| --- | --- |
| README 자동 생성 | GitHub URL 또는 ZIP/코드 파일을 분석해 Gemini가 README.md 작성 |
| 스타일 선택 | Standard(전문적) · Kawaii(친근) · Simple(간결) 3종 |
| 멀티모달 분석 | 실행 화면 스크린샷을 첨부하면 실행 화면 섹션을 자동 추가 |
| 코드 Q&A 챗봇 | FAISS 벡터 검색으로 코드 질의응답, 참고 파일·스니펫 표시 |
| Markdown 내보내기 | 생성된 README를 `.md` 파일로 다운로드 |

<br/>

### README 자동 생성
GitHub URL을 넣으면 GitPython으로 저장소를 클론하고, ZIP이나 개별 코드 파일을 올리면 압축을 풀어 소스를 읽습니다. 프로젝트 구조와 코드를 컨텍스트로 넣어 Gemini 2.5 Flash가 README를 작성합니다. 같은 코드라도 Standard / Kawaii / Simple 세 가지 톤 중에서 고를 수 있습니다.

### 코드 Q&A 챗봇
분석 단계에서 만든 FAISS 벡터 DB를 검색해서, "이 함수 어디서 쓰여?" 같은 질문에 관련 코드를 찾아 답합니다. 답변에 참고한 소스 파일과 코드 스니펫을 함께 보여줘서 근거를 확인할 수 있습니다.

<br/>

---

## 💡 만들면서 한 선택들

### 코드는 1000자 청크 + 200자 오버랩으로 쪼갰다

코드를 너무 잘게 쪼개면 함수 하나가 여러 청크로 흩어져 맥락이 끊기고, 너무 크게 쪼개면 검색 정확도가 떨어집니다. 여러 값을 시도한 끝에 `chunk_size=1000`, `chunk_overlap=200`으로 정착했습니다. 오버랩을 둔 건 청크 경계에 걸친 코드(함수 선언과 본문이 갈리는 지점 등)가 검색에서 누락되지 않게 하기 위해서입니다.

```python
RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
```

### FAISS 임베딩을 배치로 나눠서 쌓았다

큰 저장소를 한 번에 임베딩하면 API 한도에 걸리거나 중간에 실패했을 때 처음부터 다시 해야 합니다. 그래서 문서를 배치 단위로 나눠 FAISS에 점진적으로 쌓도록 했습니다. 대규모 코드베이스에서도 안정적으로 벡터 DB가 구축됩니다.

### 생성과 Q&A에 모델을 다르게 썼다

README 생성은 사실을 지어내면 안 되므로 `temperature=0.2`로 낮춰 코드에 근거한 출력을 유도하고, 모델도 긴 컨텍스트를 다루는 Gemini 2.5 Flash를 썼습니다. 반면 Q&A는 가볍고 빠른 응답이 중요해 1.5 Flash로 분리했습니다. 한 모델로 다 처리하기보다 용도에 맞게 나눈 선택입니다.

### 스크린샷을 넣으면 실행 화면 섹션을 자동으로 만든다

코드만으로는 "실제로 어떻게 보이는지"를 문서화하기 어렵습니다. 그래서 실행 화면 이미지를 첨부하면 Gemini의 멀티모달 입력으로 분석해서 실행 화면 설명을 README에 자동으로 끼워 넣도록 했습니다.

<br/>

---

## 🛠 기술 스택

| 분류 | 기술 |
| --- | --- |
| Frontend | Streamlit |
| AI Model | Google Gemini 2.5 Flash / 1.5 Flash |
| Framework | LangChain (Core, Community, Text Splitters) |
| Vector DB | FAISS (faiss-cpu) |
| Embedding | Google Generative AI Embeddings (`embedding-001`) |
| Git 연동 | GitPython |
| 이미지 처리 | Pillow |
| 컨테이너 | Docker (Python 3.9-slim) |

<br/>

---

## 📂 프로젝트 구조

```
Auto_Readme/
├── app.py              # Streamlit 메인 애플리케이션 (분석·생성·Q&A 전체)
├── Dockerfile          # Docker 컨테이너 설정
└── requirements.txt    # Python 의존성 목록
```

<br/>

---

## 🚀 설치 및 실행

### 사전 준비

- Python 3.9 이상
- [Google Gemini API Key](https://aistudio.google.com/apikey)

### 로컬 실행

```bash
git clone https://github.com/shimtaehun/Auto_Readme.git
cd Auto_Readme
pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 `http://localhost:8501`로 접속합니다.

### Docker 실행

```bash
docker build -t auto-readme .
docker run -p 8501:8501 auto-readme
```

<br/>

---

## 📖 사용 방법

1. 사이드바에 **Gemini API Key**를 입력합니다.
2. 분석 대상을 선택합니다.
   - **GitHub URL**: 저장소 주소와 브랜치명 입력
   - **파일 업로드**: `.zip` 또는 개별 코드 파일(.py, .js, .ts 등) 드래그 앤 드롭
3. **프로젝트 분석 시작**을 누르면 코드 분석과 벡터 DB 구축이 진행됩니다.
4. **README 생성기** 탭에서 스타일을 골라 README를 생성합니다.
5. **코드 Q&A** 탭에서 코드에 대해 자유롭게 질문합니다.

<br/>

---

## 📄 지원 파일 형식

`.py` `.js` `.ts` `.java` `.cpp` `.h` `.html` `.css` `.md` `.json` `.txt`

<br/>

---

<div align="center">

**Auto_Readme** · 1인 개발 · 코드 분석 기반 README 자동 생성기

</div>
