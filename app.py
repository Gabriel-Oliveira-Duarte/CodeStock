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
                SELECT id, codigo, descricao, lote, fornecedor, quantidade, unidade,
                       localizacao, data_entrada, status, responsavel, observacao, criado_em
                FROM materiais
                WHERE empresa_id = %s
                ORDER BY criado_em DESC
            """, (empresa_id,))
            lista = cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    return render_template("materiais.html", materiais=lista)


@app.route("/material/editar/<codigo>", methods=["GET", "POST"])
@login_required
@perfil_required("admin", "operador")
def editar_material(codigo):
    conn = conectar_db()

    if not conn:
        flash("Erro ao conectar ao banco de dados.", "erro")
        return redirect(url_for("materiais"))

    empresa_id = session["empresa_id"]
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT *
            FROM materiais
            WHERE empresa_id = %s AND codigo = %s
        """, (empresa_id, codigo))
        material = cursor.fetchone()

        if not material:
            flash("Material não encontrado.", "erro")
            return redirect(url_for("materiais"))

        if request.method == "GET":
            return render_template("material_editar.html", material=material)

        novo_codigo = request.form.get("codigo", "").strip()
        descricao = request.form.get("descricao", "").strip()
        lote = request.form.get("lote", "").strip()
        fornecedor = request.form.get("fornecedor", "").strip()
        quantidade = request.form.get("quantidade", "0").strip()
        unidade = request.form.get("unidade", "").strip()
        localizacao = request.form.get("localizacao", "").strip()
        status = request.form.get("status", "Pendente").strip()
        data_entrada = request.form.get("dataEntrada", "").strip() or None
        responsavel = request.form.get("responsavel", "").strip()
        observacao = request.form.get("observacao", "").strip()

        status_validos = ["Liberado", "Pendente", "Conferência", "Bloqueado"]

        if not novo_codigo or not descricao or not lote or not fornecedor or not quantidade or not unidade or not localizacao:
            flash("Preencha todos os campos obrigatórios.", "erro")
            return render_template("material_editar.html", material=material)

        if status not in status_validos:
            flash("Status inválido.", "erro")
            return render_template("material_editar.html", material=material)

        try:
            quantidade_float = float(quantidade)
        except ValueError:
            flash("Quantidade inválida.", "erro")
            return render_template("material_editar.html", material=material)

        cursor.execute("""
            UPDATE materiais
            SET codigo = %s,
                descricao = %s,
                lote = %s,
                fornecedor = %s,
                quantidade = %s,
                unidade = %s,
                localizacao = %s,
                status = %s,
                data_entrada = %s,
                responsavel = %s,
                observacao = %s
            WHERE empresa_id = %s AND codigo = %s
        """, (
            novo_codigo,
            descricao,
            lote,
            fornecedor,
            quantidade_float,
            unidade,
            localizacao,
            status,
            data_entrada,
            responsavel,
            observacao,
            empresa_id,
            codigo
        ))

        if novo_codigo != codigo:
            cursor.execute("""
                UPDATE movimentacoes
                SET material_codigo = %s
                WHERE empresa_id = %s AND material_codigo = %s
            """, (novo_codigo, empresa_id, codigo))

            cursor.execute("""
                UPDATE etiquetas
                SET material_codigo = %s,
                    lote = %s,
                    descricao = %s,
                    quantidade = %s,
                    localizacao = %s
                WHERE empresa_id = %s AND material_codigo = %s
            """, (
                novo_codigo,
                lote,
                descricao,
                f"{quantidade_float:g} {unidade}",
                localizacao,
                empresa_id,
                codigo
            ))
        else:
            cursor.execute("""
                UPDATE etiquetas
                SET lote = %s,
                    descricao = %s,
                    quantidade = %s,
                    localizacao = %s
                WHERE empresa_id = %s AND material_codigo = %s
            """, (
                lote,
                descricao,
                f"{quantidade_float:g} {unidade}",
                localizacao,
                empresa_id,
                codigo
            ))

        conn.commit()
        flash("Material atualizado com sucesso!", "sucesso")
        return redirect(url_for("materiais"))

    except mysql.connector.IntegrityError:
        conn.rollback()
        flash("Já existe outro material com esse código nesta empresa.", "erro")
        return redirect(url_for("materiais"))
    except Exception as e:
        conn.rollback()
        flash(f"Erro ao editar material: {e}", "erro")
        return redirect(url_for("materiais"))
    finally:
        cursor.close()
        conn.close()


