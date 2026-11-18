"""Motor de regras, validação, revisão e segurança do Power Request."""

from __future__ import annotations

import re
from typing import Any


class ValidationError(Exception):
    """Lançada quando uma etapa obrigatória não cumpre as regras sequenciais."""


class SecurityError(Exception):
    """Lançada quando uma tentativa de sabotagem ou injeção é detectada."""


class PowerRequestEngine:
    """Orquestrador de engenharia de prompt guiada focado em economia de tokens."""

    MAX_FIELD_LENGTH = 2000

    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
        r"ignore\s+(todas\s+as\s+)?instru[çc][õo]es\s+anteriores",
        r"desconsidere\s+(tudo|todas\s+as\s+regras)",
        r"<\s*script\b",
        r"javascript\s*:",
        r"\{\{.*\}\}",
    ]

    BASE_EDUCACIONAL: dict[str, dict[str, Any]] = {
        "bots": {
            "titulo": "Bot de Mensagens (WhatsApp, Telegram ou Chat)",
            "guia": (
                "Ferramentas mais usadas para criar bots de WhatsApp e mensagens:\n"
                "• Python + WhatsApp Cloud API (Oficial): Conexão oficial da Meta, segura e sem risco de bloqueio.\n"
                "• Node.js + Evolution API / Baileys: Muito usado para automações rápidas via QR Code.\n"
                "• Python + Telegram Bot API: Gratuito, rápido e excelente para bots internos ou de atendimento.\n"
                "• Não sei escolher: Deixe a IA indicar a opção mais simples e segura para o seu caso."
            ),
            "sugestoes_stack": [
                "Python + WhatsApp Cloud API (Oficial Meta)",
                "Node.js + Evolution API",
                "Python + Telegram Bot API",
                "Deixar a IA escolher a melhor opção para bot",
            ],
            "guia_campos": {
                "objetivo": {
                    "titulo": "1. O que o seu bot precisa fazer?",
                    "explicacao": "Explique qual atendimento ou tarefa o bot vai assumir automaticamente nas conversas.",
                    "placeholder": "Ex: Criar um mini bot de WhatsApp para responder dúvidas frequentes e enviar orçamento",
                    "sugestoes": [],
                },
                "stack": {
                    "titulo": "2. Qual ferramenta usar para conectar o bot?",
                    "explicacao": "Bots de WhatsApp rodam em um servidor (não como app de celular). Clique na opção que faz mais sentido para você.",
                    "placeholder": "Ex: Python + WhatsApp Cloud API (Oficial Meta)",
                    "sugestoes": [
                        "Python + WhatsApp Cloud API (Oficial Meta)",
                        "Node.js + Evolution API",
                        "Python + Telegram Bot API",
                        "Deixar a IA escolher a melhor opção para bot",
                    ],
                },
                "entrada": {
                    "titulo": "3. O que o cliente envia para ativar o bot? (Entrada)",
                    "explicacao": "Diga como a conversa começa: uma palavra-chave, uma pergunta livre, um número de menu ou um arquivo.",
                    "placeholder": "Ex: O cliente manda 'Oi' ou escolhe uma opção digitando 1, 2 ou 3",
                    "sugestoes": [
                        "Mensagem de texto livre do cliente",
                        "Menu numerado (digitar 1, 2 ou 3)",
                        "Palavras-chave específicas (ex: 'preço', 'horário')",
                        "Envio de imagem ou documento pelo cliente",
                    ],
                },
                "saida": {
                    "titulo": "4. Como o bot responde ou o que ele registra? (Resultado)",
                    "explicacao": "Descreva o que o bot devolve no chat e se ele salva os dados do cliente em algum lugar.",
                    "placeholder": "Ex: Responde com texto pronto, envia catálogo em PDF e salva o contato em uma planilha",
                    "sugestoes": [
                        "Resposta automática em texto no próprio chat",
                        "Envio de menu com opções ou catálogo em PDF",
                        "Salvar nome e pedido do cliente em planilha ou banco",
                        "Transferir para atendimento humano quando necessário",
                    ],
                },
                "regras": {
                    "titulo": "5. Regras de atendimento do bot",
                    "explicacao": "Defina limites claros para o bot atender bem sem incomodar o cliente.",
                    "placeholder": "Ex: Responder apenas em conversas privadas e oferecer opção de falar com humano",
                    "sugestoes": [
                        "Oferecer sempre uma opção para falar com um humano",
                        "Não responder mensagens em grupos, apenas conversas privadas",
                        "Respeitar horário de atendimento configurado",
                        "Evitar enviar mensagens repetidas (controle de spam)",
                    ],
                },
                "tratamento_erros": {
                    "titulo": "6. E se o cliente enviar algo que o bot não entendeu?",
                    "explicacao": "Defina a resposta de segurança caso o cliente mande áudio, figurinha ou texto confuso.",
                    "placeholder": "Ex: Pedir desculpas educadamente e mostrar novamente o menu de opções",
                    "sugestoes": [
                        "Mostrar o menu novamente quando não entender a mensagem",
                        "Avisar que não lê áudios/figurinhas e pedir para digitar",
                        "Encaminhar para um atendente humano após 2 tentativas sem sucesso",
                    ],
                },
            },
        },
        "jogos": {
            "titulo": "Criação de Jogos (2D, 3D ou Tabuleiro)",
            "guia": (
                "Ferramentas mais usadas para criar jogos:\n"
                "• Godot (GDScript): Gratuito, leve e excelente para jogos 2D, 3D e tabuleiro com animações.\n"
                "• HTML5 + JavaScript (Navegador): O jogo roda direto no navegador (Chrome/Safari) sem precisar instalar nada.\n"
                "• Unity (C#): Muito popular para jogos no computador e celular, com muitos recursos prontos.\n"
                "• Não sei escolher: Pode deixar que a IA escolha a opção mais simples para o seu caso."
            ),
            "sugestoes_stack": [
                "Godot 4 (GDScript)",
                "HTML5 + JavaScript (roda no navegador)",
                "Unity (C#)",
                "Deixar a IA escolher a melhor ferramenta",
            ],
            "guia_campos": {
                "objetivo": {
                    "titulo": "1. Qual é a ideia do seu jogo?",
                    "explicacao": "Conte com suas palavras como o jogo funciona e o que torna ele divertido ou diferente.",
                    "placeholder": "Ex: Criar um jogo de Damas onde cada peça é um personagem animado que ganha vida ao se mover",
                    "sugestoes": [],
                },
                "stack": {
                    "titulo": "2. Onde o jogo vai rodar e qual ferramenta usar?",
                    "explicacao": "Se não souber o nome técnico, clique em uma opção abaixo ou diga onde quer jogar (PC, Mac, celular ou navegador).",
                    "placeholder": "Ex: Roda no navegador do computador, ou Godot 4",
                    "sugestoes": [
                        "Godot 4 (GDScript)",
                        "HTML5 + JavaScript (roda no navegador)",
                        "Unity (C#)",
                        "Deixar a IA escolher a melhor ferramenta",
                    ],
                },
                "entrada": {
                    "titulo": "3. Como o jogador controla o jogo? (Comandos)",
                    "explicacao": "Pense em como a pessoa interage com a tela: clicando com o mouse, tocando no celular ou usando o teclado.",
                    "placeholder": "Ex: O jogador clica na peça com o mouse e depois clica na casa para onde quer mover",
                    "sugestoes": [
                        "Clique do mouse (selecionar e mover peças)",
                        "Toque na tela do celular ou tablet",
                        "Teclado (setas ou teclas WASD)",
                        "Mouse + atalhos de teclado",
                    ],
                },
                "saida": {
                    "titulo": "4. O que o jogador vê e ouve na tela? (Resultado)",
                    "explicacao": "Descreva o que acontece na tela depois de cada jogada: animações, placar, sons ou tela de vitória.",
                    "placeholder": "Ex: Tabuleiro colorido com personagens animados andando, efeitos sonoros e placar",
                    "sugestoes": [
                        "Animações dos personagens a cada jogada",
                        "Placar em tempo real e tela de vitória/derrota",
                        "Efeitos sonoros e música de fundo",
                        "Destaque visual das casas válidas para jogar",
                    ],
                },
                "regras": {
                    "titulo": "5. Quais são as regras do jogo?",
                    "explicacao": "Clique nas sugestões abaixo ou escreva suas próprias regras (uma por vez).",
                    "placeholder": "Ex: Quando uma peça chega ao outro lado do tabuleiro, ela vira Dama",
                    "sugestoes": [
                        "Modo 1 jogador contra a máquina (IA) e 2 jogadores no mesmo aparelho",
                        "Validar jogadas para impedir movimentos proibidos",
                        "Permitir captura obrigatória e múltiplos saltos",
                        "Botão para reiniciar a partida a qualquer momento",
                    ],
                },
                "tratamento_erros": {
                    "titulo": "6. E se o jogador clicar no lugar errado? (Proteção contra erros)",
                    "explicacao": "Diga como o jogo deve reagir quando alguém tentar fazer uma jogada inválida, sem travar a partida.",
                    "placeholder": "Ex: Se clicar em uma casa proibida, mostrar um aviso leve e manter a peça parada",
                    "sugestoes": [
                        "Ignorar cliques fora das casas válidas e destacar onde pode jogar",
                        "Exibir mensagem amigável sem travar ou fechar o jogo",
                        "Pedir confirmação antes de reiniciar ou sair da partida",
                    ],
                },
            },
        },
        "mobile": {
            "titulo": "Aplicativo para Celular (iOS e Android)",
            "guia": (
                "Ferramentas para desenvolver apps para iOS e Android:\n"
                "• Flutter (Dart): Cria aplicativos nativos para iOS e Android com um único código e visual altamente personalizável.\n"
                "• React Native (JavaScript/TypeScript): Usa a base do React para construir aplicativos móveis com grande comunidade e bibliotecas prontas.\n"
                "• SwiftUI (Swift): Framework oficial da Apple para criar aplicativos nativos exclusivos para iPhone, iPad e Mac.\n"
                "• Jetpack Compose (Kotlin): Ferramenta oficial do Google para desenvolver aplicativos nativos modernos para Android."
            ),
            "sugestoes_stack": [
                "Flutter (Dart)",
                "React Native (TypeScript)",
                "SwiftUI (Swift)",
                "Jetpack Compose (Kotlin)",
            ],
            "guia_campos": {
                "objetivo": {
                    "titulo": "1. O que o aplicativo vai fazer?",
                    "explicacao": "Explique qual problema o app resolve para quem vai usar no celular.",
                    "placeholder": "Ex: Aplicativo para organizar minhas vendas diárias e controlar clientes",
                    "sugestoes": [],
                },
                "stack": {
                    "titulo": "2. Em qual celular vai rodar e qual tecnologia usar?",
                    "explicacao": "Escolha uma das opções sugeridas abaixo ou diga se é para iPhone, Android ou os dois.",
                    "placeholder": "Ex: Flutter para rodar no iPhone e no Android",
                    "sugestoes": [
                        "Flutter (Dart)",
                        "React Native (TypeScript)",
                        "SwiftUI (Swift)",
                        "Jetpack Compose (Kotlin)",
                    ],
                },
                "entrada": {
                    "titulo": "3. O que a pessoa digita ou envia no app?",
                    "explicacao": "Diga o que o usuário coloca na tela: preenche campos, tira foto, aperta botões ou faz login.",
                    "placeholder": "Ex: O usuário preenche nome, valor da venda e tira foto do comprovante",
                    "sugestoes": [
                        "Formulário simples digitado na tela",
                        "Login com e-mail e senha",
                        "Foto da câmera ou galeria do celular",
                        "Seleção em listas e botões grandes",
                    ],
                },
                "saida": {
                    "titulo": "4. O que o app mostra ou entrega de volta?",
                    "explicacao": "Descreva o que aparece na tela depois: lista organizada, gráfico, alerta ou resumo para compartilhar.",
                    "placeholder": "Ex: Lista organizada de vendas do mês e botão para compartilhar resumo",
                    "sugestoes": [
                        "Tela de resumo com lista organizada",
                        "Notificação ou lembrete no celular",
                        "Compartilhar resumo em PDF ou WhatsApp",
                        "Salvar os dados automaticamente no aparelho",
                    ],
                },
                "regras": {
                    "titulo": "5. Regras importantes do aplicativo",
                    "explicacao": "Clique nas sugestões abaixo ou adicione suas próprias regras (uma por vez).",
                    "placeholder": "Ex: Funcionar mesmo sem internet e sincronizar depois",
                    "sugestoes": [
                        "Funcionar offline salvando os dados no aparelho",
                        "Formatar valores em Reais (R$ 0.000,00)",
                        "Interface simples com botões grandes e fáceis de tocar",
                        "Pedir confirmação antes de apagar qualquer registro",
                    ],
                },
                "tratamento_erros": {
                    "titulo": "6. O que fazer se algo der errado? (Sem internet ou campo vazio)",
                    "explicacao": "Como o app deve avisar a pessoa se faltar internet ou se ela esquecer um campo.",
                    "placeholder": "Ex: Avisar qual campo faltou preencher sem apagar o que já foi digitado",
                    "sugestoes": [
                        "Mostrar aviso claro se ficar sem internet sem perder dados",
                        "Destacar campos obrigatórios não preenchidos sem limpar o formulário",
                        "Exibir mensagem amigável em português para qualquer falha",
                    ],
                },
            },
        },
        "web": {
            "titulo": "Site ou Sistema Online (Navegador)",
            "guia": (
                "Ferramentas principais para projetos Web:\n"
                "• React + TypeScript: Padrão de mercado para telas rápidas e modernas no navegador.\n"
                "• Next.js: Baseado em React, ótimo quando o site precisa aparecer bem no Google (SEO).\n"
                "• FastAPI (Python): Servidor moderno, muito rápido e excelente para integrar IAs.\n"
                "• Django (Python): Sistema completo com painel administrativo e login prontos."
            ),
            "sugestoes_stack": [
                "React + FastAPI (Python)",
                "Next.js + TypeScript",
                "Django (Python)",
                "Deixar a IA escolher a melhor stack web",
            ],
            "guia_campos": {
                "objetivo": {
                    "titulo": "1. O que esse site ou sistema vai fazer?",
                    "explicacao": "Descreva com suas palavras para que o site serve.",
                    "placeholder": "Ex: Criar um sistema online para clientes simularem parcelas e enviarem documentos",
                    "sugestoes": [],
                },
                "stack": {
                    "titulo": "2. Quais tecnologias usar no site?",
                    "explicacao": "Clique em uma opção recomendada abaixo ou deixe a IA escolher a melhor combinação.",
                    "placeholder": "Ex: React + FastAPI (Python)",
                    "sugestoes": [
                        "React + FastAPI (Python)",
                        "Next.js + TypeScript",
                        "Django (Python)",
                        "Deixar a IA escolher a melhor stack web",
                    ],
                },
                "entrada": {
                    "titulo": "3. Como o visitante interage ou envia dados?",
                    "explicacao": "Diga o que a pessoa faz no site: preenche um formulário, pesquisa algo, faz login ou envia um arquivo.",
                    "placeholder": "Ex: O usuário preenche um formulário simples na tela e clica em calcular",
                    "sugestoes": [
                        "Preenchimento de formulário na tela",
                        "Campo de busca e filtros por categoria",
                        "Login de usuário com senha",
                        "Envio de arquivo (PDF, imagem ou planilha)",
                    ],
                },
                "saida": {
                    "titulo": "4. O que o site mostra ou gera como resposta?",
                    "explicacao": "Explique o que aparece ao final: tabela, painel com gráficos, arquivo para baixar ou mensagem.",
                    "placeholder": "Ex: Mostra uma tabela clara na tela com botão para baixar em PDF",
                    "sugestoes": [
                        "Painel visual (dashboard) com cartões e tabelas",
                        "Botão para copiar ou baixar o resultado em PDF",
                        "Confirmação na tela e registro salvo no banco de dados",
                    ],
                },
                "regras": {
                    "titulo": "5. Regras de funcionamento do sistema",
                    "explicacao": "Clique nas sugestões abaixo ou informe restrições e cálculos obrigatórios.",
                    "placeholder": "Ex: Funcionar bem tanto no computador quanto no celular",
                    "sugestoes": [
                        "Layout responsivo (funcionar bem no computador e no celular)",
                        "Validar todos os campos antes de enviar",
                        "Salvar histórico das ações do usuário",
                    ],
                },
                "tratamento_erros": {
                    "titulo": "6. O que fazer quando acontecer um erro?",
                    "explicacao": "Diga como o site deve orientar o visitante se algo falhar ou um campo estiver incorreto.",
                    "placeholder": "Ex: Mostrar alerta claro explicando o erro e permitir tentar novamente",
                    "sugestoes": [
                        "Mostrar mensagem amigável em português sem códigos técnicos",
                        "Indicar exatamente qual campo precisa ser corrigido",
                        "Manter os dados preenchidos caso o servidor falhe",
                    ],
                },
            },
        },
        "automacao": {
            "titulo": "Automação, Scripts e Leitura de Arquivos",
            "guia": (
                "Ferramentas ideais para scripts e automação:\n"
                "• Python: Melhor opção para ler PDFs, planilhas Excel, organizar pastas e usar IA.\n"
                "• Go (Golang): Gera programas leves e muito rápidos em um único arquivo.\n"
                "• Node.js + Playwright: Excelente para automatizar cliques e tarefas em sites."
            ),
            "sugestoes_stack": [
                "Python 3 (Scripts / FastAPI)",
                "Go (Golang)",
                "Node.js + Playwright",
            ],
            "guia_campos": {
                "objetivo": {
                    "titulo": "1. Qual tarefa repetitiva você quer automatizar?",
                    "explicacao": "Conte o que hoje você faz manualmente e quer que o computador faça sozinho.",
                    "placeholder": "Ex: Ler uma pasta com 50 arquivos PDF e organizar os valores em uma planilha",
                    "sugestoes": [],
                },
                "stack": {
                    "titulo": "2. Qual linguagem ou ferramenta usar?",
                    "explicacao": "Para a maioria das automações com arquivos e planilhas, Python é a escolha mais simples e poderosa.",
                    "placeholder": "Ex: Python 3",
                    "sugestoes": [
                        "Python 3 (Scripts / FastAPI)",
                        "Go (Golang)",
                        "Node.js + Playwright",
                    ],
                },
                "entrada": {
                    "titulo": "3. De onde vêm os dados que o programa vai ler?",
                    "explicacao": "Informe o que você vai entregar para o programa processar: arquivos numa pasta, planilha, texto ou site.",
                    "placeholder": "Ex: Arquivos PDF salvos em uma pasta no meu computador",
                    "sugestoes": [
                        "Arquivos PDF em uma pasta local",
                        "Planilha Excel (.xlsx) ou CSV",
                        "Texto digitado no terminal",
                        "Dados coletados de uma página da internet",
                    ],
                },
                "saida": {
                    "titulo": "4. O que o programa deve entregar pronto no final?",
                    "explicacao": "Escolha o formato final que você quer receber depois que a automação terminar.",
                    "placeholder": "Ex: Uma planilha Excel organizada salva na mesma pasta",
                    "sugestoes": [
                        "Planilha Excel (.xlsx) ou CSV pronta",
                        "Arquivo PDF ou documento Word (.docx) preenchido",
                        "Relatório resumido salvo em texto ou JSON",
                        "Arquivos renomeados e organizados em pastas",
                    ],
                },
                "regras": {
                    "titulo": "5. Regras que a automação precisa respeitar",
                    "explicacao": "Detalhe formatos de moeda, filtros ou cuidados para não apagar arquivos originais.",
                    "placeholder": "Ex: Nunca apagar os arquivos originais, apenas criar cópias organizadas",
                    "sugestoes": [
                        "Nunca alterar ou apagar os arquivos originais",
                        "Formatar valores no padrão brasileiro (R$ 0.000,00)",
                        "Mostrar no final quantos itens foram processados com sucesso",
                    ],
                },
                "tratamento_erros": {
                    "titulo": "6. E se algum arquivo estiver com defeito ou fora do padrão?",
                    "explicacao": "Diga se o programa deve pular o arquivo problemático e continuar os outros, avisando no final.",
                    "placeholder": "Ex: Se um PDF estiver ilegível, pular esse arquivo, anotar o nome dele e continuar",
                    "sugestoes": [
                        "Pular arquivos com erro, registrar num log e continuar o lote",
                        "Avisar claramente se a pasta ou arquivo não for encontrado",
                        "Parar com segurança sem corromper o arquivo de saída",
                    ],
                },
            },
        },
        "geral": {
            "titulo": "Projeto de Software Geral",
            "guia": (
                "Guia simples para montar um ótimo pedido:\n"
                "• Não precisa falar difícil: descreva o que o usuário faz e o que espera ver acontecer.\n"
                "• Se não souber escolher a tecnologia, basta dizer onde quer usar o programa (computador, celular ou navegador)."
            ),
            "sugestoes_stack": [
                "Python",
                "TypeScript",
                "Go",
                "Deixar a IA escolher a melhor opção",
            ],
            "guia_campos": {
                "objetivo": {
                    "titulo": "1. O que você quer criar?",
                    "explicacao": "Explique com suas próprias palavras o que o programa deve fazer.",
                    "placeholder": "Ex: Criar uma ferramenta simples para organizar minhas tarefas e cálculos do dia",
                    "sugestoes": [],
                },
                "stack": {
                    "titulo": "2. Onde vai rodar ou qual linguagem prefere?",
                    "explicacao": "Se não tiver preferência técnica, clique em 'Deixar a IA escolher a melhor opção'.",
                    "placeholder": "Ex: Quero abrir no navegador do computador ou celular",
                    "sugestoes": [
                        "Python",
                        "TypeScript",
                        "Go",
                        "Deixar a IA escolher a melhor opção",
                    ],
                },
                "entrada": {
                    "titulo": "3. Como a pessoa vai usar ou enviar informações?",
                    "explicacao": "Pense no primeiro passo de quem abre o programa: vai clicar em botões, digitar textos ou escolher um arquivo?",
                    "placeholder": "Ex: A pessoa digita as informações na tela e clica em um botão",
                    "sugestoes": [
                        "Digitar informações em campos na tela",
                        "Cliques de mouse ou toque em botões",
                        "Escolher um arquivo do computador",
                        "Comandos simples no terminal",
                    ],
                },
                "saida": {
                    "titulo": "4. O que o programa deve mostrar ou gerar?",
                    "explicacao": "Qual é o resultado final esperado depois que o programa faz o trabalho dele?",
                    "placeholder": "Ex: Mostrar o resultado pronto na tela com botão para copiar ou salvar",
                    "sugestoes": [
                        "Mostrar o resultado organizado na tela",
                        "Gerar um arquivo pronto para salvar",
                        "Copiar o resultado pronto com um clique",
                    ],
                },
                "regras": {
                    "titulo": "5. Regras e detalhes importantes",
                    "explicacao": "Clique nas sugestões ou adicione detalhes que não podem faltar.",
                    "placeholder": "Ex: Tudo em português e com visual simples e fácil de entender",
                    "sugestoes": [
                        "Interface toda em português e fácil de usar",
                        "Validar dados antes de processar",
                        "Salvar automaticamente para não perder o progresso",
                    ],
                },
                "tratamento_erros": {
                    "titulo": "6. Como agir se o usuário errar ou algo falhar?",
                    "explicacao": "Explique como o programa deve se comportar diante de um erro, sem travar.",
                    "placeholder": "Ex: Exibir uma mensagem simples explicando o que corrigir, sem travar o programa",
                    "sugestoes": [
                        "Mostrar mensagem amigável explicando o que faltou preencher",
                        "Nunca travar ou fechar sozinho se receber um dado inválido",
                    ],
                },
            },
        },
    }

    @staticmethod
    def _contem_palavra(texto: str, padroes: list[str]) -> bool:
        """Verifica correspondência por palavra inteira para evitar falsos positivos (ex: 'app' em 'WhatsApp')."""
        return any(re.search(rf"\b{p}\b", texto, flags=re.IGNORECASE) for p in padroes)

    def _sanitizar_e_validar_seguranca(self, valor: str, campo: str) -> str:
        """Remove espaços excedentes e bloqueia tentativas de sabotagem ou injeção."""
        if not isinstance(valor, str):
            raise ValidationError(f"O campo '{campo}' deve ser um texto válido.")

        texto_limpo = re.sub(r"[ \t]+", " ", valor).strip()

        if len(texto_limpo) > self.MAX_FIELD_LENGTH:
            raise SecurityError(
                f"O campo '{campo}' excede o limite de segurança ({self.MAX_FIELD_LENGTH} caracteres)."
            )

        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, texto_limpo, flags=re.IGNORECASE):
                raise SecurityError(
                    f"Conteúdo suspeito ou tentativa de injeção detectada no campo '{campo}'."
                )

        return texto_limpo

    def analisar_intencao(self, intencao: str) -> dict[str, Any]:
        """Regra 1: Identifica o perfil do projeto e devolve o formulário guiado passo a passo."""
        texto = self._sanitizar_e_validar_seguranca(intencao, "intencao")
        if len(texto) < 5:
            raise ValidationError(
                "Descreva sua ideia com pelo menos 5 caracteres para montarmos o formulário."
            )

        lower = texto.lower()
        if self._contem_palavra(
            lower,
            ["bot", "chatbot", "whatsapp", "zap", "telegram", "discord", "atendente virtual"],
        ):
            categoria = "bots"
        elif self._contem_palavra(
            lower,
            ["jogo", "jogos", "game", "games", "damas", "xadrez", "tabuleiro", "rpg", "personagem", "personagens", "godot", "unity"],
        ):
            categoria = "jogos"
        elif self._contem_palavra(
            lower,
            ["script", "scripts", "pdf", "pdfs", "automação", "automacao", "planilha", "planilhas", "excel", "scraping", "scraper"],
        ):
            categoria = "automacao"
        elif self._contem_palavra(
            lower,
            ["app", "aplicativo", "celular", "mobile", "ios", "android", "iphone", "smartphone"],
        ):
            categoria = "mobile"
        elif self._contem_palavra(
            lower,
            ["site", "web", "sistema", "dashboard", "portal", "saas", "loja virtual", "e-commerce"],
        ):
            categoria = "web"
        else:
            categoria = "geral"

        perfil = self.BASE_EDUCACIONAL[categoria]
        return {
            "categoria": categoria,
            "titulo": perfil["titulo"],
            "guia_educacional": perfil["guia"],
            "sugestoes_stack": perfil["sugestoes_stack"],
            "guia_campos": perfil["guia_campos"],
            "ordem_campos": ["objetivo", "stack", "entrada", "saida", "regras", "tratamento_erros"],
        }

    def validar_sequencia(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Regra 2: Garante preenchimento sequencial estrito e higienização."""
        ordem_obrigatoria = ["objetivo", "stack", "entrada", "saida", "regras"]
        limpo: dict[str, Any] = {}

        for campo in ordem_obrigatoria:
            valor = payload.get(campo)
            if campo == "regras":
                if not isinstance(valor, list):
                    raise ValidationError("O campo 'regras' deve ser uma lista de regras.")
                regras_limpas = [
                    self._sanitizar_e_validar_seguranca(r, "regras")
                    for r in valor
                    if isinstance(r, str) and r.strip()
                ]
                if not regras_limpas:
                    raise ValidationError(
                        "O campo 'regras' deve ter pelo menos 1 regra preenchida antes de prosseguir."
                    )
                limpo["regras"] = regras_limpas
            else:
                if valor is None or not isinstance(valor, str) or not valor.strip():
                    raise ValidationError(
                        f"O campo '{campo}' deve ser preenchido antes de prosseguir."
                    )
                limpo[campo] = self._sanitizar_e_validar_seguranca(valor, campo)

        erros_opcional = payload.get("tratamento_erros", "")
        limpo["tratamento_erros"] = (
            self._sanitizar_e_validar_seguranca(erros_opcional, "tratamento_erros")
            if erros_opcional
            else ""
        )
        return limpo

    def revisar_pedido(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Regra 3: Revisa o pedido completo e sinaliza lacunas ou incoerências técnicas."""
        limpo = self.validar_sequencia(payload)
        pendencias: list[str] = []

        if len(limpo["objetivo"].split()) < 4:
            pendencias.append(
                "Objetivo muito curto: especifique qual problema real o código resolve."
            )

        if limpo["stack"].lower() in {"qualquer", "tanto faz", "nao sei", "não sei"}:
            pendencias.append(
                "Stack indefinida: escolha uma opção do guia ou informe onde o sistema vai rodar."
            )

        if len(limpo["regras"]) < 2:
            pendencias.append(
                "Adicione pelo menos 2 regras de negócio ou restrições (ex: formato, testes, segurança)."
            )

        if not limpo["tratamento_erros"]:
            pendencias.append(
                "Falta definir o tratamento de erros (o que fazer se um arquivo ou dado falhar)."
            )

        if self._contem_palavra(limpo["objetivo"], ["bot", "chatbot", "whatsapp", "telegram"]) and self._contem_palavra(
            limpo["stack"], ["flutter", "swiftui", "jetpack"]
        ):
            pendencias.append(
                "Incoerência detectada: bots de WhatsApp/Telegram rodam em servidor (ex: Python ou Node.js), não em Flutter/SwiftUI."
            )

        score = max(40, 100 - (len(pendencias) * 15))
        return {
            "aprovado": len(pendencias) == 0,
            "score_qualidade": score,
            "pendencias": pendencias,
        }

    def gerar_prompt_final(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Regra 4: Gera o prompt compactado, estruturado e pronto para copiar e colar."""
        limpo = self.validar_sequencia(payload)
        regras_md = "\n".join(f"- {r}" for r in limpo["regras"])
        erros_md = (
            limpo["tratamento_erros"]
            or "Validar entradas e retornar mensagens claras sem quebrar a execução."
        )

        prompt = (
            f"### Objetivo\n{limpo['objetivo']}\n\n"
            f"### Stack\n{limpo['stack']}\n\n"
            f"### Input\n{limpo['entrada']}\n\n"
            f"### Output\n{limpo['saida']}\n\n"
            f"### Regras\n{regras_md}\n\n"
            f"### Erros e Edge Cases\n{erros_md}\n\n"
            f"### Padrão\nCódigo limpo, tipado, documentado e acompanhado de testes automatizados."
        )

        tokens_estimados = max(1, int(len(prompt.split()) * 1.35))
        return {
            "prompt_final": prompt.strip(),
            "tokens_estimados": tokens_estimados,
        }
