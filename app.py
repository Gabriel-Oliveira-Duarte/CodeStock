from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import date
from flask import send_file
from io import BytesIO
import qrcode
from flask import request

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
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated


def perfil_required(*perfis_permitidos):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            perfil_usuario = session.get("usuario_perfil")

            if perfil_usuario not in perfis_permitidos:
                flash("Você não tem permissão para acessar esta página.", "erro")
                return redirect(url_for("home"))

            return f(*args, **kwargs)
        return decorated
    return decorator


def admin_required(f):
    return perfil_required("admin")(f)


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

    senha_empresa = request.form.get("senha", "")
    confirmar_empresa = request.form.get("confirmarSenha", "")
    senha_admin = request.form.get("senhaAdmin", "")
    confirmar_admin = request.form.get("confirmarSenhaAdmin", "")
    termos = request.form.get("termos")

    if not razao or not cnpj or not segmento or not email_empresa or not nome_admin or not email_admin:
        flash("Preencha todos os campos obrigatórios.", "erro")
        return render_template("cadastro.html")

    if not senha_empresa or not confirmar_empresa:
        flash("Informe e confirme a senha empresarial.", "erro")
        return render_template("cadastro.html")

    if not senha_admin or not confirmar_admin:
        flash("Informe e confirme a senha do administrador.", "erro")
        return render_template("cadastro.html")

    if senha_empresa != confirmar_empresa:
        flash("As senhas da empresa não coincidem.", "erro")
        return render_template("cadastro.html")

    if senha_admin != confirmar_admin:
        flash("As senhas do administrador não coincidem.", "erro")
        return render_template("cadastro.html")

    if len(senha_empresa) < 8:
        flash("A senha empresarial deve ter no mínimo 8 caracteres.", "erro")
        return render_template("cadastro.html")

    if len(senha_admin) < 8:
        flash("A senha do administrador deve ter no mínimo 8 caracteres.", "erro")
        return render_template("cadastro.html")

    if not termos:
        flash("Você precisa aceitar os termos para concluir o cadastro.", "erro")
        return render_template("cadastro.html")

    conn = conectar_db()
    if not conn:
        flash("Erro ao conectar ao banco de dados.", "erro")
        return render_template("cadastro.html")

    cursor = conn.cursor()
    try:
        senha_empresa_hash = generate_password_hash(senha_empresa)
        senha_admin_hash = generate_password_hash(senha_admin)

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
            senha_empresa_hash
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
            senha_admin_hash
        ))

        conn.commit()
        flash(f"Empresa cadastrada com sucesso! Use a matrícula {matricula} e a senha do administrador para acessar.", "sucesso")
        return redirect(url_for("login"))

    except mysql.connector.IntegrityError:
        conn.rollback()
        flash("CNPJ, e-mail empresarial ou matrícula já cadastrado no sistema.", "erro")
        return render_template("cadastro.html")
    except Exception as e:
        conn.rollback()
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
        "materiais_recentes": [],
        "grafico_semana": {
            "Seg": {"entrada": 0, "saida": 0},
            "Ter": {"entrada": 0, "saida": 0},
            "Qua": {"entrada": 0, "saida": 0},
            "Qui": {"entrada": 0, "saida": 0},
            "Sex": {"entrada": 0, "saida": 0}
        }
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

            cursor.execute("""
                SELECT
                    DAYOFWEEK(data) AS dia_semana,
                    tipo,
                    COUNT(*) AS total
                FROM movimentacoes
                WHERE empresa_id = %s
                  AND data >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                  AND tipo IN ('Entrada', 'Saída')
                GROUP BY dia_semana, tipo
            """, (empresa_id,))

            mapa_dias = {
                2: "Seg",
                3: "Ter",
                4: "Qua",
                5: "Qui",
                6: "Sex"
            }

            for item in cursor.fetchall():
                dia = mapa_dias.get(item["dia_semana"])

                if dia:
                    if item["tipo"] == "Entrada":
                        dados["grafico_semana"][dia]["entrada"] = item["total"]
                    elif item["tipo"] == "Saída":
                        dados["grafico_semana"][dia]["saida"] = item["total"]

        finally:
            cursor.close()
            conn.close()

    altura_grafico = {}

    for dia, valores in dados["grafico_semana"].items():
        altura_grafico[dia] = {
            "entrada": max(valores["entrada"] * 20, 6),
            "saida": max(valores["saida"] * 20, 6)
        }

    dados["altura_grafico"] = altura_grafico

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
@perfil_required("admin", "operador")
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
@perfil_required("admin", "operador", "conferente")
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
            cursor = conn.cursor(dictionary=True)

            try:
                qtd = float(quantidade)
                empresa_id = session["empresa_id"]

                cursor.execute("""
                    SELECT codigo, quantidade, localizacao, status
                    FROM materiais
                    WHERE empresa_id = %s AND codigo = %s
                """, (empresa_id, codigo))
                material = cursor.fetchone()

                if not material:
                    flash("Material não encontrado. Verifique o código informado.", "erro")

                elif tipo == "Saída" and float(material["quantidade"]) < qtd:
                    flash("Estoque insuficiente para realizar a saída.", "erro")
                
                elif tipo in ["Saída", "Transferência", "Correção de localização"] and origem.strip().lower() != material["localizacao"].strip().lower():
                    flash(f"Local de origem incorreto. O material está atualmente em: {material['localizacao']}", "erro")

                else:
                    cursor.execute("""
                        INSERT INTO movimentacoes
                            (empresa_id, material_codigo, tipo, origem, destino,
                             quantidade, data, responsavel, validacao, observacao)
                        VALUES
                            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        empresa_id,
                        codigo,
                        tipo,
                        origem,
                        destino,
                        qtd,
                        data,
                        responsavel,
                        validacao,
                        observacao
                    ))

                    if tipo == "Entrada":
                        cursor.execute("""
                            UPDATE materiais
                            SET quantidade = quantidade + %s
                            WHERE codigo = %s AND empresa_id = %s
                        """, (qtd, codigo, empresa_id))

                    elif tipo == "Saída":
                        cursor.execute("""
                            UPDATE materiais
                            SET quantidade = quantidade - %s
                            WHERE codigo = %s AND empresa_id = %s
                        """, (qtd, codigo, empresa_id))

                    elif tipo == "Transferência":
                        cursor.execute("""
                            UPDATE materiais
                            SET localizacao = %s
                            WHERE codigo = %s AND empresa_id = %s
                        """, (destino, codigo, empresa_id))

                    elif tipo == "Correção de localização":
                        cursor.execute("""
                            UPDATE materiais
                            SET localizacao = %s
                            WHERE codigo = %s AND empresa_id = %s
                        """, (destino, codigo, empresa_id))

                    elif tipo == "Bloqueio de material":
                        cursor.execute("""
                            UPDATE materiais
                            SET status = 'Bloqueado'
                            WHERE codigo = %s AND empresa_id = %s
                        """, (codigo, empresa_id))

                    conn.commit()
                    flash("Movimentação registrada com sucesso!", "sucesso")

            except Exception as e:
                conn.rollback()
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
@perfil_required("admin", "operador")
def etiquetas():
    conn = conectar_db()
    etiquetas_lista = []
    materiais_lista = []

    if not conn:
        flash("Erro ao conectar ao banco de dados.", "erro")
        return render_template("etiquetas.html", etiquetas=[], materiais=[])

    empresa_id = session["empresa_id"]

    if request.method == "POST":
        codigo = request.form.get("codigo", "").strip()
        lote = request.form.get("lote", "").strip()
        descricao = request.form.get("descricao", "").strip()
        quantidade = request.form.get("quantidade", "").strip()
        localizacao = request.form.get("localizacao", "").strip()
        status = request.form.get("statusEtiqueta", "Gerada").strip()

        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO etiquetas
                    (empresa_id, material_codigo, lote, descricao, quantidade, localizacao, status)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s)
            """, (empresa_id, codigo, lote, descricao, quantidade, localizacao, status))

            conn.commit()
            flash("Etiqueta gerada com sucesso!", "sucesso")
            return redirect(url_for("etiquetas"))

        except Exception as e:
            flash(f"Erro ao gerar etiqueta: {e}", "erro")
        finally:
            cursor.close()

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT codigo, descricao, lote, quantidade, unidade, localizacao, status
            FROM materiais
            WHERE empresa_id = %s
            ORDER BY criado_em DESC
        """, (empresa_id,))
        materiais_lista = cursor.fetchall()

        cursor.execute("""
            SELECT material_codigo, descricao, lote, quantidade, localizacao, status, criado_em
            FROM etiquetas
            WHERE empresa_id = %s
            ORDER BY criado_em DESC
        """, (empresa_id,))
        etiquetas_lista = cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

    return render_template(
        "etiquetas.html",
        etiquetas=etiquetas_lista,
        materiais=materiais_lista
    )


@app.route("/usuarios", methods=["GET", "POST"])
@login_required
@perfil_required("admin")
def usuarios():
    conn = conectar_db()
    if not conn:
        flash("Erro ao conectar ao banco de dados.", "erro")
        return redirect(url_for("home"))

    empresa_id = session["empresa_id"]
    perfis_validos = ["admin", "operador", "conferente"]

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        matricula = request.form.get("matricula", "").strip()
        cargo = request.form.get("cargo", "").strip()
        email = request.form.get("email", "").strip().lower()
        perfil = request.form.get("perfil", "operador").strip()
        senha = request.form.get("senha", "")
        confirmar_senha = request.form.get("confirmarSenha", "")

        if not nome or not matricula or not perfil or not senha:
            flash("Preencha nome, matrícula, perfil e senha.", "erro")
            conn.close()
            return redirect(url_for("usuarios"))

        if perfil not in perfis_validos:
            flash("Perfil inválido.", "erro")
            conn.close()
            return redirect(url_for("usuarios"))

        if senha != confirmar_senha:
            flash("As senhas do usuário não coincidem.", "erro")
            conn.close()
            return redirect(url_for("usuarios"))

        if len(senha) < 8:
            flash("A senha do usuário deve ter no mínimo 8 caracteres.", "erro")
            conn.close()
            return redirect(url_for("usuarios"))

        cursor = conn.cursor()
        try:
            senha_hash = generate_password_hash(senha)
            cursor.execute("""
                INSERT INTO usuarios
                    (empresa_id, nome, matricula, cargo, email, perfil, senha_hash)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s)
            """, (
                empresa_id,
                nome,
                matricula,
                cargo,
                email,
                perfil,
                senha_hash
            ))
            conn.commit()
            flash("Usuário cadastrado com sucesso!", "sucesso")
        except mysql.connector.IntegrityError:
            conn.rollback()
            flash("Já existe um usuário com essa matrícula nesta empresa.", "erro")
        except Exception as e:
            conn.rollback()
            flash(f"Erro ao cadastrar usuário: {e}", "erro")
        finally:
            cursor.close()

        conn.close()
        return redirect(url_for("usuarios"))

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, nome, matricula, cargo, email, perfil, criado_em
            FROM usuarios
            WHERE empresa_id = %s
            ORDER BY criado_em DESC
        """, (empresa_id,))
        lista_usuarios = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) AS total FROM usuarios WHERE empresa_id = %s", (empresa_id,))
        total_usuarios = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM usuarios WHERE empresa_id = %s AND perfil = 'admin'", (empresa_id,))
        total_admins = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM usuarios WHERE empresa_id = %s AND perfil = 'operador'", (empresa_id,))
        total_operadores = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM usuarios WHERE empresa_id = %s AND perfil = 'conferente'", (empresa_id,))
        total_conferentes = cursor.fetchone()["total"]
    finally:
        cursor.close()
        conn.close()

    return render_template(
        "usuarios.html",
        usuarios=lista_usuarios,
        total_usuarios=total_usuarios,
        total_admins=total_admins,
        total_operadores=total_operadores,
        total_conferentes=total_conferentes
    )


