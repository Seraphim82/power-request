/** Tempo decorrido no formato m:ss (ex.: 83 vira "1:23"). */
export function formatarTempo(segundos: number): string {
  const total = Math.max(0, Math.floor(segundos));
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, '0')}`;
}
