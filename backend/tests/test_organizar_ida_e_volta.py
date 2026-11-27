"""Ida e volta: gerar um prompt no app e organizá-lo devolve os campos sem misturar."""

from fastapi.testclient import TestClient

from main import app
from prompt_engine import PowerRequestEngine

eng = PowerRequestEngine()
client = TestClient(app, base_url="http://127.0.0.1:8765")

PEDIDO = {
    "objetivo": "Sistema de controle de tarefas com prazo",
    "stack": "Python + SQLite",
    "entrada": "Título e prazo digitados no navegador",
    "saida": "Lista de tarefas ordenada por prazo",
    "regras": ["Salvar em SQLite", "Incluir testes; rodar offline"],
    "tratamento_erros": "Mostrar aviso se faltar o prazo",
}
CONTEXTO = "Responder em português.\nStack: TypeScript\n\nRegras:\n- Sem emojis"


def ida_e_volta(**mudancas):
    prompt = eng.gerar_prompt_final({**PEDIDO, **mudancas})["prompt_final"]
    return eng.organizar_prompt(prompt)


def test_campos_voltam_iguais_e_sem_contexto():
    r = ida_e_volta()
    assert r["campos"] == PEDIDO
    assert r["contexto"] == ""
    assert r["perguntas"] == []


def test_contexto_fica_separado_e_inteiro():
    r = ida_e_volta(contexto_fixo=CONTEXTO)
    assert r["campos"] == PEDIDO
    assert r["contexto"] == CONTEXTO


def test_contexto_nao_define_stack_ausente():
    prompt = "### Contexto\nUso Flutter.\n\n### Objetivo\nCriar um controle de gastos da casa"
    r = eng.organizar_prompt(prompt)
    assert r["campos"]["stack"] == ""
    assert r["campos"]["objetivo"] == "Criar um controle de gastos da casa"
    assert r["contexto"] == "Uso Flutter."


def test_contexto_com_titulo_do_app_dentro_nao_vaza():
    contexto = "Modelo antigo:\n\n### Objetivo\nexemplo qualquer"
    r = ida_e_volta(contexto_fixo=contexto)
    assert r["campos"] == PEDIDO
    assert r["contexto"] == contexto


def test_texto_padrao_de_erros_nao_vira_resposta():
    r = ida_e_volta(tratamento_erros="")
    assert r["campos"]["tratamento_erros"] == ""
    assert "tratamento_erros" not in r["campos_encontrados"]
    assert [p["campo"] for p in r["perguntas"]] == ["tratamento_erros"]


def test_linha_parecida_com_titulo_continua_no_campo():
    objetivo = "Criar um painel de pedidos\nErro: hoje a lista some ao recarregar"
    r = ida_e_volta(objetivo=objetivo)
    assert r["campos"]["objetivo"] == " ".join(objetivo.split("\n"))
    assert r["campos"]["tratamento_erros"] == PEDIDO["tratamento_erros"]


def test_gerar_organizar_gerar_nao_muda_o_prompt():
    prompt = eng.gerar_prompt_final(PEDIDO)["prompt_final"]
    campos = eng.organizar_prompt(prompt)["campos"]
    assert eng.gerar_prompt_final(campos)["prompt_final"] == prompt


def test_prompt_colado_com_quebra_do_windows_e_espacos_no_fim():
    prompt = eng.gerar_prompt_final({**PEDIDO, "contexto_fixo": CONTEXTO})["prompt_final"]
    r = eng.organizar_prompt(prompt.replace("\n", "  \r\n"))
    assert r["campos"] == PEDIDO


def test_prompt_editado_ainda_separa_contexto_e_tira_frase_padrao():
    prompt = eng.gerar_prompt_final({**PEDIDO, "contexto_fixo": CONTEXTO})["prompt_final"]
    r = eng.organizar_prompt(prompt + "\n\n### Padrão\nComentar em português.")
    assert r["contexto"] == CONTEXTO
    assert "Comentar em português." in r["campos"]["regras"]
    assert eng.TEXTO_PADRAO not in r["campos"]["regras"]
    assert "TypeScript" not in r["campos"]["stack"]


def test_api_devolve_contexto_sem_alterar_o_contexto_salvo(monkeypatch):
    def proibido(*args, **kwargs):
        raise AssertionError("Organizar não pode salvar o contexto fixo")

    import main

    monkeypatch.setattr(main.history_store, "salvar_config", proibido)
    prompt = eng.gerar_prompt_final({**PEDIDO, "contexto_fixo": CONTEXTO})["prompt_final"]
    r = client.post("/api/organizar-prompt", json={"texto": prompt})
    assert r.status_code == 200
    assert r.json()["contexto"] == CONTEXTO
