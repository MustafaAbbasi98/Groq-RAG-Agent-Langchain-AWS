import os
import streamlit as st
import boto3
import requests

# 1️⃣ Environment
S3_BUCKET = os.environ["S3_BUCKET_NAME"]
API_URL    = os.environ["API_URL"]  # e.g. https://<API_ID>.execute-api…/prod

# 2️⃣ AWS client
s3 = boto3.client("s3")

st.title("📚 Groq RAG Agent UI")

# 3️⃣ Upload new PDF
uploaded = st.file_uploader("Upload a PDF", type=["pdf"])
if uploaded:
    key = uploaded.name
    s3.upload_fileobj(uploaded, S3_BUCKET, key)
    st.success(f"Uploaded `{key}`")

# 4️⃣ List existing PDFs
objs = s3.list_objects_v2(Bucket=S3_BUCKET).get("Contents", [])
pdf_keys = [o["Key"] for o in objs]
selected = st.selectbox("Choose a PDF", pdf_keys)

# 5️⃣ Ask a question
query = st.text_input("Your question")
if st.button("Ask your question"):
    with st.spinner("Fetching answer..."):
        if not query:
            st.error("Please enter a question.")
        else:
            payload = {"s3_key": selected, "query": query}
            res = requests.post(f"{API_URL}/query", json=payload)
            if res.status_code == 200:
                ans = res.json().get("answer", "")
                st.info("**Answer:** \n\n" + ans)
                # st.write(ans)
            else:
                st.error(f"Error {res.status_code}: {res.text}")

with st.expander("View Tips and Instructions"):
    
    st.markdown("""
                Instructions:
                                
                • Upload your PDF (research) document you want to chat with.
                
                • Select the PDF you want to chat with from the dropdown.
                
                • Type your query and click "Ask your question" to obtain a response from the LLM.
                
                Tips:
                
                • The LLM has access to wikipedia, a calculator and your PDF document.
                
                • If the LLM fails to respond, guide it by telling it what tool to use. Use a phrase like "You MUST do research"
                
                • Try to frame your queries as questions.
                
                • Avoid using punctuation marks at end of sentences. For some reason, it can mess up the LLM.
                
                • Avoid queries that require multi-step reasoning or multi-step tool usage.        
                
                • If you still want multi-step/tool reasoning try appending the following phrase at the end of your query:
                "You MUST think step-by-step"
                
                """
                )