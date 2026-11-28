"""Hub multi-IA (BYOK + Bridge Local CLI) do Power Request com segurança estrita."""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import agy_seguro


class AIHubError(Exception):
    """Erro genérico de comunicação ou configuração no Hub de IAs."""


class AIHubSecurityError(AIHubError):
    """Erro de segurança (SSRF, command injection, injeção de cabeçalho ou provedor inválido)."""


PROVIDERS_CATALOG: dict[str, dict[str, Any]] = {
    "openrouter": {
        "nome": "OpenRouter (Várias IAs em 1 chave)",
        "descricao": "Com uma única conta você acessa Gemini, Claude, GPT e modelos gratuitos.",
        "precisa_chave": True,
        "modelo_padrao": "google/gemini-2.5-flash",
        "modelos_sugeridos": [
            "google/gemini-2.5-flash",
            "anthropic/claude-sonnet-4",
            "openai/gpt-4o-mini",
            "meta-llama/llama-3.3-70b-instruct:free",
        ],
        "link_chave": "https://openrouter.ai/keys",
        "placeholder_chave": "sk-or-v1-...",
    },
    "gemini": {
        "nome": "Google Gemini (AI Studio)",
        "descricao": "API oficial do Google Gemini, muito rápida e com cota gratuita para testes.",
        "precisa_chave": True,
        "modelo_padrao": "gemini-2.5-flash",
        "modelos_sugeridos": [
            "gemini-2.5-flash",
            "gemini-2.5-pro",
        ],
        "link_chave": "https://aistudio.google.com/apikey",
        "placeholder_chave": "AIzaSy...",
    },
    "claude": {
        "nome": "Anthropic Claude",
        "descricao": "Excelente para arquitetura de software, revisão rigorosa e código limpo.",
        "precisa_chave": True,
        "modelo_padrao": "claude-sonnet-4-20250514",
        "modelos_sugeridos": [
            "claude-sonnet-4-20250514",
            "claude-3-5-haiku-latest",
        ],
        "link_chave": "https://console.anthropic.com/settings/keys",
        "placeholder_chave": "sk-ant-...",
    },
    "openai": {
        "nome": "OpenAI (ChatGPT API)",
        "descricao": "Modelos GPT oficiais da OpenAI via chave de API.",
        "precisa_chave": True,
        "modelo_padrao": "gpt-4o-mini",
        "modelos_sugeridos": [
            "gpt-4o-mini",
            "gpt-4o",
        ],
        "link_chave": "https://platform.openai.com/api-keys",
        "placeholder_chave": "sk-proj-...",
    },
    "ollama": {
        "nome": "Ollama (IA Local — Grátis)",
        "descricao": "Roda modelos abertos localmente sem gastar nada e sem enviar dados à nuvem.",
        "precisa_chave": False,
        "modelo_padrao": "llama3.2",
        "modelos_sugeridos": [
            "llama3.2",
            "qwen2.5-coder",
            "deepseek-r1:8b",
        ],
        "link_chave": "https://ollama.com",
        "placeholder_chave": "Não precisa de chave",
    },
    "claude_cli": {
        "nome": "Claude (Local)",
        "descricao": "Usa o Claude Code já autenticado neste computador, sem precisar de chave API.",
        "precisa_chave": False,
        "modelo_padrao": "claude-cli-local",
        "modelos_sugeridos": ["claude-cli-local"],
        "link_chave": "",
        "placeholder_chave": "Usa seu login local do terminal",
    },
    "antigravity_cli": {
        "nome": "Gemini / Antigravity (Local)",
        "descricao": "Usa o Antigravity (agy) já autenticado neste computador, sem chave API. O Gemini CLI funciona só no Abrir no Terminal.",
        "precisa_chave": False,
        "modelo_padrao": "antigravity-cli-local",
        "modelos_sugeridos": ["antigravity-cli-local"],
        "link_chave": "",
        "placeholder_chave": "Usa seu login local do terminal",
    },
}

LOCAL_CLI_SPECS: dict[str, dict[str, Any]] = {
    "claude_cli": {
        "brand_id": "claude",
        "nome": "Claude (Local)",
        "binaries": ["claude"],
        # Dentro do app o Claude roda SEMPRE com CLAUDE_ARGS_PROTEGIDOS (ver _call_local_cli).
        "args": ["-p"],
        # Mínimo pedido pelo Enviar e pelo Sequenciar. Não decide nada: no Claude,
        # _call_local_cli ignora os argumentos de quem chama e usa a proteção completa.
        "send_args": ["-p", "--tools", ""],
        # No Terminal o prompt entra como argumento inicial da sessão interativa.
        "terminal_mode": "argumento",
    },
    "antigravity_cli": {
        "brand_id": "gemini",
        "nome": "Antigravity / Gemini (Local)",
        "binaries": ["agy", "gemini"],
        "args": ["-p"],
        # Sintaxe do prompt inicial varia entre agy e gemini: abre a sessão e copia o prompt.
        "terminal_mode": "area_de_transferencia",
    },
}

