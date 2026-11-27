/** Regras da tela "Já tenho um prompt" (sem React, para poder testar). */

// Mesmo limite do backend (MAX_TEXTO_ORGANIZAR em backend/prompt_engine.py).
export const MAX_TEXTO_ORGANIZAR = 8000;
export const MIN_TEXTO_ORGANIZAR = 10;

export interface CamposOrganizados {
  objetivo: string;
  stack: string;
  entrada: string;
  saida: string;
  regras: string[];
  tratamento_erros: string;
}

export const NOMES_CAMPOS: [keyof CamposOrganizados, string][] = [
  ['objetivo', 'Objetivo'],
  ['stack', 'Tecnologia'],
  ['entrada', 'O que entra'],
  ['saida', 'O que sai'],
  ['regras', 'Regras'],
  ['tratamento_erros', 'Erros'],
];

export function podeOrganizar(texto: string): boolean {
  const tamanho = texto.trim().length;
  return tamanho >= MIN_TEXTO_ORGANIZAR && tamanho <= MAX_TEXTO_ORGANIZAR;
}

export function campoVazio(valor: string | string[]): boolean {
  return Array.isArray(valor) ? valor.length === 0 : !valor.trim();
}

/** Há algo na tela que "Usar estes campos" apagaria? */
export function haTrabalhoNaTela(atual: CamposOrganizados, temResultado: boolean): boolean {
  return temResultado || NOMES_CAMPOS.some(([campo]) => !campoVazio(atual[campo]));
}

/** Primeira etapa (1 a 6) que ficou vazia; se nenhuma, a 1. */
export function primeiraEtapaVazia(campos: CamposOrganizados): number {
  const indice = NOMES_CAMPOS.findIndex(([campo]) => campoVazio(campos[campo]));
  return indice < 0 ? 1 : indice + 1;
}

/** Pedaço do texto colado que não coube nos campos. */
export interface TrechoDeFora {
  campo: keyof CamposOrganizados;
  titulo: string;
  texto: string;
}

/** "Usar estes campos" pede confirmação se apagar trabalho ou se algo ficar de fora. */
export function precisaPerguntar(haTrabalho: boolean, ficouDeFora: TrechoDeFora[]): boolean {
  return haTrabalho || ficouDeFora.length > 0;
}

/** Mensagem mostrada depois de preencher o formulário. */
export function avisoDepoisDeUsar(ficouDeFora: TrechoDeFora[]): string {
  const base = 'Campos preenchidos. Confira cada etapa abaixo antes de gerar.';
  return ficouDeFora.length
    ? `${base} Atenção: parte do texto que você colou ficou de fora.`
    : base;
}
