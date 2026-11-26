// Testes da regra do aviso do link com o prompt. Rodar: npm test (dentro de frontend/).
import assert from 'node:assert/strict';
import test from 'node:test';
import { montarLinkIa } from './abrirNaIa.ts';
import { enderecoDaEscolha, precisaDeAviso } from './avisoLink.ts';

const claude = { chatUrl: 'https://claude.ai/new', preenchimento: { param: 'q' } };
const link = montarLinkIa(claude, 'SEGREDO123');

test('avisa só quando o prompt iria no endereço', () => {
  assert.equal(precisaDeAviso(link), true);
  assert.equal(precisaDeAviso(montarLinkIa({ chatUrl: 'https://grok.com/' }, 'oi')), false);
  assert.equal(precisaDeAviso(montarLinkIa(claude, 'x'.repeat(9000))), false);
});

test('abrir preenchido sem marcar a ciência não abre nada', () => {
  assert.equal(enderecoDaEscolha('preenchido', false, claude.chatUrl, link.url), null);
  assert.equal(enderecoDaEscolha('preenchido', true, claude.chatUrl, link.url), link.url);
});

test('só copiar nunca leva o prompt no endereço, marcado ou não', () => {
  for (const ciente of [false, true]) {
    const url = enderecoDaEscolha('so-copiar', ciente, claude.chatUrl, link.url);
    assert.equal(url, claude.chatUrl);
    assert.ok(!url.includes('SEGREDO123'));
  }
});
