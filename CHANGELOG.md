# Changelog

Todas as mudanças significativas neste projeto são documentadas neste arquivo.

---

## [1.0.1] - 2026-03-31

### ✨ Novas Funcionalidades

- **Pré-visualização em Dividir/Juntar**: Painel de preview mostra thumbnail da primeira página do PDF selecionado
  - Split page: navegação entre páginas com botões ◀ ▶
  - Merge page: atualiza ao clicar em um arquivo na lista
- **Splash screen animado**: Janela de carregamento com animação enquanto as dependências pesadas carregam em background
  - App abre em ~100ms em vez de 2-5s

### 🚀 Melhorias de Performance

- **Lazy loading de dependências**: pytesseract, PIL, pdf2image, reportlab e PyPDF2 carregam em background thread
- **OCR página-a-página**: Processa uma página por vez em vez de carregar todas na memória
- **Compress página-a-página**: Processa imagens diretamente em memória (BytesIO) sem criar arquivos temporários
- **Memory cleanup**: Imagens preprocessadas são deletadas imediatamente após uso

### 🔧 Melhorias de Precisão

- **OCR mais preciso**: Pipeline de pré-processamento de imagem
  - Conversão para escala de cinza
  - Aumento de contraste (1.8x)
  - Filtro de nitidez para bordas de caracteres
  - Binarização Otsu (threshold adaptativo)
- **Tesseract otimizado**: OEM 3 (melhor engine disponível) + PSM 6 (block text detection)
- **Threshold de confiança**: Ajustado para >=20 para melhor captura de palavras
- **Imagem original preservada**: Output PDF mantém imagem visual original (pré-processamento usado apenas para OCR)

### 🎨 Correções de Layout

- **Página Sobre**: Adicionado container scrollável (Canvas + Scrollbar) para conteúdo que extrapolava
- **Split/Merge progress bars**: Corrigido range de 0-1 para 0-100

### 🐛 Correções de Bugs

- **File handle leak em Split**: Uso correto de `with open()` para evitar travamento de arquivo
- **Memory leak em Compress**: Eliminação de temp files desnecessários
- **Frozensets em detecção de nomes**: Lookup mais eficiente para constantes

---

## [1.0.0] - 2026-03-30

### ✨ Lançamento Inicial

- **OCR**: Conversão de PDFs escaneados em PDFs pesquisáveis
  - Suporte a Português, Inglês, Espanhol, Francês, Alemão
  - Destaque automático de nomes de pessoas
- **Comprimir**: Redução de tamanho com opções de qualidade (100-250 DPI)
  - Formatos: JPEG com perda / PNG sem perda
- **Dividir PDF**: Extração de intervalos de páginas
  - Modo único, múltiplos intervalos, ou todas as páginas individualmente
- **Juntar PDF**: União de múltiplos PDFs
  - Reordenação com mouse ou botões ↑↓
  - Suporte a drag & drop do Explorer
- **Atualização automática**: Verificação e instalação de novas versões
- **Interface dark mode**: VS Code Dark theme

---

## Versionamento

Este projeto segue [Semantic Versioning](https://semver.org/lang/pt-BR/).

- **MAJOR**: Mudanças incompatíveis na API ou interface
- **MINOR**: Novas funcionalidades, retrocompatível
- **PATCH**: Correções de bugs
