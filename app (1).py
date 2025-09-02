# app.py - Versão Final Avançada
# Sistema de Controle de Medicamentos com cadastro, edição, exclusão, exportação, impressão e validações

import streamlit as st
import pandas as pd
import json
import os
import shutil
from datetime import datetime, date
import plotly.express as px
import base64

st.set_page_config(page_title="Controle de Medicamentos", layout="wide")

DATA_FILE = "medicamentos.json"
BACKUP_FOLDER = "backups"

# Funções principais
def init_file():
    os.makedirs(BACKUP_FOLDER, exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"medications": []}, f, ensure_ascii=False, indent=2)

def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)["medications"]
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return []

def save_data(data):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    shutil.copy(DATA_FILE, os.path.join(BACKUP_FOLDER, f"backup_{timestamp}.json"))
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"medications": data}, f, ensure_ascii=False, indent=2)

def export_csv(data):
    df = pd.DataFrame(data)
    df.to_csv("export_medicamentos.csv", index=False, encoding="utf-8-sig")
    st.success("Arquivo CSV exportado com sucesso.")

def export_excel(data):
    df = pd.DataFrame(data)
    df.to_excel("export_medicamentos.xlsx", index=False)
    st.success("Arquivo Excel exportado com sucesso.")

def generate_html_report(data):
    df = pd.DataFrame(data)
    html = df.to_html(index=False)
    b64 = base64.b64encode(html.encode()).decode()
    href = f'<a href="data:text/html;base64,{b64}" download="relatorio.html" target="_blank">📄 Baixar relatório HTML</a>'
    st.markdown(href, unsafe_allow_html=True)

# Inicialização
init_file()
data = load_data()
st.title("💊 Sistema de Controle de Medicamentos")

aba = st.sidebar.radio("Navegação", [
    "Cadastrar", "Estoque", "Previsão", "Estatísticas",
    "Exportar", "Editar/Excluir", "Imprimir"
])

# Cadastrar novo medicamento
if aba == "Cadastrar":
    with st.form("form"):
        st.subheader("Adicionar Medicamento")
        nome = st.text_input("Nome Comercial")
        marca = st.text_input("Marca")
        classe = st.text_input("Classe")
        administracao = st.text_input("Administração")
        armario = st.text_input("Armário")
        localizacao = st.text_input("Localização")
        qtd_min = st.number_input("Quantidade Mínima", min_value=0)
        qtd_max = st.number_input("Quantidade Máxima", min_value=0)
        uso_diario = st.number_input("Uso Diário", min_value=0.0, step=0.5)
        validade = st.date_input("Validade do Lote")
        lote_qtd = st.number_input("Quantidade do Lote", min_value=0)

        if st.form_submit_button("Salvar Medicamento"):
            if not nome:
                st.warning("Preencha o nome do medicamento.")
                st.stop()
            if uso_diario <= 0 or lote_qtd <= 0:
                st.warning("Preencha uma quantidade e uso diário válidos.")
                st.stop()
            if any(m["nome_comercial"].lower().strip() == nome.lower().strip() for m in data):
                st.warning("Este medicamento já está cadastrado.")
                st.stop()

            novo = {
                "id": datetime.now().isoformat(),
                "nome_comercial": nome,
                "marca": marca,
                "classe": classe,
                "administracao": administracao,
                "armario": armario,
                "localizacao": localizacao,
                "qtd_minima": qtd_min,
                "qtd_maxima": qtd_max,
                "uso_diario": uso_diario,
                "validade": validade.strftime("%Y-%m-%d"),
                "estoque": lote_qtd,
                "created_at": datetime.now().isoformat()
            }
            data.append(novo)
            save_data(data)
            st.success("Medicamento salvo com sucesso!")

# Visualizar Estoque
elif aba == "Estoque":
    st.subheader("📦 Estoque Atual")
    if data:
        df = pd.DataFrame(data)
        df["validade"] = pd.to_datetime(df["validade"], errors="coerce")
        df["dias_para_validade"] = (df["validade"] - pd.to_datetime(date.today())).dt.days
        df["status"] = df["dias_para_validade"].apply(
            lambda x: "🔴 Vencido" if x < 0 else ("🟠 Em breve" if x <= 30 else "🟢 Ok")
        )
        st.dataframe(df[["nome_comercial", "estoque", "uso_diario", "dias_para_validade", "status"]])
    else:
        st.info("Nenhum medicamento cadastrado.")

# Previsão de Consumo
elif aba == "Previsão":
    st.subheader("📉 Previsão de Consumo")
    if data:
        forecast = []
        for med in data:
            if med["uso_diario"] > 0:
                dias = round(med["estoque"] / med["uso_diario"], 1)
            else:
                dias = "N/A"
            forecast.append({"nome": med["nome_comercial"], "dias_restantes": dias})
        df = pd.DataFrame(forecast)
        fig = px.bar(df, x="nome", y="dias_restantes", text="dias_restantes",
                     labels={"nome": "Medicamento", "dias_restantes": "Dias restantes"})
        st.plotly_chart(fig)
    else:
        st.info("Nenhum dado disponível.")

# Estatísticas
elif aba == "Estatísticas":
    st.subheader("📊 Estatísticas")
    if data:
        df = pd.DataFrame(data)
        st.metric("Total de Medicamentos", len(df))
        classe_count = df["classe"].value_counts()
        st.bar_chart(classe_count)
    else:
        st.info("Nada para mostrar.")

# Exportar dados
elif aba == "Exportar":
    st.subheader("📁 Exportar Dados")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Exportar CSV"):
            export_csv(data)
    with col2:
        if st.button("Exportar Excel"):
            export_excel(data)

# Editar ou Excluir Medicamentos
elif aba == "Editar/Excluir":
    st.subheader("✏️ Editar ou Excluir Medicamentos")
    if data:
        nomes = [med["nome_comercial"] for med in data]
        escolha = st.selectbox("Escolha o medicamento", nomes)
        med = next((m for m in data if m["nome_comercial"] == escolha), None)
        if med:
            if st.button("Excluir medicamento"):
                data = [m for m in data if m["id"] != med["id"]]
                save_data(data)
                st.success("Medicamento excluído com sucesso.")
                st.experimental_rerun()
            with st.form("edit_form"):
                med["estoque"] = st.number_input("Estoque atual", value=med["estoque"], min_value=0)
                med["uso_diario"] = st.number_input("Uso diário", value=med["uso_diario"], min_value=0.0)
                nova_validade = st.date_input("Nova validade", value=pd.to_datetime(med["validade"]))
                if st.form_submit_button("Salvar alterações"):
                    med["validade"] = nova_validade.strftime("%Y-%m-%d")
                    save_data(data)
                    st.success("Alterações salvas.")

# Imprimir HTML
elif aba == "Imprimir":
    st.subheader("🖨️ Relatório HTML para impressão")
    if data:
        generate_html_report(data)
    else:
        st.info("Nada para imprimir.")