# Claude (Local) dentro do app: sem ferramentas internas, sem MCP e sem personalizações
# (ganchos, plugins, skills, CLAUDE.md, memória automática). Vale para todo uso dentro do app
# (Testar Conexão, revisão, otimização, Enviar e Sequenciar). Não vale para Abrir no Terminal.
# Limite (documentação oficial): ganchos impostos por política de administrador continuam valendo.
CLAUDE_ARGS_PROTEGIDOS: tuple[str, ...] = (
    "-p",
    "--safe-mode",  # desliga ganchos, plugins, skills, CLAUDE.md, memória e servidores MCP
    "--tools", "",  # nenhuma ferramenta interna (arquivos, terminal, web)
    "--strict-mcp-config",  # ignora os servidores MCP configurados (não passamos --mcp-config)
    "--disallowedTools", "mcp__*",  # e recusa qualquer ferramenta MCP que sobrar
)
PREFIXO_PASTA_CLAUDE = "power-request-claude-"
AVISO_CLAUDE_SEM_MODO_SEGURO = (
    "Sua versão do Claude (Local) não aceita o modo seguro que o app exige (sem ferramentas, "
    "sem MCP e sem ganchos). Por segurança, o app não usa o Claude sem essa proteção. "
    "No Terminal, rode claude update e use Testar Conexão de novo."
)

PROVIDER_UI_META: dict[str, dict[str, str]] = {
    "openrouter": {"auth_mode": "api_key"},
    "gemini": {"auth_mode": "api_key"},
    "claude": {"auth_mode": "api_key"},
    "openai": {"auth_mode": "api_key"},
    "ollama": {"auth_mode": "local_server", "base_url_padrao": "http://127.0.0.1:11434"},
    "claude_cli": {"auth_mode": "local_cli", "cli_command": "claude"},
    "antigravity_cli": {"auth_mode": "local_cli", "cli_command": "agy / gemini"},
}


def providers_for_ui() -> list[dict[str, Any]]:
    """Catálogo no formato consumido pelo frontend (lista com id, auth_mode, dica etc.)."""
    itens: list[dict[str, Any]] = []
    for provider_id, meta in PROVIDERS_CATALOG.items():
        ui = PROVIDER_UI_META.get(provider_id, {})
        itens.append(
            {
                "id": provider_id,
                "nome": meta["nome"],
                "auth_mode": ui.get("auth_mode", "api_key" if meta["precisa_chave"] else "local_cli"),
                "cli_command": ui.get("cli_command", ""),
                "modelo_padrao": meta["modelo_padrao"],
                "modelos_sugeridos": list(meta["modelos_sugeridos"]),
                "base_url_padrao": ui.get("base_url_padrao", ""),
                "console_url": meta["link_chave"],
                "dica": meta["descricao"],
            }
        )
    return itens


MODEL_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9._:/-]{2,120}$")
OAUTH_TOKEN_PATTERN = re.compile(r"^[a-zA-Z0-9._~-]{8,512}$")
ALLOWED_LOCAL_HOSTS = {"localhost", "127.0.0.1"}
MAX_CLI_PROMPT_CHARS = 12000
MAX_CLI_OUTPUT_CHARS = 24000

# Envio direto do prompt final para a IA (respostas longas, ex: código)
MAX_SEND_PROMPT_CHARS = 11000
SEND_MAX_TOKENS = 4096
SEND_HTTP_TIMEOUT = 300
SEND_CLI_TIMEOUT = 600
MAX_TERMINAL_PROMPT_CHARS = 100_000
TERMINAL_PASTAS_PROIBIDAS = {"library", "applications", "system", "private", "volumes"}

SEND_SYSTEM_PROMPT = "Siga com precisão o pedido do usuário e entregue o resultado completo."


class RespostaIA(str):
    """Texto da resposta da IA, com a informação de se ele chegou cortado."""

    cortada: bool = False

    def __new__(cls, texto: str, cortada: bool = False) -> "RespostaIA":
        obj = super().__new__(cls, texto)
        obj.cortada = cortada
        return obj


def parou_no_limite(provider: str, data: dict[str, Any]) -> bool:
    """True quando o provedor informa que parou por atingir o limite de tamanho."""
    try:
        if provider in {"openrouter", "openai"}:
            return data["choices"][0].get("finish_reason") == "length"
        if provider == "claude":
            return data.get("stop_reason") == "max_tokens"
        if provider == "gemini":
            return data["candidates"][0].get("finishReason") == "MAX_TOKENS"
        if provider == "ollama":
            return data.get("done_reason") == "length"
    except (KeyError, IndexError, TypeError, AttributeError):
        return False
    return False