@app.route("/usuarios/editar/<int:usuario_id>", methods=["POST"])
@login_required
@perfil_required("admin")
def editar_usuario(usuario_id):
    nome = request.form.get("nome", "").strip()
    matricula = request.form.get("matricula", "").strip()
    cargo = request.form.get("cargo", "").strip()
    email = request.form.get("email", "").strip().lower()
    perfil = request.form.get("perfil", "operador").strip()
    senha = request.form.get("senha", "")
    confirmar_senha = request.form.get("confirmarSenha", "")

    perfis_validos = ["admin", "operador", "conferente"]

    if not nome or not matricula or perfil not in perfis_validos:
        flash("Preencha nome, matrícula e perfil corretamente.", "erro")
        return redirect(url_for("usuarios"))

    if senha and senha != confirmar_senha:
        flash("As novas senhas não coincidem.", "erro")
        return redirect(url_for("usuarios"))

    if senha and len(senha) < 8:
        flash("A nova senha deve ter no mínimo 8 caracteres.", "erro")
        return redirect(url_for("usuarios"))

    conn = conectar_db()
    if not conn:
        flash("Erro ao conectar ao banco de dados.", "erro")
        return redirect(url_for("usuarios"))

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, perfil FROM usuarios WHERE id = %s AND empresa_id = %s",
            (usuario_id, session["empresa_id"])
        )
        usuario_atual = cursor.fetchone()

        if not usuario_atual:
            flash("Usuário não encontrado.", "erro")
            return redirect(url_for("usuarios"))

        if usuario_id == session.get("usuario_id") and perfil != "admin":
            flash("Você não pode remover o próprio perfil de administrador.", "erro")
            return redirect(url_for("usuarios"))

        if senha:
            senha_hash = generate_password_hash(senha)
            cursor.execute("""
                UPDATE usuarios
                SET nome = %s, matricula = %s, cargo = %s, email = %s, perfil = %s, senha_hash = %s
                WHERE id = %s AND empresa_id = %s
            """, (
                nome, matricula, cargo, email, perfil, senha_hash, usuario_id, session["empresa_id"]
            ))
        else:
            cursor.execute("""
                UPDATE usuarios
                SET nome = %s, matricula = %s, cargo = %s, email = %s, perfil = %s
                WHERE id = %s AND empresa_id = %s
            """, (
                nome, matricula, cargo, email, perfil, usuario_id, session["empresa_id"]
            ))

        conn.commit()
        flash("Usuário atualizado com sucesso!", "sucesso")
    except mysql.connector.IntegrityError:
        conn.rollback()
        flash("Já existe outro usuário com essa matrícula nesta empresa.", "erro")
    except Exception as e:
        conn.rollback()
        flash(f"Erro ao editar usuário: {e}", "erro")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("usuarios"))


