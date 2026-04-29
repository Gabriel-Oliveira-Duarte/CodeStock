from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import date

app = Flask(__name__)
app.secret_key = "codestock_tcc_secret_key_2024"


def conectar_db():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="codestock"
        )
        return conn
    except Exception as e:
        print("Erro ao conectar ao banco:", e)
        return None


def limpar_cnpj(cnpj):
    return "".join(filter(str.isdigit, cnpj or ""))


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Faça login para continuar.", "erro")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "GET":
        return render_template("cadastro.html")

    razao = request.form.get("razao", "").strip()
    fantasia = request.form.get("fantasia", "").strip()
    cnpj = request.form.get("cnpj", "").strip()
    segmento = request.form.get("segmento", "").strip()
    telefone = request.form.get("telefone", "").strip()
    email_empresa = request.form.get("emailEmpresa", "").strip().lower()
    endereco = request.form.get("endereco", "").strip()
    nome_admin = request.form.get("nomeAdmin", "").strip()
    cargo_admin = request.form.get("cargoAdmin", "").strip()
    email_admin = request.form.get("emailAdmin", "").strip().lower()
    matricula = request.form.get("matriculaAdmin", "").strip() or "ADM001"
    senha = request.form.get("senha", "")
    confirmar = request.form.get("confirmarSenha", "")

    if not razao or not cnpj or not email_empresa or not nome_admin or not email_admin or not senha:
        flash("Preencha todos os campos obrigatórios.", "erro")
        return render_template("cadastro.html")

    if senha != confirmar:
        flash("As senhas não coincidem.", "erro")
        return render_template("cadastro.html")

    if len(senha) < 8:
        flash("A senha deve ter no mínimo 8 caracteres.", "erro")
        return render_template("cadastro.html")

    conn = conectar_db()
    if not conn:
        flash("Erro ao conectar ao banco de dados.", "erro")
        return render_template("cadastro.html")

    cursor = conn.cursor()
    try:
        senha_hash = generate_password_hash(senha)

        cursor.execute("""
            INSERT INTO empresas
                (razao_social, nome_fantasia, cnpj, segmento, telefone, email, endereco, senha_hash)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            razao,
            fantasia,
            limpar_cnpj(cnpj),
            segmento,
            telefone,
            email_empresa,
            endereco,
            senha_hash
        ))

        empresa_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO usuarios
                (empresa_id, nome, matricula, cargo, email, perfil, senha_hash)
            VALUES
                (%s, %s, %s, %s, %s, 'admin', %s)
        """, (
            empresa_id,
            nome_admin,
            matricula,
            cargo_admin,
            email_admin,
            senha_hash
        ))

        conn.commit()
        flash(f"Empresa cadastrada com sucesso! Use a matrícula {matricula} para acessar.", "sucesso")
        return redirect(url_for("login"))

    except mysql.connector.IntegrityError:
        flash("CNPJ ou e-mail já cadastrado no sistema.", "erro")
        return render_template("cadastro.html")
    except Exception as e:
        flash(f"Erro ao cadastrar: {e}", "erro")
        return render_template("cadastro.html")
    finally:
        cursor.close()
        conn.close()


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", etapa="empresa")

    etapa = request.form.get("etapa", "empresa")

    conn = conectar_db()
    if not conn:
        flash("Erro ao conectar ao banco de dados.", "erro")
        return render_template("login.html", etapa="empresa")

    cursor = conn.cursor(dictionary=True)

    try:
        if etapa == "empresa":
            cnpj = request.form.get("cnpj", "").strip()
            email_empresa = request.form.get("emailEmpresa", "").strip().lower()
            senha_empresa = request.form.get("senhaEmpresa", "")

            cursor.execute(
                "SELECT * FROM empresas WHERE LOWER(email) = %s",
                (email_empresa,)
            )
            empresa = cursor.fetchone()

            if not empresa:
                flash("E-mail empresarial não encontrado.", "erro")
                return render_template("login.html", etapa="empresa")

            if limpar_cnpj(empresa["cnpj"]) != limpar_cnpj(cnpj):
                flash("CNPJ incorreto.", "erro")
                return render_template("login.html", etapa="empresa")

            if not check_password_hash(empresa["senha_hash"], senha_empresa):
                flash("Senha empresarial incorreta.", "erro")
                return render_template("login.html", etapa="empresa")

            empresa_nome = empresa["nome_fantasia"] or empresa["razao_social"]

            return render_template(
                "login.html",
                etapa="usuario",
                empresa_id=empresa["id"],
                empresa_nome=empresa_nome
            )

        if etapa == "usuario":
            empresa_id = request.form.get("empresa_id", "").strip()
            empresa_nome = request.form.get("empresa_nome", "").strip()
            usuario_digitado = request.form.get("usuario", "").strip()
            senha_usuario = request.form.get("senhaUsuario", "")

            if not empresa_id:
                flash("Empresa não identificada. Faça a primeira etapa novamente.", "erro")
                return render_template("login.html", etapa="empresa")

            cursor.execute("""
                SELECT *
                FROM usuarios
                WHERE empresa_id = %s
                  AND (
                    matricula = %s
                    OR email = %s
                    OR nome = %s
                  )
            """, (
                empresa_id,
                usuario_digitado,
                usuario_digitado.lower(),
                usuario_digitado
            ))

            usuario = cursor.fetchone()

            if not usuario:
                flash("Usuário não encontrado. Use a matrícula cadastrada, por exemplo ADM001.", "erro")
                return render_template(
                    "login.html",
                    etapa="usuario",
                    empresa_id=empresa_id,
                    empresa_nome=empresa_nome
                )

            if not check_password_hash(usuario["senha_hash"], senha_usuario):
                flash("Senha do usuário incorreta.", "erro")
                return render_template(
                    "login.html",
                    etapa="usuario",
                    empresa_id=empresa_id,
                    empresa_nome=empresa_nome
                )

            session.clear()
            session["usuario_id"] = usuario["id"]
            session["usuario_nome"] = usuario["nome"]
            session["usuario_perfil"] = usuario["perfil"]
            session["empresa_id"] = usuario["empresa_id"]
            session["empresa_nome"] = empresa_nome

            return redirect(url_for("home"))

        flash("Etapa de login inválida.", "erro")
        return render_template("login.html", etapa="empresa")

    except Exception as e:
        flash(f"Erro no login: {e}", "erro")
        return render_template("login.html", etapa="empresa")
    finally:
        cursor.close()
        conn.close()


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/home")
@login_required
def home():
    conn = conectar_db()
    dados = {
        "total_materiais": 0,
        "pendentes": 0,
        "total_etiquetas": 0,
        "total_movimentacoes": 0,
        "materiais_recentes": []
    }

    if conn:
        cursor = conn.cursor(dictionary=True)
        empresa_id = session["empresa_id"]
        try:
            cursor.execute("SELECT COUNT(*) AS total FROM materiais WHERE empresa_id = %s", (empresa_id,))
            dados["total_materiais"] = cursor.fetchone()["total"]

            cursor.execute(
                "SELECT COUNT(*) AS total FROM materiais WHERE empresa_id = %s AND status = 'Pendente'",
                (empresa_id,)
            )
            dados["pendentes"] = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total FROM etiquetas WHERE empresa_id = %s", (empresa_id,))
            dados["total_etiquetas"] = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) AS total FROM movimentacoes WHERE empresa_id = %s", (empresa_id,))
            dados["total_movimentacoes"] = cursor.fetchone()["total"]

            cursor.execute("""
                SELECT codigo, descricao, lote, localizacao, status
                FROM materiais
                WHERE empresa_id = %s
                ORDER BY criado_em DESC
                LIMIT 5
            """, (empresa_id,))
            dados["materiais_recentes"] = cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    return render_template("home.html", **dados)


