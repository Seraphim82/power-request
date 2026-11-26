import assert from 'node:assert/strict';
import { test } from 'node:test';
import {
  MARCA_RESPOSTA_CORTADA,
  recortarRodadas,
  respostaFoiCortada,
  tamanhoDoPrompt,
} from './tamanhoEnvio.ts';

test('conta o prompt como o servidor', () => {
  assert.equal(tamanhoDoPrompt('  abc  \n'), 3);
  assert.equal(tamanhoDoPrompt('a🚀'), 2);
});

test('reconhece a marca de corte, inclusive depois de reabrir o histórico', () => {
  assert.equal(respostaFoiCortada('código' + MARCA_RESPOSTA_CORTADA), true);
  assert.equal(respostaFoiCortada('resposta completa'), false);
});

test('reenvia só as 3 últimas rodadas e informa quantas ficaram para trás', () => {
  const muitas = Array.from({ length: 45 }, (_, i) => i + 1);
  assert.deepEqual(recortarRodadas(muitas), { enviadas: [43, 44, 45], anteriores: 42 });
  assert.deepEqual(recortarRodadas([1]), { enviadas: [1], anteriores: 0 });
});