@app.route("/usuarios/excluir/<int:usuario_id>", methods=["POST"])
@login_required
@perfil_required("admin")
def excluir_usuario(usuario_id):
    if usuario_id == session.get("usuario_id"):
        flash("Você não pode excluir o próprio usuário logado.", "erro")
        return redirect(url_for("usuarios"))

    conn = conectar_db()
    if not conn:
        flash("Erro ao conectar ao banco de dados.", "erro")
        return redirect(url_for("usuarios"))

    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM usuarios WHERE id = %s AND empresa_id = %s",
            (usuario_id, session["empresa_id"])
        )
        conn.commit()

        if cursor.rowcount == 0:
            flash("Usuário não encontrado.", "erro")
        else:
            flash("Usuário excluído com sucesso!", "sucesso")
    except Exception as e:
        conn.rollback()
        flash(f"Erro ao excluir usuário: {e}", "erro")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("usuarios"))


@app.route("/relatorios")
@login_required
@perfil_required("admin")
def relatorios():
    return render_template("relatorios.html")


@app.route("/material/<codigo>")
@login_required
def visualizar_material(codigo):
    conn = conectar_db()

    if not conn:
        flash("Erro ao conectar ao banco de dados.", "erro")
        return redirect(url_for("materiais"))

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT *
            FROM materiais
            WHERE empresa_id = %s AND codigo = %s
        """, (session["empresa_id"], codigo))

        material = cursor.fetchone()

        if not material:
            flash("Material não encontrado.", "erro")
            return redirect(url_for("materiais"))

        return render_template("material_detalhes.html", material=material)

    finally:
        cursor.close()
        conn.close()


@app.route("/qrcode/material/<codigo>")
@login_required
def gerar_qrcode_material(codigo):
    url_material = request.host_url + f"material/{codigo}"

    img = qrcode.make(url_material)

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return send_file(buffer, mimetype="image/png")

@app.route("/scan")
@login_required
def scan():
    return render_template("scan.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)