def _build_search_path() -> str:
    """Inclui caminhos comuns do macOS (Homebrew, npm global, ~/.local/bin) no PATH de busca."""
    home = os.path.expanduser("~")
    extras = [
        "/opt/homebrew/bin",
        "/usr/local/bin",
        os.path.join(home, ".local", "bin"),
        os.path.join(home, ".npm-global", "bin"),
    ]
    current = os.environ.get("PATH", "")
    parts = [p for p in current.split(os.pathsep) if p]
    for extra in extras:
        if extra not in parts:
            parts.append(extra)
    return os.pathsep.join(parts)


class AIHubClient:
    """Cliente unificado para conectar múltiplas IAs (nuvem + CLI local) com segurança estrita."""

    DEFAULT_TIMEOUT = 30
    LOCAL_CLI_TIMEOUT = 60

    @staticmethod
    def mask_secret(secret: str) -> str:
        """Mascara chaves sensíveis para exibição segura."""
        if not secret:
            return ""
        clean = secret.strip()
        if len(clean) <= 8:
            return "****"
        return f"{clean[:4]}...{clean[-4:]}"

    @staticmethod
    def _scrub_secret(mensagem: str, secret: str) -> str:
        """Garante que a chave API nunca vaze em mensagens de erro ou logs."""
        if secret and secret in mensagem:
            return mensagem.replace(secret, "[CHAVE_OCULTA]")
        return mensagem

    @staticmethod
    def _resolve_local_binary(provider: str) -> tuple[str | None, str | None]:
        """Resolve apenas binários da allowlist fixa (nunca aceita caminho externo do usuário)."""
        spec = LOCAL_CLI_SPECS.get(provider)
        if not spec:
            return None, None
        search_path = _build_search_path()
        for binary_name in spec["binaries"]:
            found = shutil.which(binary_name, path=search_path)
            if found:
                return binary_name, found
        return None, None

    def detectar_ferramentas_locais(self) -> dict[str, Any]:
        """Inspeciona quais CLIs oficiais (Claude, Antigravity/Gemini, Ollama) estão no Mac."""
        resultado: dict[str, Any] = {}
        for provider, spec in LOCAL_CLI_SPECS.items():
            binary_name, binary_path = self._resolve_local_binary(provider)
            resultado[provider] = {
                "disponivel": binary_path is not None,
                "brand_id": spec["brand_id"],
                "nome": spec["nome"],
                "comando_detectado": binary_name or "",
            }

        ollama_path = shutil.which("ollama", path=_build_search_path())
        resultado["ollama"] = {
            "disponivel": ollama_path is not None,
            "brand_id": "ollama",
            "nome": "Ollama (IA Local)",
            "comando_detectado": "ollama" if ollama_path else "",
        }
        return resultado

    def ferramentas_locais_para_ui(self) -> list[dict[str, Any]]:
        """Ferramentas locais no formato consumido pelo frontend (provider_id, command, installed)."""
        return [
            {
                "provider_id": provider_id,
                "command": info["comando_detectado"],
                "installed": bool(info["disponivel"]),
            }
            for provider_id, info in self.detectar_ferramentas_locais().items()
        ]

    def validate_config(self, config: dict[str, Any]) -> dict[str, str]:
        """Valida provedor, modelo, chave e bloqueia SSRF, command injection e header injection."""
        provider = str(config.get("provider", "")).strip().lower()
        if provider not in PROVIDERS_CATALOG:
            raise AIHubSecurityError(f"Provedor não suportado: '{provider}'.")

        meta = PROVIDERS_CATALOG[provider]
        api_key = str(config.get("api_key", "")).strip()
        model = str(config.get("model", "")).strip() or meta["modelo_padrao"]
        alias = str(config.get("alias", "")).strip() or meta["nome"]
        base_url = str(config.get("base_url", "")).strip()

        if any(c in api_key for c in ["\r", "\n", "\x00"]) or " " in api_key:
            raise AIHubSecurityError("A chave API contém caracteres inválidos.")

        if len(api_key) > 300:
            raise AIHubSecurityError("A chave API excede o tamanho máximo permitido.")

        if meta["precisa_chave"] and not api_key:
            raise AIHubError(f"Informe a chave API para conectar em {meta['nome']}.")

        if ".." in model or not MODEL_NAME_PATTERN.match(model):
            raise AIHubSecurityError(f"Nome de modelo inválido ou inseguro: '{model}'.")

        validated_url = ""
        if provider == "ollama":
            raw_url = base_url or "http://127.0.0.1:11434"
            parsed = urllib.parse.urlparse(raw_url)
            if parsed.scheme not in {"http", "https"} or parsed.hostname not in ALLOWED_LOCAL_HOSTS:
                raise AIHubSecurityError(
                    "Por segurança (proteção SSRF), o Ollama só pode apontar para localhost ou 127.0.0.1."
                )
            validated_url = raw_url.rstrip("/")

        if provider in LOCAL_CLI_SPECS and base_url:
            raise AIHubSecurityError(
                "Por segurança, conectores locais do terminal não aceitam caminhos ou URLs personalizadas."
            )

        limpo = {
            "provider": provider,
            "api_key": api_key,
            "model": model,
            "alias": alias[:60],
            "base_url": validated_url,
        }
        # Aceite do aviso de ganchos globais: só vale o booleano True.
        if provider == "antigravity_cli" and config.get("aceito_ganchos") is True:
            limpo["aceito_ganchos"] = True
        return limpo

    def _call_local_cli(
        self,
        cfg: dict[str, str],
        system_prompt: str,
        user_prompt: str,
        timeout: int | None = None,
        cwd: str | None = None,
        cli_args: list[str] | None = None,
    ) -> str:
        """Executa o CLI local autenticado via stdin com shell=False e allowlist estrita."""
        provider = cfg["provider"]
        spec = LOCAL_CLI_SPECS.get(provider)
        if not spec:
            raise AIHubSecurityError(f"Conector local inválido: '{provider}'.")

        binary_name, binary_path = self._resolve_local_binary(provider)
        if not binary_path:
            esperados = " ou ".join(spec["binaries"])
            raise AIHubError(
                f"{spec['nome']} não foi encontrado neste computador (comando esperado: {esperados})."
            )

        combined_prompt = (
            f"[INSTRUÇÕES DO SISTEMA]\n{system_prompt}\n\n"
            f"[PEDIDO DO USUÁRIO]\n{user_prompt}\n"
        )
        if "\x00" in combined_prompt:
            raise AIHubSecurityError("Entrada contém byte nulo não permitido.")
        if len(combined_prompt) > MAX_CLI_PROMPT_CHARS:
            raise AIHubSecurityError(
                f"Entrada excede o limite de segurança ({MAX_CLI_PROMPT_CHARS} caracteres) para execução local."
            )

        env = self._ambiente_cli()

        if provider == "antigravity_cli":
            return self._call_agy(cfg, binary_name, binary_path, combined_prompt, env, timeout)

        # Ponto único da proteção do Claude: quem chama não escolhe os argumentos nem a pasta.
        # `cli_args` e `cwd` ficam na assinatura só por compatibilidade e são ignorados aqui.
        del cli_args, cwd
        if provider != "claude_cli":  # CLI novo precisa de trava própria, testada, antes de entrar
            raise AIHubSecurityError(f"Conector local sem trava de segurança: '{provider}'.")
        cmd = [binary_path, *CLAUDE_ARGS_PROTEGIDOS]
        env["CLAUDE_CODE_SAFE_MODE"] = "1"  # reforço do --safe-mode
        limite = timeout or self.LOCAL_CLI_TIMEOUT
        # Pasta nova e vazia a cada uso; apagada ao terminar, inclusive em erro ou tempo esgotado.
        with tempfile.TemporaryDirectory(prefix=PREFIXO_PASTA_CLAUDE) as pasta_isolada:
            try:
                proc = subprocess.run(
                    cmd,
                    input=combined_prompt,
                    capture_output=True,
                    text=True,
                    timeout=limite,
                    shell=False,
                    env=env,
                    cwd=pasta_isolada,
                )
            except subprocess.TimeoutExpired:
                raise AIHubError(
                    f"Tempo esgotado ({limite}s) aguardando resposta de {cfg['alias']}."
                ) from None
            except OSError as exc:
                raise AIHubError(f"Falha ao executar {binary_name} localmente: {exc}") from None

        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()

        if proc.returncode != 0:
            # Opção recusada = versão sem o modo seguro. Nunca tenta de novo sem a proteção.
            if "unknown option" in f"{stderr}\n{stdout}".lower():
                raise AIHubError(AVISO_CLAUDE_SEM_MODO_SEGURO)
            detalhe = (stderr or stdout or "verifique se você já fez login no terminal")[:280]
            raise AIHubError(f"{cfg['alias']} retornou erro (código {proc.returncode}): {detalhe}")

        if not stdout:
            raise AIHubError(f"{cfg['alias']} não retornou texto na resposta.")

        return RespostaIA(stdout[:MAX_CLI_OUTPUT_CHARS], len(stdout) > MAX_CLI_OUTPUT_CHARS)

    @staticmethod
    def _ambiente_cli() -> dict[str, str]:
        env = os.environ.copy()
        env["PATH"] = _build_search_path()
        env["NO_COLOR"] = "1"
        env["TERM"] = "dumb"
        return env

    @staticmethod
    def _exigir_agy(binary_name: str) -> None:
        if binary_name != "agy":
            raise AIHubError(
                "O Gemini CLI não é usado dentro do app, porque a trava de ferramentas não foi "
                "testada nele. Instale o Antigravity (agy) ou use Abrir no Terminal."
            )

    def _call_agy(
        self,
        cfg: dict[str, Any],
        binary_name: str,
        binary_path: str,
        texto: str,
        env: dict[str, str],
        timeout: int | None,
    ) -> str:
        """Antigravity: sem argumentos com o pedido, pasta própria e ferramentas travadas."""
        self._exigir_agy(binary_name)
        if agy_seguro.tem_ganchos_globais() and cfg.get("aceito_ganchos") is not True:
            raise AIHubError(agy_seguro.AVISO_GANCHOS)
        try:
            resposta = agy_seguro.enviar(binary_path, texto, timeout or self.LOCAL_CLI_TIMEOUT, env)
        except agy_seguro.AgyFalha as exc:
            raise AIHubError(str(exc)) from None
        return RespostaIA(resposta[:MAX_CLI_OUTPUT_CHARS], len(resposta) > MAX_CLI_OUTPUT_CHARS)

    def _testar_agy(self, cfg: dict[str, Any]) -> dict[str, Any]:
        """O teste de conexão do Antigravity é a própria prova da trava (só dados falsos)."""
        binary_name, binary_path = self._resolve_local_binary("antigravity_cli")
        if not binary_path:
            raise AIHubError(
                "Antigravity não foi encontrado neste computador (comando esperado: agy)."
            )
        self._exigir_agy(binary_name)
        try:
            agy_seguro.provar_trava(binary_path, self.LOCAL_CLI_TIMEOUT, self._ambiente_cli())
        except agy_seguro.AgyFalha as exc:
            raise AIHubError(str(exc)) from None
        return {
            "conectado": True,
            "alias": cfg["alias"],
            "provider": cfg["provider"],
            "model": cfg["model"],
            "resposta": "OK",
            "mensagem": f"{cfg['alias']} respondeu e a trava de ferramentas foi conferida.",
            "ganchos_globais": agy_seguro.tem_ganchos_globais(),
        }

    def _build_request(
        self,
        cfg: dict[str, str],
        system_prompt: str,
        user_prompt: str,
        max_tokens: int | None = None,
    ) -> urllib.request.Request:
        provider = cfg["provider"]
        api_key = cfg["api_key"]
        model = cfg["model"]

        if provider in {"openrouter", "openai"}:
            url = (
                "https://openrouter.ai/api/v1/chat/completions"
                if provider == "openrouter"
                else "https://api.openai.com/v1/chat/completions"
            )
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            }
            if provider == "openrouter":
                headers["HTTP-Referer"] = "http://localhost:5173"
                headers["X-Title"] = "Power Request"
            body = {
                "model": model,
                "temperature": 0.2,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            }
            if max_tokens:
                body["max_tokens"] = max_tokens
            return urllib.request.Request(
                url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST"
            )

        if provider == "claude":
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            }
            body = {
                "model": model,
                "max_tokens": max_tokens or 900,
                "temperature": 0.2,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            }
            return urllib.request.Request(
                url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST"
            )

        if provider == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            }
            body = {
                "system_instruction": {"parts": [{"text": system_prompt}]},
                "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
                "generationConfig": {
                    "temperature": 0.2,
                    **({"maxOutputTokens": max_tokens} if max_tokens else {}),
                },
            }
            return urllib.request.Request(
                url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST"
            )

        if provider == "ollama":
            url = f"{cfg['base_url']}/api/chat"
            headers = {"Content-Type": "application/json"}
            body = {
                "model": model,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                **({"options": {"num_predict": max_tokens}} if max_tokens else {}),
            }
            return urllib.request.Request(
                url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST"
            )

        raise AIHubSecurityError(f"Provedor não suportado: '{provider}'.")

    @staticmethod
    def _extract_text(provider: str, data: dict[str, Any]) -> str:
        try:
            if provider in {"openrouter", "openai"}:
                return str(data["choices"][0]["message"]["content"]).strip()
            if provider == "claude":
                return str(data["content"][0]["text"]).strip()
            if provider == "gemini":
                return str(data["candidates"][0]["content"]["parts"][0]["text"]).strip()
            if provider == "ollama":
                return str(data["message"]["content"]).strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise AIHubError(f"Resposta inesperada do provedor {provider}.") from exc
        raise AIHubError(f"Não foi possível ler a resposta de {provider}.")

    def call_llm(
        self,
        config: dict[str, Any],
        system_prompt: str,
        user_prompt: str,
        *,
        max_tokens: int | None = None,
        timeout: int | None = None,
        cwd: str | None = None,
        cli_args: list[str] | None = None,
    ) -> str:
        """Executa a chamada ao modelo ativo no Hub (nuvem ou CLI local)."""
        cfg = self.validate_config(config)

        if cfg["provider"] in LOCAL_CLI_SPECS:
            return self._call_local_cli(
                cfg, system_prompt, user_prompt, timeout=timeout, cwd=cwd, cli_args=cli_args
            )

        req = self._build_request(cfg, system_prompt, user_prompt, max_tokens=max_tokens)
        try:
            with urllib.request.urlopen(req, timeout=timeout or self.DEFAULT_TIMEOUT) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                data = json.loads(raw)
                return RespostaIA(
                    self._extract_text(cfg["provider"], data),
                    parou_no_limite(cfg["provider"], data),
                )
        except urllib.error.HTTPError as exc:
            try:
                detalhe = exc.read().decode("utf-8", errors="replace")[:250]
            except Exception:
                detalhe = str(exc.reason)
            msg = self._scrub_secret(
                f"Erro HTTP {exc.code} ao chamar {cfg['alias']}: {detalhe}",
                cfg["api_key"],
            )
            raise AIHubError(msg) from None
        except urllib.error.URLError as exc:
            msg = self._scrub_secret(
                f"Não foi possível conectar em {cfg['alias']}: {exc.reason}",
                cfg["api_key"],
            )
            raise AIHubError(msg) from None
        except Exception as exc:
            msg = self._scrub_secret(
                f"Falha ao consultar {cfg['alias']}: {exc}",
                cfg["api_key"],
            )
            raise AIHubError(msg) from None

    def testar_conexao(self, config: dict[str, Any]) -> dict[str, Any]:
        """Envia um ping mínimo para confirmar se a IA (nuvem ou local) está respondendo."""
        cfg = self.validate_config(config)
        if cfg["provider"] == "antigravity_cli":
            return self._testar_agy(cfg)
        resposta = self.call_llm(
            cfg,
            system_prompt="Responda apenas com a palavra OK.",
            user_prompt="Teste de conexão.",
        )
        return {
            "conectado": True,
            "alias": cfg["alias"],
            "provider": cfg["provider"],
            "model": cfg["model"],
            "resposta": resposta[:60],
            "mensagem": f"{cfg['alias']} respondeu ({cfg['model']}).",
        }

    def enviar_prompt(self, config: dict[str, Any], prompt: str) -> dict[str, Any]:
        """Envia o prompt final para a IA ativa e devolve a resposta completa."""
        cfg = self.validate_config(config)
        texto = (prompt or "").strip()
        if not texto:
            raise AIHubError("Não há prompt para enviar.")
        if len(texto) > MAX_SEND_PROMPT_CHARS:
            raise AIHubError(
                f"O prompt tem mais de {MAX_SEND_PROMPT_CHARS} caracteres. Reduza o pedido antes de enviar."
            )

        # CLIs locais rodam numa pasta nova e vazia (apagada ao terminar), sem acesso aos
        # arquivos do projeto e, quando o CLI permite, sem ferramentas.
        spec = LOCAL_CLI_SPECS.get(cfg["provider"], {})
        with tempfile.TemporaryDirectory(prefix="power-request-") as pasta_isolada:
            resposta = self.call_llm(
                cfg,
                SEND_SYSTEM_PROMPT,
                texto,
                max_tokens=SEND_MAX_TOKENS,
                timeout=SEND_CLI_TIMEOUT if spec else SEND_HTTP_TIMEOUT,
                cwd=pasta_isolada,
                cli_args=spec.get("send_args"),
            )
        return {
            "resposta": str(resposta),
            "cortada": bool(getattr(resposta, "cortada", False)),
            "alias": cfg["alias"],
            "provider": cfg["provider"],
            "model": cfg["model"],
        }

    @staticmethod
    def validar_pasta_terminal(pasta: str) -> Path:
        """Aceita só pastas dentro da home (cria se não existir), sem ocultas nem de sistema."""
        texto = (pasta or "").strip()
        if not texto or len(texto) > 500 or any(ord(c) < 32 for c in texto):
            raise AIHubError("Informe uma pasta válida para abrir o Terminal.")
        home = Path.home().resolve()
        caminho = Path(texto).expanduser()
        if not caminho.is_absolute():
            caminho = home / caminho
        caminho = caminho.resolve()
        try:
            relativo = caminho.relative_to(home)
        except ValueError:
            raise AIHubSecurityError("Use uma pasta dentro da sua pasta de usuário.") from None
        partes = relativo.parts
        if not partes:
            raise AIHubSecurityError("Escolha uma subpasta (ex.: Desktop/meu-projeto), não a pasta de usuário inteira.")
        if any(p.startswith(".") for p in partes) or partes[0].lower() in TERMINAL_PASTAS_PROIBIDAS:
            raise AIHubSecurityError("Essa pasta é oculta ou de sistema e não pode ser usada.")
        try:
            caminho.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise AIHubError(f"Não foi possível usar a pasta: {exc.strerror or exc}") from None
        return caminho

    def abrir_no_terminal(self, config: dict[str, Any], prompt: str, pasta: str) -> dict[str, Any]:
        """Abre o Terminal do macOS na pasta, com a IA local já iniciada (com todas as ferramentas).

        O prompt nunca vai dentro de um comando de shell: fica num arquivo temporário privado
        (0600) que o script lê e apaga antes de iniciar a IA.
        """
        if sys.platform != "darwin":
            raise AIHubError("Abrir no Terminal está disponível apenas no macOS.")
        cfg = self.validate_config(config)
        provider = cfg["provider"]
        spec = LOCAL_CLI_SPECS.get(provider)
        if not spec:
            raise AIHubError("Abrir no Terminal só funciona com IAs locais (Claude ou Antigravity/Gemini).")
        texto = (prompt or "").strip()
        if not texto:
            raise AIHubError("Não há prompt para enviar.")
        if len(texto) > MAX_TERMINAL_PROMPT_CHARS:
            raise AIHubError(f"O prompt tem mais de {MAX_TERMINAL_PROMPT_CHARS} caracteres.")
        if "\x00" in texto:
            raise AIHubSecurityError("Entrada contém byte nulo não permitido.")

        binary_name, binary_path = self._resolve_local_binary(provider)
        if not binary_path:
            raise AIHubError(f"{spec['nome']} não foi encontrado neste computador.")
        modo = spec["terminal_mode"]
        # Como argumento, um texto que começa com "-" seria lido pelo programa como opção
        # (ex.: uma que desliga os pedidos de permissão). Recusa antes de criar qualquer coisa.
        if modo == "argumento" and texto.startswith("-"):
            raise AIHubSecurityError(
                'Por segurança, o Abrir no Terminal não aceita um prompt que começa com "-", porque '
                "o programa poderia entender o texto como um comando dele. Apague o \"-\" do começo "
                "ou escreva uma frase antes."
            )
        # Uma palavra só (ex.: "update") pode ser lida como um subcomando do programa.
        if modo == "argumento" and len(texto.split()) < 2:
            raise AIHubSecurityError(
                "Por segurança, o Abrir no Terminal não aceita um prompt de uma palavra só, porque o "
                "programa poderia entender a palavra como um comando dele. Escreva uma frase."
            )
        destino = self.validar_pasta_terminal(pasta)

        env_path = _build_search_path()
        if modo == "area_de_transferencia":
            try:
                subprocess.run(
                    ["pbcopy"], input=texto, text=True, timeout=10, shell=False, check=True
                )
            except (OSError, subprocess.SubprocessError):
                raise AIHubError("Não foi possível copiar o prompt para a área de transferência.") from None

        pasta_tmp = tempfile.mkdtemp(prefix="power-request-term-")  # permissão 0700
        os.chmod(pasta_tmp, 0o700)
        arquivo_prompt = os.path.join(pasta_tmp, "prompt.txt")
        script = os.path.join(pasta_tmp, "abrir.command")
        try:
            if modo == "argumento":
                fd = os.open(arquivo_prompt, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(texto)
                inicio = (
                    f"PROMPT=$(cat {shlex.quote(arquivo_prompt)})\n"
                    f"rm -rf {shlex.quote(pasta_tmp)}\n"
                    f'exec {shlex.quote(binary_path)} "$PROMPT"\n'
                )
            else:
                inicio = (
                    f"rm -rf {shlex.quote(pasta_tmp)}\n"
                    'echo "Prompt copiado. Cole com Cmd+V quando a IA abrir."\n'
                    f"exec {shlex.quote(binary_path)}\n"
                )
            conteudo = (
                "#!/bin/bash\n"
                f"export PATH={shlex.quote(env_path)}\n"
                f"cd {shlex.quote(str(destino))} || exit 1\n"
                "clear\n" + inicio
            )
            fd = os.open(script, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o700)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(conteudo)
            subprocess.run(
                ["open", "-a", "Terminal", script], timeout=15, shell=False, check=True
            )
        except (OSError, subprocess.SubprocessError):
            shutil.rmtree(pasta_tmp, ignore_errors=True)
            raise AIHubError("Não foi possível abrir o Terminal.") from None
        return {
            "aberto": True,
            "modo": modo,
            "pasta": str(destino),
            "alias": cfg["alias"],
            "provider": provider,
        }

    @staticmethod
    def _extrair_json(texto: str) -> dict[str, Any]:
        limpo = texto.strip()
        fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", limpo, flags=re.DOTALL)
        if fence:
            limpo = fence.group(1)
        else:
            obj = re.search(r"(\{.*\})", limpo, flags=re.DOTALL)
            if obj:
                limpo = obj.group(1)
        return json.loads(limpo)

    def revisar_com_ia(
        self,
        config: dict[str, Any],
        payload_limpo: dict[str, Any],
        revisao_local: dict[str, Any],
    ) -> dict[str, Any]:
        """Regra 3 turbinada: combina validação local rigorosa com revisão de arquiteto via IA."""
        cfg = self.validate_config(config)
        system_prompt = (
            "Você é um arquiteto de software sênior revisando uma especificação técnica para economizar tokens "
            "e aumentar a assertividade do código gerado. Responda EXCLUSIVAMENTE em JSON válido no formato: "
            '{"score_qualidade": 0-100, "pendencias": ["lista curta de lacunas reais em português simples"], '
            '"dica_extra": "1 dica prática e objetiva em até 2 frases"}. '
            "Não invente burocracia; se o pedido estiver claro e coerente, retorne lista de pendencias vazia."
        )
        user_prompt = json.dumps(payload_limpo, ensure_ascii=False)

        texto = self.call_llm(cfg, system_prompt, user_prompt)
        try:
            ia_json = self._extrair_json(texto)
            pendencias_ia = [
                str(p).strip()
                for p in ia_json.get("pendencias", [])
                if isinstance(p, str) and p.strip()
            ][:5]
            score_ia = int(ia_json.get("score_qualidade", revisao_local["score_qualidade"]))
            score_ia = max(0, min(100, score_ia))
            dica_extra = str(ia_json.get("dica_extra", "")).strip()[:400]
        except Exception:
            pendencias_ia = []
            score_ia = revisao_local["score_qualidade"]
            dica_extra = texto[:300]

        todas_pendencias = list(dict.fromkeys(revisao_local["pendencias"] + pendencias_ia))
        score_final = min(revisao_local["score_qualidade"], score_ia) if todas_pendencias else score_ia

        return {
            "aprovado": len(todas_pendencias) == 0,
            "score_qualidade": score_final,
            "pendencias": todas_pendencias,
            "dica_extra": dica_extra,
            "revisado_por": f"{cfg['alias']} ({cfg['model']})",
        }

    def otimizar_prompt_com_ia(self, config: dict[str, Any], prompt_base: str) -> dict[str, Any]:
        """Regra 4 opcional: compacta e lapida o prompt mantendo todas as regras e economizando tokens."""
        cfg = self.validate_config(config)
        system_prompt = (
            "Você é um especialista em compactação de prompts de engenharia de software. "
            "Reescreva o prompt recebido mantendo TODAS as exigências, tornando-o ainda mais direto, "
            "sem ambiguidades e usando menos tokens. Retorne APENAS o prompt final em Markdown limpo, "
            "sem saudações nem explicações extras."
        )
        otimizado = self.call_llm(cfg, system_prompt, prompt_base)
        tokens_estimados = max(1, int(len(otimizado.split()) * 1.35))
        return {
            "prompt_final": otimizado.strip(),
            "tokens_estimados": tokens_estimados,
            "gerado_por": f"{cfg['alias']} ({cfg['model']})",
        }


def exchange_openrouter_oauth_code(code: str, code_verifier: str) -> dict[str, str]:
    """Troca o código de autorização OAuth PKCE por uma credencial de acesso do OpenRouter."""
    clean_code = str(code or "").strip()
    clean_verifier = str(code_verifier or "").strip()

    if not OAUTH_TOKEN_PATTERN.match(clean_code):
        raise AIHubSecurityError("Código de autorização inválido.")
    if not OAUTH_TOKEN_PATTERN.match(clean_verifier):
        raise AIHubSecurityError("Verificador de segurança PKCE inválido.")

    url = "https://openrouter.ai/api/v1/auth/keys"
    body = {
        "code": clean_code,
        "code_verifier": clean_verifier,
        "code_challenge_method": "S256",
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=AIHubClient.DEFAULT_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
            api_key = str(data.get("key", "")).strip()
            if not api_key:
                raise AIHubError("A autorização não retornou uma credencial válida.")
            return {"api_key": api_key}
    except urllib.error.HTTPError as exc:
        try:
            detalhe = exc.read().decode("utf-8", errors="replace")[:200]
        except Exception:
            detalhe = str(exc.reason)
        raise AIHubError(f"Autorização recusada (HTTP {exc.code}): {detalhe}") from None
    except urllib.error.URLError as exc:
        raise AIHubError(f"Não foi possível concluir o login no navegador: {exc.reason}") from None