@app.route("/materiais")
@login_required
def materiais():
    conn = conectar_db()
    lista = []

    if conn:
        cursor = conn.cursor(dictionary=True)
        empresa_id = session["empresa_id"]
        try:
            cursor.execute("""
                SELECT codigo, descricao, lote, fornecedor, quantidade, unidade,
                       localizacao, data_entrada, status
                FROM materiais
                WHERE empresa_id = %s
                ORDER BY criado_em DESC
            """, (empresa_id,))
            lista = cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    return render_template("materiais.html", materiais=lista)


@app.route("/materialcadastro", methods=["GET", "POST"])
@login_required
def materialcadastro():
    if request.method == "GET":
        return render_template("materialcadastro.html")

    codigo = request.form.get("codigo", "").strip()
    descricao = request.form.get("descricao", "").strip()
    lote = request.form.get("lote", "").strip()
    fornecedor = request.form.get("fornecedor", "").strip()
    quantidade = request.form.get("quantidade", "0")
    unidade = request.form.get("unidade", "").strip()
    localizacao = request.form.get("localizacao", "").strip()
    status = request.form.get("status", "Pendente").strip()
    data_entrada = request.form.get("dataEntrada", str(date.today()))
    responsavel = request.form.get("responsavel", "").strip()
    observacao = request.form.get("observacao", "").strip()

    if not codigo or not descricao or not lote or not fornecedor or not quantidade or not unidade or not localizacao:
        flash("Preencha todos os campos obrigatórios.", "erro")
        return render_template("materialcadastro.html")

    conn = conectar_db()
    if not conn:
        flash("Erro ao conectar ao banco de dados.", "erro")
        return render_template("materialcadastro.html")

    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO materiais
                (empresa_id, codigo, descricao, lote, fornecedor, quantidade, unidade,
                 localizacao, status, data_entrada, responsavel, observacao)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            session["empresa_id"],
            codigo,
            descricao,
            lote,
            fornecedor,
            float(quantidade),
            unidade,
            localizacao,
            status,
            data_entrada,
            responsavel,
            observacao
        ))

        conn.commit()
        flash("Material cadastrado com sucesso!", "sucesso")
        return redirect(url_for("materiais"))

    except mysql.connector.IntegrityError:
        flash(f"O código '{codigo}' já existe para esta empresa.", "erro")
        return render_template("materialcadastro.html")
    except Exception as e:
        flash(f"Erro ao salvar: {e}", "erro")
        return render_template("materialcadastro.html")
    finally:
        cursor.close()
        conn.close()


