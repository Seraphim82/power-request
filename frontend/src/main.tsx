import { Component, StrictMode, type ErrorInfo, type ReactNode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.tsx'

class ErrorBoundary extends Component<{ children: ReactNode }, { falhou: boolean }> {
  state = { falhou: false }

  static getDerivedStateFromError() {
    return { falhou: true }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Power Request: erro inesperado na interface', error, info)
  }

  render() {
    if (this.state.falhou) {
      return (
        <div style={{ padding: 32, fontFamily: 'system-ui', color: '#e2e8f0', background: '#080e1c', minHeight: '100vh' }}>
          <h1>Algo deu errado na interface</h1>
          <p>Seus dados salvos no histórico continuam seguros. Recarregue a página para tentar de novo.</p>
          <button type="button" onClick={() => window.location.reload()}>Recarregar</button>
        </div>
      )
    }
    return this.props.children
  }
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </StrictMode>,
)
