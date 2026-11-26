import { test } from 'node:test';
import assert from 'node:assert/strict';
import { iaOfflineBloqueiaEnvio } from './bloqueioEnvio.ts';

test('IA offline bloqueia o envio', () => {
  assert.equal(iaOfflineBloqueiaEnvio('offline'), true);
});

test('online, desconhecido e verificando não bloqueiam o envio', () => {
  for (const estado of ['online', 'desconhecido', 'verificando']) {
    assert.equal(iaOfflineBloqueiaEnvio(estado), false, estado);
  }
});