@app.route("/material/excluir/<codigo>", methods=["POST"])
@login_required
@perfil_required("admin")
def excluir_material(codigo):
    conn = conectar_db()

    if not conn:
        flash("Erro ao conectar ao banco de dados.", "erro")
        return redirect(url_for("materiais"))

    empresa_id = session["empresa_id"]
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id
            FROM materiais
            WHERE empresa_id = %s AND codigo = %s
        """, (empresa_id, codigo))

        if not cursor.fetchone():
            flash("Material não encontrado.", "erro")
            return redirect(url_for("materiais"))

        cursor.execute("""
            DELETE FROM etiquetas
            WHERE empresa_id = %s AND material_codigo = %s
        """, (empresa_id, codigo))

        cursor.execute("""
            DELETE FROM materiais
            WHERE empresa_id = %s AND codigo = %s
        """, (empresa_id, codigo))

        conn.commit()
        flash("Material excluído com sucesso!", "sucesso")

    except Exception as e:
        conn.rollback()
        flash(f"Erro ao excluir material: {e}", "erro")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("materiais"))


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

    if not conn:
        flash("Erro ao conectar ao banco de dados.", "erro")
        return render_template(
            "movimentacoes.html",
            movimentacoes=[],
            materiais=[],
            filtros={},
            resumo={
                "entradas_hoje": 0,
                "saidas_hoje": 0,
                "transferencias_hoje": 0,
                "bloqueios_hoje": 0
            },
            altura_grafico={
                "Seg": {"entrada": 6, "saida": 6},
                "Ter": {"entrada": 6, "saida": 6},
                "Qua": {"entrada": 6, "saida": 6},
                "Qui": {"entrada": 6, "saida": 6},
                "Sex": {"entrada": 6, "saida": 6}
            }
        )

    empresa_id = session["empresa_id"]

    if request.method == "POST":
        codigo = request.form.get("codigo", "").strip()
        tipo = request.form.get("tipo", "").strip()
        origem = request.form.get("origem", "").strip()
        destino = request.form.get("destino", "").strip()
        quantidade = request.form.get("quantidade", "0").strip()
        data_mov = request.form.get("data", str(date.today())).strip()
        responsavel = session.get("usuario_nome", "Sistema")
        validacao = request.form.get("validacao", "Validado").strip()
        observacao = request.form.get("observacao", "").strip()

        tipos_validos = [
            "Entrada",
            "Saída",
            "Transferência",
            "Correção de localização",
            "Bloqueio de material"
        ]

        validacoes_validas = ["Validado", "Pendente", "Revisão necessária"]

        if not codigo or not tipo or not quantidade:
            flash("Informe o material, o tipo de movimentação e a quantidade.", "erro")
            conn.close()
            return redirect(url_for("movimentacoes"))

        if tipo not in tipos_validos:
            flash("Tipo de movimentação inválido.", "erro")
            conn.close()
            return redirect(url_for("movimentacoes"))

        if validacao not in validacoes_validas:
            flash("Status de validação inválido.", "erro")
            conn.close()
            return redirect(url_for("movimentacoes"))

        try:
            qtd = float(quantidade.replace(",", "."))
        except ValueError:
            flash("Quantidade inválida.", "erro")
            conn.close()
            return redirect(url_for("movimentacoes"))

        if qtd <= 0:
            flash("A quantidade deve ser maior que zero.", "erro")
            conn.close()
            return redirect(url_for("movimentacoes"))

        if tipo in ["Entrada", "Transferência", "Correção de localização"] and not destino:
            flash("Informe o local de destino para este tipo de movimentação.", "erro")
            conn.close()
            return redirect(url_for("movimentacoes"))

        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT codigo, descricao, quantidade, localizacao, status
                FROM materiais
                WHERE empresa_id = %s AND codigo = %s
            """, (empresa_id, codigo))
            material = cursor.fetchone()

            if not material:
                flash("Material não encontrado. Verifique o código informado.", "erro")
                return redirect(url_for("movimentacoes"))

            local_atual = (material.get("localizacao") or "").strip()

            if tipo in ["Saída", "Transferência", "Correção de localização"]:
                if not origem:
                    flash(f"Informe a origem. O material está atualmente em: {local_atual or 'sem localização cadastrada'}", "erro")
                    return redirect(url_for("movimentacoes"))

                if origem.lower() != local_atual.lower():
                    flash(f"Local de origem incorreto. O material está atualmente em: {local_atual}", "erro")
                    return redirect(url_for("movimentacoes"))

            if tipo == "Saída" and float(material["quantidade"] or 0) < qtd:
                flash("Estoque insuficiente para realizar a saída.", "erro")
                return redirect(url_for("movimentacoes"))

            if tipo == "Entrada" and not origem:
                origem = "Entrada externa"

            if tipo == "Saída" and not destino:
                destino = "Saída do estoque"

            if tipo == "Bloqueio de material":
                origem = origem or local_atual
                destino = destino or local_atual

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
                data_mov,
                responsavel,
                validacao,
                observacao
            ))

            if tipo == "Entrada":
                cursor.execute("""
                    UPDATE materiais
                    SET quantidade = quantidade + %s,
                        localizacao = %s
                    WHERE codigo = %s AND empresa_id = %s
                """, (qtd, destino, codigo, empresa_id))

            elif tipo == "Saída":
                cursor.execute("""
                    UPDATE materiais
                    SET quantidade = quantidade - %s
                    WHERE codigo = %s AND empresa_id = %s
                """, (qtd, codigo, empresa_id))

            elif tipo in ["Transferência", "Correção de localização"]:
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
            flash(f"Erro ao registrar movimentação: {e}", "erro")
        finally:
            cursor.close()

        conn.close()
        return redirect(url_for("movimentacoes"))

    filtros = {
        "busca": request.args.get("busca", "").strip(),
        "tipo": request.args.get("tipo", "").strip(),
        "data_inicio": request.args.get("data_inicio", "").strip(),
        "data_fim": request.args.get("data_fim", "").strip()
    }

    lista = []
    materiais_lista = []
    resumo = {
        "entradas_hoje": 0,
        "saidas_hoje": 0,
        "transferencias_hoje": 0,
        "bloqueios_hoje": 0
    }

    grafico_semana = {
        "Seg": {"entrada": 0, "saida": 0},
        "Ter": {"entrada": 0, "saida": 0},
        "Qua": {"entrada": 0, "saida": 0},
        "Qui": {"entrada": 0, "saida": 0},
        "Sex": {"entrada": 0, "saida": 0}
    }

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT codigo, descricao, quantidade, unidade, localizacao, status
            FROM materiais
            WHERE empresa_id = %s
            ORDER BY codigo
        """, (empresa_id,))
        materiais_lista = cursor.fetchall()

        cursor.execute("""
            SELECT
                SUM(CASE WHEN tipo = 'Entrada' THEN 1 ELSE 0 END) AS entradas_hoje,
                SUM(CASE WHEN tipo = 'Saída' THEN 1 ELSE 0 END) AS saidas_hoje,
                SUM(CASE WHEN tipo = 'Transferência' THEN 1 ELSE 0 END) AS transferencias_hoje,
                SUM(CASE WHEN tipo = 'Bloqueio de material' THEN 1 ELSE 0 END) AS bloqueios_hoje
            FROM movimentacoes
            WHERE empresa_id = %s
            AND data >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        """, (empresa_id,))
        resumo_db = cursor.fetchone() or {}
        resumo = {
            "entradas_hoje": resumo_db.get("entradas_hoje") or 0,
            "saidas_hoje": resumo_db.get("saidas_hoje") or 0,
            "transferencias_hoje": resumo_db.get("transferencias_hoje") or 0,
            "bloqueios_hoje": resumo_db.get("bloqueios_hoje") or 0
        }

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

        mapa_dias = {2: "Seg", 3: "Ter", 4: "Qua", 5: "Qui", 6: "Sex"}

        for item in cursor.fetchall():
            dia = mapa_dias.get(item["dia_semana"])
            if dia:
                if item["tipo"] == "Entrada":
                    grafico_semana[dia]["entrada"] = item["total"]
                elif item["tipo"] == "Saída":
                    grafico_semana[dia]["saida"] = item["total"]

        sql = """
            SELECT m.tipo, m.material_codigo, mat.descricao AS material_descricao,
                   m.origem, m.destino, m.quantidade, m.validacao, m.data,
                   m.responsavel, m.observacao, m.criado_em
            FROM movimentacoes m
            LEFT JOIN materiais mat
              ON mat.empresa_id = m.empresa_id
             AND mat.codigo = m.material_codigo
            WHERE m.empresa_id = %s
        """
        params = [empresa_id]

        if filtros["busca"]:
            sql += """
                AND (
                    m.material_codigo LIKE %s
                    OR mat.descricao LIKE %s
                    OR m.responsavel LIKE %s
                    OR m.origem LIKE %s
                    OR m.destino LIKE %s
                )
            """
            termo = f"%{filtros['busca']}%"
            params.extend([termo, termo, termo, termo, termo])

        if filtros["tipo"]:
            sql += " AND m.tipo = %s"
            params.append(filtros["tipo"])

        if filtros["data_inicio"]:
            sql += " AND m.data >= %s"
            params.append(filtros["data_inicio"])

        if filtros["data_fim"]:
            sql += " AND m.data <= %s"
            params.append(filtros["data_fim"])

        sql += " ORDER BY m.criado_em DESC LIMIT 100"

        cursor.execute(sql, params)
        lista = cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

    altura_grafico = {}
    for dia, valores in grafico_semana.items():
        altura_grafico[dia] = {
            "entrada": max(valores["entrada"] * 20, 6),
            "saida": max(valores["saida"] * 20, 6)
        }

    return render_template(
        "movimentacoes.html",
        movimentacoes=lista,
        materiais=materiais_lista,
        filtros=filtros,
        resumo=resumo,
        altura_grafico=altura_grafico
    )


@app.route("/etiquetas", methods=["GET", "POST"])
@login_required
@perfil_required("admin", "operador")
def etiquetas():
    conn = conectar_db()
    etiquetas_lista = []
    materiais_lista = []
    resumo_etiquetas = {
        "total": 0,
        "ativas": 0,
        "pendentes": 0,
        "reimpressoes": 0
    }

    if not conn:
        flash("Erro ao conectar ao banco de dados.", "erro")
        return render_template(
            "etiquetas.html",
            etiquetas=[],
            materiais=[],
            resumo_etiquetas=resumo_etiquetas
        )

    empresa_id = session["empresa_id"]

    if request.method == "POST":
        codigo = request.form.get("codigo", "").strip()
        lote = request.form.get("lote", "").strip()
        descricao = request.form.get("descricao", "").strip()
        quantidade = request.form.get("quantidade", "").strip()
        localizacao = request.form.get("localizacao", "").strip()
        status = request.form.get("statusEtiqueta", "Gerada").strip()

        status_validos = ["Ativa", "Gerada", "Pendente", "Reimpressão"]

        if not codigo or not descricao or not quantidade or not localizacao:
            flash("Selecione um material e confirme os dados da etiqueta.", "erro")
            conn.close()
            return redirect(url_for("etiquetas"))

        if status not in status_validos:
            flash("Status da etiqueta inválido.", "erro")
            conn.close()
            return redirect(url_for("etiquetas"))

        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT codigo
                FROM materiais
                WHERE empresa_id = %s AND codigo = %s
            """, (empresa_id, codigo))
            material = cursor.fetchone()

            if not material:
                flash("Material não encontrado para gerar etiqueta.", "erro")
                return redirect(url_for("etiquetas"))

            cursor.execute("""
                INSERT INTO etiquetas
                    (empresa_id, material_codigo, lote, descricao, quantidade, localizacao, status)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s)
            """, (empresa_id, codigo, lote, descricao, quantidade, localizacao, status))

            conn.commit()
            flash("Etiqueta gerada com sucesso! Ela já está pronta para impressão ou PDF.", "sucesso")
            return redirect(url_for("etiquetas"))

        except Exception as e:
            conn.rollback()
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
            SELECT e.material_codigo, e.descricao, e.lote, e.quantidade,
                   e.localizacao, e.status, e.criado_em, m.unidade
            FROM etiquetas e
            LEFT JOIN materiais m
              ON m.empresa_id = e.empresa_id
             AND m.codigo = e.material_codigo
            WHERE e.empresa_id = %s
            ORDER BY e.criado_em DESC
        """, (empresa_id,))
        etiquetas_lista = cursor.fetchall()

        cursor.execute("""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'Ativa' THEN 1 ELSE 0 END) AS ativas,
                SUM(CASE WHEN status = 'Pendente' THEN 1 ELSE 0 END) AS pendentes,
                SUM(CASE WHEN status = 'Reimpressão' THEN 1 ELSE 0 END) AS reimpressoes
            FROM etiquetas
            WHERE empresa_id = %s
        """, (empresa_id,))
        resumo_db = cursor.fetchone() or {}
        resumo_etiquetas = {
            "total": resumo_db.get("total") or 0,
            "ativas": resumo_db.get("ativas") or 0,
            "pendentes": resumo_db.get("pendentes") or 0,
            "reimpressoes": resumo_db.get("reimpressoes") or 0
        }

    finally:
        cursor.close()
        conn.close()

    return render_template(
        "etiquetas.html",
        etiquetas=etiquetas_lista,
        materiais=materiais_lista,
        resumo_etiquetas=resumo_etiquetas
    )


@app.route("/etiquetas/pdf/<codigo>")
@login_required
@perfil_required("admin", "operador")
def baixar_etiqueta_pdf(codigo):
    conn = conectar_db()

    if not conn:
        flash("Erro ao conectar ao banco de dados.", "erro")
        return redirect(url_for("etiquetas"))

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT m.codigo, m.descricao, m.lote, m.quantidade, m.unidade,
                   m.localizacao, m.status, e.criado_em AS etiqueta_criada_em,
                   e.status AS status_etiqueta
            FROM materiais m
            LEFT JOIN etiquetas e
              ON e.empresa_id = m.empresa_id
             AND e.material_codigo = m.codigo
            WHERE m.empresa_id = %s AND m.codigo = %s
            ORDER BY e.criado_em DESC
            LIMIT 1
        """, (session["empresa_id"], codigo))
        material = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    if not material:
        flash("Material não encontrado para gerar PDF da etiqueta.", "erro")
        return redirect(url_for("etiquetas"))

    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib.utils import ImageReader
        from reportlab.pdfgen import canvas
    except Exception:
        flash("Dependência reportlab não instalada. Rode: pip install reportlab", "erro")
        return redirect(url_for("etiquetas"))

    buffer_pdf = BytesIO()
    pdf = canvas.Canvas(buffer_pdf, pagesize=A4)
    largura, altura = A4

    etiqueta_largura = 100 * mm
    etiqueta_altura = 70 * mm
    x = 18 * mm
    y = altura - etiqueta_altura - 18 * mm

    pdf.setStrokeColor(colors.HexColor("#07182c"))
    pdf.setLineWidth(1.4)
    pdf.roundRect(x, y, etiqueta_largura, etiqueta_altura, 4 * mm, stroke=1, fill=0)

    pdf.setFillColor(colors.HexColor("#07182c"))
    pdf.rect(x, y + etiqueta_altura - 13 * mm, etiqueta_largura, 13 * mm, stroke=0, fill=1)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(x + 6 * mm, y + etiqueta_altura - 8.5 * mm, "CODESTOCK")
    pdf.setFont("Helvetica", 7)
    pdf.drawRightString(x + etiqueta_largura - 6 * mm, y + etiqueta_altura - 8 * mm, "Etiqueta de identificação")

    qr_url = request.host_url + f"material/{material['codigo']}"
    qr_img = qrcode.make(qr_url)
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    qr_reader = ImageReader(qr_buffer)

    qr_size = 34 * mm
    qr_x = x + etiqueta_largura - qr_size - 7 * mm
    qr_y = y + 17 * mm
    pdf.drawImage(qr_reader, qr_x, qr_y, qr_size, qr_size, mask="auto")

    info_x = x + 6 * mm
    info_y = y + etiqueta_altura - 22 * mm
    linha = 7 * mm

    quantidade = f"{material.get('quantidade') or 0} {material.get('unidade') or ''}".strip()
    status = material.get("status_etiqueta") or material.get("status") or "Gerada"
    data_geracao = material.get("etiqueta_criada_em") or date.today()

    campos = [
        ("Código", material.get("codigo") or "-"),
        ("Material", material.get("descricao") or "-"),
        ("Lote", material.get("lote") or "-"),
        ("Quantidade", quantidade or "-"),
        ("Local", material.get("localizacao") or "-"),
        ("Status", status),
    ]

    pdf.setFillColor(colors.HexColor("#07182c"))
    for rotulo, valor in campos:
        pdf.setFont("Helvetica-Bold", 7)
        pdf.drawString(info_x, info_y, f"{rotulo}:")
        pdf.setFont("Helvetica", 8)
        texto = str(valor)
        if len(texto) > 34:
            texto = texto[:31] + "..."
        pdf.drawString(info_x + 22 * mm, info_y, texto)
        info_y -= linha

    pdf.setFont("Helvetica", 6.5)
    pdf.setFillColor(colors.HexColor("#5f6b7c"))
    pdf.drawString(x + 6 * mm, y + 7 * mm, f"Gerado em: {data_geracao}")
    pdf.drawRightString(x + etiqueta_largura - 6 * mm, y + 7 * mm, "Escaneie para abrir a ficha do material")

    pdf.showPage()
    pdf.save()
    buffer_pdf.seek(0)

    nome_arquivo = f"etiqueta_{material['codigo']}.pdf"
    return send_file(
        buffer_pdf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=nome_arquivo
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

        cursor.execute("""
            SELECT tipo, origem, destino, quantidade, data, responsavel, validacao, observacao, criado_em
            FROM movimentacoes
            WHERE empresa_id = %s AND material_codigo = %s
            ORDER BY criado_em DESC
            LIMIT 20
        """, (session["empresa_id"], codigo))

        historico = cursor.fetchall()

        return render_template(
            "material_detalhes.html",
            material=material,
            historico=historico
        )

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