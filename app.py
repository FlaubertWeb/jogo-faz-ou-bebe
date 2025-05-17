from flask import Flask, render_template, request, redirect, url_for, session
import json
import random
import os

app = Flask(__name__)
app.secret_key = '4f3c6f529ec43e2f8a8f8a2b4e531d5f'  # Altere para uma chave segura em produção

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JOGADORES_FILE = os.path.join(BASE_DIR, "jogadores.json")
PRENDAS_FILE = os.path.join(BASE_DIR, "prendas.json")
CATEGORIAS_FILE = os.path.join(BASE_DIR, "categorias.json")

# ----------------- UTILITÁRIOS ------------------

def carregar_jogadores():
    if not os.path.exists(JOGADORES_FILE):
        with open(JOGADORES_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)
    with open(JOGADORES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_jogador(jogador):
    jogadores = carregar_jogadores()
    jogadores.append(jogador)
    with open(JOGADORES_FILE, "w", encoding="utf-8") as f:
        json.dump(jogadores, f, ensure_ascii=False, indent=4)

def carregar_prendas():
    if not os.path.exists(PRENDAS_FILE):
        with open(PRENDAS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)
    with open(PRENDAS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_prenda(prenda):
    prendas = carregar_prendas()
    prendas.append(prenda)
    with open(PRENDAS_FILE, "w", encoding="utf-8") as f:
        json.dump(prendas, f, ensure_ascii=False, indent=4)

def carregar_categorias():
    if not os.path.exists(CATEGORIAS_FILE):
        with open(CATEGORIAS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)
    with open(CATEGORIAS_FILE, "r", encoding="utf-8") as f:
        categorias = json.load(f)
        print("Categorias carregadas:", categorias)  # Adicionado para depuração
        return categorias

def salvar_categoria(categoria):
    categorias = carregar_categorias()
    if categoria and categoria not in categorias:
        categorias.append(categoria)
        with open(CATEGORIAS_FILE, "w", encoding="utf-8") as f:
            json.dump(categorias, f, ensure_ascii=False, indent=4)
        print("Categoria salva:", categoria)  # Adicionado para depuração

def limpar_jogadores():
    with open(JOGADORES_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=4)

# ---------------- ROTAS PRINCIPAIS ------------------

@app.route("/", methods=["GET", "POST"])
def index():
    jogadores = carregar_jogadores()
    categorias = carregar_categorias()
    categoria_selecionada = session.get("categoria_ativa", None)

    # --- NOVO: Define a primeira categoria como padrão se não houver seleção ---
    if not categoria_selecionada and categorias:  # Só ativa se não houver categoria E existirem categorias
        categoria_selecionada = categorias[0]  # Pega a primeira categoria
        session["categoria_ativa"] = categoria_selecionada  # Salva na sessão
    # --------------------------------------------------------------------------

    if request.method == "POST":
        acao = request.form.get("acao")

        if acao == "adicionar":
            nome = request.form.get("nome", "").strip()
            if nome:
                salvar_jogador(nome)
            return redirect(url_for("index"))

        elif acao == "limpar":
            limpar_jogadores()
            return redirect(url_for("index"))

        elif "categoria" in request.form:
            categoria = request.form["categoria"]
            session["categoria_ativa"] = categoria
            return redirect(url_for("index"))

    # Adicionando o retorno do template para o caso de GET ou após a execução de POST
    return render_template(
        "index.html",
        jogadores=jogadores,
        categorias=categorias,
        categoria_selecionada=categoria_selecionada
    )



@app.route("/iniciar", methods=["POST"])
def iniciar():
    categoria = session.get("categoria_ativa")
    if not categoria:
        return redirect(url_for("index"))
    return redirect(url_for("jogo"))

@app.route("/jogo", methods=['GET', 'POST'])  # Aceita GET e POST
def jogo():
    if request.method == 'POST':
        # Se clicou em "Continuar", sorteia novamente
        return redirect(url_for('jogo'))  # Recarrega a página com novos sorteios

    # Lógica normal (GET)
    jogadores = carregar_jogadores()
    prendas = carregar_prendas()
    categoria_selecionada = session.get("categoria_ativa")

    if not jogadores or not prendas or not categoria_selecionada:
        return redirect(url_for("index"))

    prendas_categoria = [p for p in prendas if p["categoria"] == categoria_selecionada]
    jogador_sorteado = random.choice(jogadores)
    prenda_sorteada = random.choice(prendas_categoria)

    return render_template(
        "jogo.html", 
        jogador=jogador_sorteado,
        categoria=categoria_selecionada,
        prenda=prenda_sorteada,
        shots=prenda_sorteada.get("doses_se_recusar", 0)
    ) 

@app.route("/cadastrar-prenda", methods=["GET", "POST"])
def cadastrar_prenda():
    categorias = carregar_categorias()
    prenda = None  # Inicializa como None

    if request.method == "POST":
        # Captura os dados com segurança
        descricao = request.form.get("descricao", "").strip()
        categoria = request.form.get("categoria", "").strip()
        doses_str = request.form.get("doses", "").strip()

        # Validação básica
        if not descricao or not categoria or not doses_str:
            return render_template("cadastrar_prenda.html", categorias=categorias, prenda=None)

        try:
            doses = int(doses_str)
        except ValueError:
            return render_template("cadastrar_prenda.html", categorias=categorias, prenda=None)

        # Verifica se a categoria já existe, senão cria uma nova
        if categoria not in categorias:
            salvar_categoria(categoria)
            categorias.append(categoria)  # Atualiza a lista com a nova categoria

        # Cria e salva a nova prenda
        nova_prenda = {
            "descricao": descricao,
            "categoria": categoria, 
            "doses_se_recusar": doses
        }
        salvar_prenda(nova_prenda)

        prenda = nova_prenda  # Passa para o template

    return render_template("cadastrar_prenda.html", categorias=categorias, prenda=prenda)



 
@app.route("/nova-partida", methods=['POST'])
def nova_partida():
    limpar_jogadores()  # Reseta a lista de jogadores
    session.pop("categoria_ativa", None)  # Remove a categoria da sessão
    return redirect(url_for('index'))  # Volta para o início
# ---------------- INICIAR APP ------------------

if __name__ == "__main__":
    app.run(debug=True)
