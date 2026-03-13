# 🤖 Auto_Readme

**AI를 활용하여 GitHub 저장소 또는 업로드된 프로젝트의 README.md를 자동으로 생성해주는 웹 애플리케이션**

Google Gemini API와 LangChain 기반의 RAG(Retrieval-Augmented Generation) 파이프라인을 통해 소스코드를 분석하고, 전문적인 README 문서를 자동으로 작성합니다. 추가로 코드에 대한 자유로운 질의응답(Q&A) 챗봇 기능도 제공합니다.

---

## 📌 주요 기능

### 1. README 자동 생성 (Long-Context)
- GitHub URL 또는 ZIP/코드 파일 업로드를 통해 프로젝트를 분석
- Gemini 2.5 Flash 모델이 프로젝트 구조와 소스코드를 읽고 README.md를 자동 작성
- 3가지 스타일 선택 가능: **Standard** (전문적), **Kawaii** (친근한 이모지), **Simple** (간결)
- 실행 화면 스크린샷 첨부 시 멀티모달 분석을 통해 실행 화면 섹션 자동 추가
- 생성된 README를 Markdown 파일로 다운로드

### 2. 코드 Q&A 챗봇 (Vector RAG)
- FAISS 벡터 데이터베이스 기반의 코드 검색 및 질의응답
- 대규모 코드베이스에서도 관련 코드를 정확히 찾아 답변
- 참고한 소스 파일과 코드 스니펫을 함께 표시

---

## 🗂️ 프로젝트 구조

```
Auto_Readme/
├── 📄 app.py              # Streamlit 메인 애플리케이션
├── 📄 Dockerfile           # Docker 컨테이너 설정
└── 📄 requirements.txt     # Python 의존성 목록
```

---

## 🛠️ 기술 스택

| 분류 | 기술 |
|------|------|
| **Frontend** | Streamlit |
| **AI Model** | Google Gemini 2.5 Flash / 1.5 Flash |
| **Framework** | LangChain (Core, Community, Text Splitters) |
| **Vector DB** | FAISS (faiss-cpu) |
| **Embedding** | Google Generative AI Embeddings |
| **Git 연동** | GitPython |
| **이미지 처리** | Pillow |
| **컨테이너** | Docker (Python 3.9-slim) |

---

## ⚙️ 설치 및 실행 방법

### 사전 준비

- Python 3.9 이상
- [Google Gemini API Key](https://aistudio.google.com/apikey) 발급

### 로컬 실행

```bash
# 1. 저장소 클론
git clone https://github.com/shimtaehun/Auto_Readme.git
cd Auto_Readme

# 2. 의존성 설치
pip install -r requirements.txt

# 3. Streamlit 실행
streamlit run app.py
```

브라우저에서 `http://localhost:8501`로 접속합니다.

### Docker 실행

```bash
# 1. 이미지 빌드
docker build -t auto-readme .

# 2. 컨테이너 실행
docker run -p 8501:8501 auto-readme
```

---

## 🚀 사용 방법

1. 사이드바에 **Gemini API Key**를 입력합니다.
2. 분석 대상을 선택합니다.
   - **GitHub URL**: 저장소 주소와 브랜치명을 입력
   - **파일 업로드**: `.zip` 파일 또는 개별 코드 파일(.py, .js, .ts 등)을 드래그 앤 드롭
3. **프로젝트 분석 시작** 버튼을 클릭하면 코드 분석과 벡터 DB 구축이 진행됩니다.
4. **README 생성기** 탭에서 스타일을 선택하고 README를 생성합니다.
5. **코드 Q&A** 탭에서 코드에 대한 자유로운 질문을 할 수 있습니다.

---

## 📎 지원 파일 형식

분석 대상으로 인식되는 파일 확장자:

`.py` `.js` `.ts` `.java` `.cpp` `.h` `.html` `.css` `.md` `.json` `.txt`

---

## 📄 License

이 프로젝트는 별도의 라이선스가 명시되어 있지 않습니다. 사용 전 저작자에게 문의해 주세요.
