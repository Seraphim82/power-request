import assert from 'node:assert/strict';
import { test } from 'node:test';
import { formatarTempo } from './tempoEspera.ts';

test('mostra minutos e segundos com dois dígitos', () => {
  assert.equal(formatarTempo(0), '0:00');
  assert.equal(formatarTempo(9), '0:09');
  assert.equal(formatarTempo(83), '1:23');
  assert.equal(formatarTempo(600), '10:00');
});

test('não mostra tempo negativo nem quebrado', () => {
  assert.equal(formatarTempo(-5), '0:00');
  assert.equal(formatarTempo(61.9), '1:01');
});
