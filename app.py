import streamlit as st
import tempfile
import os
import base64
import time 
import zipfile
from PIL import Image
from io import BytesIO


# LangChain & AI 관련 임포트
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain_community.document_loaders import GitLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document 

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="AI Dev Assistant", page_icon="🤖", layout="wide")
st.title("코드 분석과 README 생성기")

# 세션 상태 초기화 (데이터 유지용)
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "raw_documents" not in st.session_state:
    st.session_state.raw_documents = None
if "tree_structure" not in st.session_state:
    st.session_state.tree_structure = ""
if "repo_name" not in st.session_state:
    st.session_state.repo_name = ""

# --- 2. 유틸리티 함수 ---
def generate_tree_structure(path):
    """폴더 구조를 문자열 트리로 변환"""
    tree = []
    for root, dirs, files in os.walk(path):
        # .git 등 숨김 폴더 제외
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        level = root.replace(path, '').count(os.sep)
        indent = ' ' * 4 * (level)
        tree.append(f"{indent} {os.path.basename(root)}/")
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            if f.endswith(('.py', '.js', '.ts', '.java', '.md', '.html', '.css', '.json')):
                tree.append(f"{subindent}📄 {f}")
    return "\n".join(tree)

# [추가된 함수] 폴더에서 파일을 직접 읽어오는 함수 (ZIP 파일용)
def load_documents_from_folder(folder_path):
    documents = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            # 분석할 파일 확장자 필터링
            if file.endswith(('.py', '.js', '.ts', '.java', '.md', '.html', '.css', '.json', '.cpp', '.h')):
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        # 메타데이터에 상대 경로 저장
                        rel_path = os.path.relpath(full_path, folder_path)
                        documents.append(Document(page_content=content, metadata={"source": rel_path}))
                except Exception:
                    pass 
    return documents

def encode_image(image):
    """이미지를 Base64로 인코딩"""
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# --- 3. 사이드바 (설정 및 분석) ---
with st.sidebar:
    st.header("프로젝트 설정")
    gemini_api_key = st.text_input("Gemini API Key", type="password")
    
    st.divider()
    
    # 1. 데이터 소스 선택
    data_source = st.radio("분석 대상 선택", ("GitHub URL", "파일 업로드 (Zip 또는 코드)"), horizontal=True)
    
    repo_url = ""
    uploaded_files = [] # 여러 파일을 받기 위해 리스트로 초기화
    branch = "main"

    # 2. 입력 UI 표시
    if data_source == "GitHub URL":
        repo_url = st.text_input("GitHub URL", placeholder="https://github.com/username/repo")
        branch = st.text_input("Branch", value="main")
    else:
        # [NEW] 여러 파일 업로드 가능 + 다양한 확장자 지원
        uploaded_files = st.file_uploader(
            "파일을 드래그해서 놓으세요 (.zip, .py, .js 등)", 
            accept_multiple_files=True, 
            type=['zip', 'py', 'js', 'ts', 'java', 'cpp', 'h', 'html', 'css', 'md', 'json', 'txt']
        )
        if uploaded_files:
            st.info(f"총 {len(uploaded_files)}개 파일 선택됨")

    st.divider()
    
    analyze_btn = st.button("프로젝트 분석 시작", type="primary")
    
    if analyze_btn:
        # 유효성 검사
        if not gemini_api_key:
            st.error("Gemini API Key를 입력해주세요!")
        elif data_source == "GitHub URL" and not repo_url:
            st.error("GitHub URL을 입력해주세요!")
        elif data_source == "파일 업로드 (Zip 또는 코드)" and not uploaded_files:
            st.error("파일을 업로드해주세요!")
        else:
            with st.spinner("프로젝트 분석 중..."):
                try:
                    with tempfile.TemporaryDirectory() as temp_dir:
                        documents = []
                        
                        # Case A: GitHub 클론
                        if data_source == "GitHub URL":
                            st.info("GitHub에서 클론 중")
                            loader = GitLoader(
                                clone_url=repo_url,
                                repo_path=temp_dir,
                                branch=branch,
                                file_filter=lambda x: x.endswith((".py", ".js", ".ts", ".java", ".md", ".html", ".css"))
                            )
                            documents = loader.load()
                            st.session_state.repo_name = repo_url.split("/")[-1]

                        # Case B: 파일 업로드 (Zip 또는 낱개 파일)
                        else:
                            st.info("파일 처리 중")
                            st.session_state.repo_name = "Uploaded_Project"
                            
                            for uploaded_file in uploaded_files:
                                # 1. Zip 파일인 경우 -> 압축 해제
                                if uploaded_file.name.endswith(".zip"):
                                    with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
                                        zip_ref.extractall(temp_dir)
                                
                                # 2. 일반 코드 파일인 경우 -> 임시 폴더에 저장
                                else:
                                    # 파일을 임시 폴더에 씁니다.
                                    file_path = os.path.join(temp_dir, uploaded_file.name)
                                    with open(file_path, "wb") as f:
                                        f.write(uploaded_file.getbuffer())

                            # 폴더에 저장된 파일들을 다시 읽어들임 (트리 구조 및 분석용)
                            documents = load_documents_from_folder(temp_dir)

                        # --- 공통 로직 (분석 및 저장) ---
                        if not documents:
                            st.warning("분석할 수 있는 코드 파일이 없습니다.")
                        else:
                            # 트리 생성
                            tree_str = generate_tree_structure(temp_dir)
                            st.session_state.tree_structure = tree_str
                            st.session_state.raw_documents = documents

                            # 벡터 DB 구축
                            with st.spinner("벡터 데이터베이스 구축 중..."):
                                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                                splits = text_splitter.split_documents(documents)
                                
                                embeddings = GoogleGenerativeAIEmbeddings(
                                    model="models/embedding-001", 
                                    google_api_key=gemini_api_key
                                )
                                batch_size = 10
                                vectorstore = None
                            
                                progress_bar = st.progress(0) # 진행률 표시
                                
                                for i in range(0, len(splits), batch_size):
                                    batch = splits[i:i+batch_size]
                                    
                                    if vectorstore is None:
                                        vectorstore = FAISS.from_documents(documents=batch, embedding=embeddings)
                                    else:
                                        vectorstore.add_documents(batch)
                                    
                                    # 진행률 업데이트
                                    progress = min((i + batch_size) / len(splits), 1.0)
                                    progress_bar.progress(progress)
                                    
                                    # 구글 무료 티어 제한을 피하기 위해 1초 대기
                                    time.sleep(1.5) 
                                
                                st.session_state.vector_store = vectorstore
                        
                except Exception as e:
                    st.error(f"분석 중 오류 발생: {e}")

