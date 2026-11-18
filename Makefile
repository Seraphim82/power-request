# Atalhos do Power Request (rode a partir da raiz do projeto)
.PHONY: setup test typecheck build check run dev app icon node-check

node-check:  ## Confere a versão do Node exigida pelo frontend
	@node -e "const [a,b]=process.versions.node.split('.').map(Number); if(!(a>22||(a===22&&b>=12)||(a===20&&b>=19))){console.error('Precisa de Node 20.19+ ou 22.12+ (voce tem '+process.versions.node+'). Instale em https://nodejs.org');process.exit(1)}"

setup: node-check  ## Instala backend (venv) e frontend
	cd backend && python3 -m venv venv && ./venv/bin/pip install -r requirements-dev.txt
	cd frontend && npm install

test:  ## Testes do backend
	cd backend && ./venv/bin/python -m pytest

typecheck: node-check  ## Checagem de tipos do frontend
	cd frontend && npm run typecheck

build: node-check  ## Compila o frontend (frontend/dist)
	cd frontend && npm run build

check: test typecheck build  ## Tudo que precisa passar antes de um commit

run: build  ## Servidor unificado em http://127.0.0.1:8765
	cd backend && ./venv/bin/python desktop_app.py

dev:  ## Desenvolvimento: API em :8000 e Vite em :5173 (rode em dois terminais)
	@echo "Terminal 1: cd backend && ./venv/bin/uvicorn main:app --reload --port 8000"
	@echo "Terminal 2: cd frontend && npm run dev"

app:  ## Gera o Power Request.app (macOS)
	./build_mac_app.sh

icon:  ## Regenera o AppIcon.icns e a cópia do logo do frontend a partir de assets/logo-power-request.svg (macOS)
	./assets/build_icon.sh
	cp assets/logo-power-request.svg frontend/public/logo.svg