@app.route("/movimentacoes", methods=["GET", "POST"])
@login_required
def movimentacoes():
    conn = conectar_db()
    lista = []

    if request.method == "POST":
        codigo = request.form.get("codigo", "").strip()
        tipo = request.form.get("tipo", "").strip()
        origem = request.form.get("origem", "").strip()
        destino = request.form.get("destino", "").strip()
        quantidade = request.form.get("quantidade", "0")
        data = request.form.get("data", str(date.today()))
        responsavel = request.form.get("responsavel", "").strip()
        validacao = request.form.get("validacao", "Pendente").strip()
        observacao = request.form.get("observacao", "").strip()

        if not codigo or not tipo or not destino or not quantidade:
            flash("Preencha todos os campos obrigatórios.", "erro")
        elif conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO movimentacoes
                        (empresa_id, material_codigo, tipo, origem, destino,
                         quantidade, data, responsavel, validacao, observacao)
                    VALUES
                        (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    session["empresa_id"],
                    codigo,
                    tipo,
                    origem,
                    destino,
                    float(quantidade),
                    data,
                    responsavel,
                    validacao,
                    observacao
                ))

                conn.commit()
                flash("Movimentação registrada com sucesso!", "sucesso")
            except Exception as e:
                flash(f"Erro ao registrar: {e}", "erro")
            finally:
                cursor.close()

    if conn:
        cursor = conn.cursor(dictionary=True)
        empresa_id = session["empresa_id"]
        try:
            cursor.execute("""
                SELECT tipo, material_codigo, origem, destino, quantidade, validacao, data
                FROM movimentacoes
                WHERE empresa_id = %s
                ORDER BY criado_em DESC
                LIMIT 50
            """, (empresa_id,))
            lista = cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    return render_template("movimentacoes.html", movimentacoes=lista)


@app.route("/etiquetas", methods=["GET", "POST"])
@login_required
def etiquetas():
    conn = conectar_db()
    lista = []

    if request.method == "POST":
        codigo = request.form.get("codigo", "").strip()
        lote = request.form.get("lote", "").strip()
        descricao = request.form.get("descricao", "").strip()
        quantidade = request.form.get("quantidade", "").strip()
        localizacao = request.form.get("localizacao", "").strip()
        status = request.form.get("statusEtiqueta", "Gerada").strip()

        if not codigo or not lote:
            flash("Informe ao menos o código e o lote.", "erro")
        elif conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO etiquetas
                        (empresa_id, material_codigo, lote, descricao, quantidade, localizacao, status)
                    VALUES
                        (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    session["empresa_id"],
                    codigo,
                    lote,
                    descricao,
                    quantidade,
                    localizacao,
                    status
                ))

                conn.commit()
                flash("Etiqueta gerada com sucesso!", "sucesso")
            except Exception as e:
                flash(f"Erro ao gerar etiqueta: {e}", "erro")
            finally:
                cursor.close()

    if conn:
        cursor = conn.cursor(dictionary=True)
        empresa_id = session["empresa_id"]
        try:
            cursor.execute("""
                SELECT material_codigo, descricao, lote, localizacao, status
                FROM etiquetas
                WHERE empresa_id = %s
                ORDER BY criado_em DESC
            """, (empresa_id,))
            lista = cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    return render_template("etiquetas.html", etiquetas=lista)


@app.route("/relatorios")
@login_required
def relatorios():
    return render_template("relatorios.html")


if __name__ == "__main__":
    app.run(debug=True)