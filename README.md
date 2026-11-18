# Power Request

Formalizador de pedidos para IA focado em compactação estruturada, economia de tokens e alta assertividade.

## Estrutura
- `backend/`: API FastAPI, motor de regras (`prompt_engine.py`) e suíte de testes severos (`test_power_request.py`).
- `frontend/`: Interface React + TypeScript (Vite) com liberação sequencial de campos e etapa de revisão.

## Execução Rápida
1. **Backend:** `cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && pytest -v && uvicorn main:app --reload`
2. **Frontend:** `cd frontend && npm install && npm run dev`
