// Testes do montarLinkIa. Rodar: npm test (dentro de frontend/).
import assert from 'node:assert/strict';
import test from 'node:test';
import { LIMITE_URL, montarLinkIa } from './abrirNaIa.ts';

const claude = { chatUrl: 'https://claude.ai/new', preenchimento: { param: 'q' } };
const semSuporte = { chatUrl: 'https://gemini.google.com/app' };

test('prompt curto vai dentro do link e volta igual ao ler o parâmetro', () => {
  const prompt = 'Crie um app & mostre o passo a passo.\nLinha 2: 100% ação? #sim';
  const r = montarLinkIa(claude, prompt);
  assert.equal(r.preenchido, true);
  const lido = new URL(r.url);
  assert.equal(lido.origin, 'https://claude.ai');
  assert.equal(lido.pathname, '/new');
  assert.equal(lido.searchParams.get('q'), prompt);
});

test('caracteres que quebrariam o endereço ficam codificados (sem & solto)', () => {
  const r = montarLinkIa(claude, 'a&b=c#d');
  assert.equal(new URL(r.url).searchParams.get('q'), 'a&b=c#d');
  assert.equal(new URL(r.url).hash, '');
});

test('prompt grande demais cai para copiar e colar', () => {
  const r = montarLinkIa(claude, 'x'.repeat(LIMITE_URL + 1));
  assert.equal(r.preenchido, false);
  assert.equal(r.url, 'https://claude.ai/new');
});

test('limite vale para o endereço já codificado (acentos aumentam o tamanho)', () => {
  const r = montarLinkIa(claude, 'ç'.repeat(2000));
  assert.equal(r.preenchido, false);
});

test('site sem preenchimento confirmado só abre a página', () => {
  const r = montarLinkIa(semSuporte, 'olá');
  assert.deepEqual(r, { url: 'https://gemini.google.com/app', preenchido: false });
});

test('prompt vazio não gera link com parâmetro', () => {
  const r = montarLinkIa(claude, '   ');
  assert.equal(r.preenchido, false);
});

test('recusa endereço que não seja https', () => {
  assert.throws(() => montarLinkIa({ chatUrl: 'http://claude.ai/new' }, 'oi'));
  assert.throws(() => montarLinkIa({ chatUrl: 'javascript:alert(1)' }, 'oi'));
});
