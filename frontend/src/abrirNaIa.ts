/**
 * Monta o link para abrir o site de uma IA com o prompt já na caixa de texto.
 *
 * Ideia: a "caixa de correio" (campo de texto do site) aceita o texto sem problema.
 * Quem fecha a tampa (Enter) é a pessoa. Assim não precisa de script de teclado,
 * não pede permissão especial ao sistema e funciona igual em Mac, Windows e Linux.
 *
 * Sem efeitos colaterais de propósito: só devolve o link, para poder ser testado.
 */

export interface PreenchimentoPorLink {
  /** Nome do parâmetro de endereço que o site lê (ex.: "q" em claude.ai/new?q=). */
  param: string;
}

export interface MarcaSite {
  chatUrl: string;
  /** Presente só nos sites em que o preenchimento por endereço está confirmado. */
  preenchimento?: PreenchimentoPorLink;
}

export interface LinkIa {
  url: string;
  /** true = o prompt vai dentro do link; false = só abre o site (usar colar). */
  preenchido: boolean;
}

/**
 * Tamanho máximo do endereço final. Servidores e proxies costumam recusar endereços
 * muito longos, e o Claude corta o texto perto de 14.000 caracteres. Acima disso,
 * o caminho seguro é copiar e colar.
 */
export const LIMITE_URL = 8000;

export function montarLinkIa(marca: MarcaSite, prompt: string): LinkIa {
  const base = new URL(marca.chatUrl);
  if (base.protocol !== 'https:') {
    throw new Error('Endereço da IA precisa ser https.');
  }
  const semPreencher: LinkIa = { url: base.toString(), preenchido: false };
  if (!marca.preenchimento || !prompt.trim()) return semPreencher;

  base.searchParams.set(marca.preenchimento.param, prompt);
  const url = base.toString();
  return url.length <= LIMITE_URL ? { url, preenchido: true } : semPreencher;
}
