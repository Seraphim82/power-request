"""Hub multi-IA (BYOK + Bridge Local CLI) do Power Request com segurança estrita."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


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
        "descricao": "Usa o Antigravity (agy) ou Gemini CLI já autenticado neste computador, sem chave API.",
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
        "args": ["-p"],
    },
    "antigravity_cli": {
        "brand_id": "gemini",
        "nome": "Antigravity / Gemini (Local)",
        "binaries": ["agy", "gemini"],
        "args": ["-p"],
    },
}

MODEL_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9._:/-]{2,120}$")
OAUTH_TOKEN_PATTERN = re.compile(r"^[a-zA-Z0-9._~-]{8,512}$")
ALLOWED_LOCAL_HOSTS = {"localhost", "127.0.0.1"}
MAX_CLI_PROMPT_CHARS = 12000
MAX_CLI_OUTPUT_CHARS = 24000


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

        return {
            "provider": provider,
            "api_key": api_key,
            "model": model,
            "alias": alias[:60],
            "base_url": validated_url,
        }

    def _call_local_cli(self, cfg: dict[str, str], system_prompt: str, user_prompt: str) -> str:
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

        env = os.environ.copy()
        env["PATH"] = _build_search_path()
        env["NO_COLOR"] = "1"
        env["TERM"] = "dumb"

        cmd = [binary_path, *spec["args"]]
        try:
            proc = subprocess.run(
                cmd,
                input=combined_prompt,
                capture_output=True,
                text=True,
                timeout=self.LOCAL_CLI_TIMEOUT,
                shell=False,
                env=env,
            )
        except subprocess.TimeoutExpired:
            raise AIHubError(
                f"Tempo esgotado ({self.LOCAL_CLI_TIMEOUT}s) aguardando resposta de {cfg['alias']}."
            ) from None
        except OSError as exc:
            raise AIHubError(f"Falha ao executar {binary_name} localmente: {exc}") from None

        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()

        if proc.returncode != 0:
            detalhe = (stderr or stdout or "verifique se você já fez login no terminal")[:280]
            raise AIHubError(f"{cfg['alias']} retornou erro (código {proc.returncode}): {detalhe}")

        if not stdout:
            raise AIHubError(f"{cfg['alias']} não retornou texto na resposta.")

        return stdout[:MAX_CLI_OUTPUT_CHARS]

    def _build_request(
        self, cfg: dict[str, str], system_prompt: str, user_prompt: str
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
                "max_tokens": 900,
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
                "generationConfig": {"temperature": 0.2},
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

    def call_llm(self, config: dict[str, Any], system_prompt: str, user_prompt: str) -> str:
        """Executa a chamada ao modelo ativo no Hub (nuvem ou CLI local)."""
        cfg = self.validate_config(config)

        if cfg["provider"] in LOCAL_CLI_SPECS:
            return self._call_local_cli(cfg, system_prompt, user_prompt)

        req = self._build_request(cfg, system_prompt, user_prompt)
        try:
            with urllib.request.urlopen(req, timeout=self.DEFAULT_TIMEOUT) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                data = json.loads(raw)
                return self._extract_text(cfg["provider"], data)
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
