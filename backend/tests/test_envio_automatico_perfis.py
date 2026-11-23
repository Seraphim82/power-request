"""Perfis de sites: ChatGPT entra como não validado; Claude segue validado (testes novos)."""

import envio_automatico as ea


def test_perfil_chatgpt_existe_e_cola_com_comando_v():
    p = ea.carregar_perfis()["chatgpt"]
    assert p["dominio"] == "chatgpt.com"
    assert p["url_nova"].startswith("https://chatgpt.com")
    assert p["url_conversa_prefixo"] == "https://chatgpt.com/c/"
    assert p["parametro_texto"] is None  # mesmo caminho validado no Claude: abrir, ⌘V, Enter


def test_chatgpt_marcado_nao_validado_e_claude_validado():
    perfis = ea.carregar_perfis()
    assert perfis["claude"]["validado_no_mac"] is True
    assert perfis["chatgpt"]["validado_no_mac"] is False
    ui = ea.perfis_para_ui()
    assert ui["nao_validados"] == ["chatgpt"]
    assert {"chave": "chatgpt", "nome": "ChatGPT"} in ui["perfis"]


def test_validado_so_vale_com_true_literal(tmp_path):
    bruto = ea.carregar_perfis()["chatgpt"] | {"validado_no_mac": "sim"}
    arq = tmp_path / "p.json"
    import json
    arq.write_text(json.dumps({"x": {**bruto, "validado_no_mac": "sim"}}))
    assert ea.carregar_perfis(arq)["x"]["validado_no_mac"] is False
