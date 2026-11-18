"""Filtro de injeção: variáveis simples de template passam; expressões continuam bloqueadas."""

import pytest

from prompt_engine import PowerRequestEngine, SecurityError

engine = PowerRequestEngine()


def _checar(texto: str) -> str:
    return engine._sanitizar_e_validar_seguranca(texto, "objetivo")


@pytest.mark.parametrize(
    "texto",
    [
        "Enviar mensagem 'Olá, {{nome}}!' ao cliente",
        "Usar {{ cliente.email }} no assunto do e-mail",
        "Template com {{primeiro_nome}} e {{valor_parcela}}",
        "Chaves simples { assim } não são template",
    ],
)
def test_variaveis_simples_de_template_sao_permitidas(texto):
    assert _checar(texto) == texto


@pytest.mark.parametrize(
    "ataque",
    [
        "{{7*7}}",
        "{{ 7 * 7 }}",
        "Olá {{config.items()}}",
        "{{__class__.__mro__}}",
        "{{ self.__init__ }}",
        "{{''.join(x)}}",
        "{{}}",
        "{{\nimport os\n}}",
        "{{nome}} e depois {{7*7}}",
    ],
)
def test_expressoes_em_chaves_duplas_continuam_bloqueadas(ataque):
    with pytest.raises(SecurityError):
        _checar(ataque)
