FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# O requirements.txt do repo está em UTF-16 (gerado no Windows): converte antes do pip
COPY requirements.txt .
RUN iconv -f UTF-16 -t UTF-8 requirements.txt | tr -d '\r' > req.txt \
    && pip install -r req.txt \
    && rm req.txt requirements.txt

COPY . .

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request as u; u.urlopen('http://localhost:8501/_stcore/health')" || exit 1

# Copia o GeoJSON do repo para data/ (o loader procura lá) e sobe o Streamlit
CMD ["sh", "-c", "mkdir -p data && cp -n assets/br_states.json data/ ; exec streamlit run app/main.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true"]
