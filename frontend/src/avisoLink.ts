/**
 * Regra do aviso antes de abrir uma IA com o prompt dentro do endereço.
 * Sem efeitos colaterais, para poder ser testada.
 */
export type EscolhaAviso = 'preenchido' | 'so-copiar';

/** Só há o que avisar quando o texto iria no link. */
export function precisaDeAviso(link: { preenchido: boolean }): boolean {
  return link.preenchido;
}

/**
 * Endereço a abrir conforme a escolha. "Abrir preenchido" exige a ciência marcada;
 * sem ela devolve null (não abre). "Só copiar" usa o endereço do site, sem o texto.
 */
export function enderecoDaEscolha(
  escolha: EscolhaAviso,
  ciente: boolean,
  chatUrl: string,
  urlPreenchida: string
): string | null {
  if (escolha === 'so-copiar') return chatUrl;
  return ciente ? urlPreenchida : null;
}
