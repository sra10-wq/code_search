# ---- stage 1: build the React frontend ----
FROM node:22-slim AS frontend
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ---- stage 2: FastAPI app that also serves the built frontend ----
FROM python:3.12-slim
WORKDIR /app
ENV HF_HOME=/app/hf_cache
# CPU-only PyTorch keeps the image ~2 GB smaller than the default CUDA build
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt
# bake the embedding model into the image so startup needs no download
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
COPY backend backend
COPY --from=frontend /frontend/dist frontend/dist
RUN chmod -R 777 /app
ENV HF_HUB_OFFLINE=1
EXPOSE 7860
# index files are mounted at runtime: docker run -v /opt/code-search/data:/app/data ...
CMD ["python", "-m", "uvicorn", "app:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "7860"]
