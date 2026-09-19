# 🛣️ Análise Exploratória e Clusterização de Acidentes nas Rodovias Federais (PRF)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28-red?style=for-the-badge&logo=streamlit)

## 📌 Sobre o Projeto
Este projeto analisa os dados públicos de acidentes de trânsito disponibilizados pela **Polícia Rodoviária Federal (PRF)**. 
O objetivo principal é realizar uma **Análise Exploratória de Dados (EDA)** detalhada e aplicar técnicas de **Clusterização Geográfica** para identificar trechos e pontos críticos de alta periculosidade nas rodovias brasileiras.

---

## 🎯 Objetivos
- Identificar padrões temporais, causas principais e severidade dos acidentes.
- Disponibilizar um **Dashboard Interativo em Streamlit** para exploração dos resultados em mapas e gráficos.

---

## 📂 Estrutura do Repositório
```text
├── data/           # Instruções de download (dados armazenados no Google Drive)
├── notebooks/      # Análises exploratórias e protótipos em Google Colab
├── src/            # Módulos reutilizáveis de limpeza e clusterização
└── app/            # Aplicação interativa em Streamlit
```

---

## 🛠️ Como Executar o Projeto Localmente

### 1. Clonar o repositório
```bash
git clone [https://github.com/SEU-USUARIO/nome-do-repositorio.git](https://github.com/SEU-USUARIO/nome-do-repositorio.git)
cd nome-do-repositorio
```

### 2. Criar e ativar o ambiente virtual
```bash
python -m venv venv
# Linux/Mac
source venv/bin/activate
# Windows
venv\Scripts\activate
```

### 3. Instalar as dependências
```bash
pip install -r requirements.txt
```

### 4. Executar o Dashboard Streamlit
```bash
streamlit run app/main.py
```

---

## 👥 Equipe do Projeto
- **[Felipe Galindo]** - *FUNÇÃO*
- **[Nome Integrante 2]** - *FUNÇÃO*
- **[Nome Integrante 3]** - *FUNÇÃO*
- **[Nome Integrante 4]** - *FUNÇÃO*