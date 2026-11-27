// Testes das regras da tela "Já tenho um prompt". Rodar: npm test (dentro de frontend/).
import assert from 'node:assert/strict';
import test from 'node:test';
import {
  MAX_TEXTO_ORGANIZAR,
  avisoDepoisDeUsar,
  precisaPerguntar,
  haTrabalhoNaTela,
  podeOrganizar,
  primeiraEtapaVazia,
} from './organizar.ts';

const vazio = { objetivo: '', stack: '', entrada: '', saida: '', regras: [], tratamento_erros: '' };
const cheio = { objetivo: 'a', stack: 'b', entrada: 'c', saida: 'd', regras: ['e'], tratamento_erros: 'f' };

test('só libera o Organizar dentro dos limites', () => {
  assert.equal(podeOrganizar('curto'), false);
  assert.equal(podeOrganizar('x'.repeat(10)), true);
  assert.equal(podeOrganizar('x'.repeat(MAX_TEXTO_ORGANIZAR)), true);
  assert.equal(podeOrganizar('x'.repeat(MAX_TEXTO_ORGANIZAR + 1)), false);
});

test('pede confirmação quando há campo preenchido ou prompt gerado', () => {
  assert.equal(haTrabalhoNaTela(vazio, false), false);
  assert.equal(haTrabalhoNaTela(vazio, true), true);
  assert.equal(haTrabalhoNaTela({ ...vazio, regras: ['x'] }, false), true);
  assert.equal(haTrabalhoNaTela({ ...vazio, tratamento_erros: 'x' }, false), true);
});

test('leva à primeira etapa que ficou vazia', () => {
  assert.equal(primeiraEtapaVazia(cheio), 1);
  assert.equal(primeiraEtapaVazia({ ...cheio, saida: ' ' }), 4);
  assert.equal(primeiraEtapaVazia({ ...cheio, regras: [] }), 5);
});

const trecho = { campo: 'regras' as const, titulo: 'Regra que não coube (1)', texto: 'x' };

test('pergunta antes de usar quando algo ficaria de fora, mesmo com o formulário vazio', () => {
  assert.equal(precisaPerguntar(false, []), false);
  assert.equal(precisaPerguntar(true, []), true);
  assert.equal(precisaPerguntar(false, [trecho]), true);
});

test('o aviso depois de preencher lembra do que ficou de fora', () => {
  assert.doesNotMatch(avisoDepoisDeUsar([]), /ficou de fora/);
  assert.match(avisoDepoisDeUsar([trecho]), /ficou de fora/);
});