# --- 4. 메인 기능 탭 ---
tab1, tab2 = st.tabs(["README 생성기 (Long-Context)", "코드 Q&A (Vector RAG)"])

# === TAB 1: README 생성 ===
with tab1:
    st.subheader("README 자동 생성")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        style_option = st.radio("스타일 선택", ("Standard", "Kawaii", "Simple"), horizontal=True)
    with col2:
        uploaded_image = st.file_uploader("실행 화면 스크린샷 (선택)", type=["png", "jpg"])

    if st.button("README 작성하기"):
        if st.session_state.raw_documents:
            with st.spinner("AI가 프로젝트 전체를 읽고 있습니다..."):
                try:
                    # Gemini 1.5 Flash 호출
                    llm = ChatGoogleGenerativeAI(
                        model="gemini-2.5-flash", 
                        temperature=0.2, 
                        google_api_key=gemini_api_key
                    )
                    
                    # 프롬프트 구성
                    prompt_styles = {
                        "Standard": "전문적이고 신뢰감 있는 톤",
                        "Kawaii": "이모지 가득하고 친절한 톤",
                        "Simple": "핵심만 간결하게"
                    }
                    
                    # Context 조립 (트리 구조 + 코드)
                    context_text = f"## Project Structure\n```\n{st.session_state.tree_structure}\n```\n\n## Source Code\n"
                    # 토큰 절약을 위해 상위 15개 파일만 예시로 사용 (필요시 조절 가능)
                    for doc in st.session_state.raw_documents[:15]:
                        context_text += f"\nFile: {doc.metadata['source']}\n{doc.page_content[:3000]}\n"
                    
                    system_prompt = f"""
                    당신은 전문 테크니컬 라이터입니다.
                    제공된 [프로젝트 구조]와 [소스코드]를 분석하여 README.md를 작성하세요.
                    
                    [스타일]
                    {prompt_styles[style_option]}
                    
                    [필수 섹션]
                    1. 프로젝트 제목 및 한 줄 요약
                    2. 폴더 구조 (제공된 트리 구조 사용 필수)
                    3. 주요 기능
                    4. 기술 스택 (Shields.io 배지 사용)
                    5. 설치 및 실행 방법
                    
                    (이미지가 제공되었다면 '실행 화면' 섹션 추가하여 설명)
                    """
                    
                    # 멀티모달 메시지 구성
                    content_parts = [{"type": "text", "text": f"{system_prompt}\n\n[CONTEXT]\n{context_text}"}]
                    
                    if uploaded_image:
                        img_base64 = encode_image(Image.open(uploaded_image))
                        content_parts.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}})
                    
                    response = llm.invoke([HumanMessage(content=content_parts)])
                    
                    st.markdown("### 생성 결과")
                    st.markdown(response.content)
                    st.download_button("Markdown 다운로드", response.content, file_name="README.md")
                    
                except Exception as e:
                    st.error(f"생성 실패: {e}")
        else:
            st.info("사이드바에서 '프로젝트 분석 시작' 버튼을 먼저 눌러주세요!")

# === TAB 2: 코드 Q&A ===
with tab2:
    st.subheader("코드 질문 챗봇")
    st.caption("벡터 DB를 통해 방대한 코드 속에서 정확한 답변을 찾아줍니다.")
    
    # 채팅 메시지 기록 (UI용)
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "코드에 대해 무엇이든 물어보세요! (예: main 함수는 어디 있어?)"}]

    # 이전 대화 출력
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    # 사용자 입력 처리
    if prompt := st.chat_input():
        if not st.session_state.vector_store:
            st.error("먼저 프로젝트를 분석해야 합니다!")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)

            with st.spinner("코드 검색 중..."):
                llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=gemini_api_key)
                
                # RAG 체인 생성
                retriever = st.session_state.vector_store.as_retriever()
                qa_prompt = ChatPromptTemplate.from_template("""
                아래 제공된 코드 문맥(Context)을 바탕으로 질문에 답하세요.
                코드를 인용해서 설명하면 더 좋습니다.
                
                <context>
                {context}
                </context>
                
                질문: {input}
                """)
                
                document_chain = create_stuff_documents_chain(llm, qa_prompt)
                retrieval_chain = create_retrieval_chain(retriever, document_chain)
                
                response = retrieval_chain.invoke({"input": prompt})
                answer = response["answer"]
                
                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.chat_message("assistant").write(answer)
                
                # 근거 문서(Source) 보여주기
                with st.expander("참고한 코드 파일 보기"):
                    for doc in response["context"]:
                        st.write(f"📄 **{doc.metadata['source']}**")
                        st.code(doc.page_content[:500] + "...")