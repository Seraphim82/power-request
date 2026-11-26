/** Limites e avisos de tamanho do Enviar e do Sequenciar. */

/** Valor usado até o servidor informar o limite (campo `limite_envio` de /api/health). */
export const LIMITE_ENVIO_PADRAO = 11000;

/** Quantas rodadas recentes a tela reenvia ao Sequenciar. */
export const RODADAS_REENVIADAS = 3;

/** Mesmo texto de MARCA_RESPOSTA_CORTADA (backend/main.py). */
export const MARCA_RESPOSTA_CORTADA = '\n\n[... resposta cortada pelo limite de tamanho ...]';

/** Conta como o servidor: sem espaços nas pontas, e um emoji vale um caractere. */
export function tamanhoDoPrompt(texto: string): number {
  return Array.from(texto.trim()).length;
}

export function respostaFoiCortada(texto: string): boolean {
  return texto.endsWith(MARCA_RESPOSTA_CORTADA.trim());
}

export function recortarRodadas<T>(rodadas: T[]): { enviadas: T[]; anteriores: number } {
  const enviadas = rodadas.slice(-RODADAS_REENVIADAS);
  return { enviadas, anteriores: rodadas.length - enviadas.length };
}
