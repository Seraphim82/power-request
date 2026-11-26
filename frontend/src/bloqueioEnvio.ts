/**
 * Enviar e Sequenciar só são bloqueados quando o último teste disse que a IA está offline.
 * "desconhecido" fica liberado (chave de API não é testada sozinha, para não gastar cota) e
 * "verificando" também. É ajuda de tela: quem valida o envio continua sendo o servidor.
 */
export function iaOfflineBloqueiaEnvio(estado: string): boolean {
  return estado === 'offline';
}
