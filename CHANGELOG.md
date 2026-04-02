# Changelog

Todas as mudanças significativas neste projeto são documentadas neste arquivo.

---

## [1.0.7] - 2026-04-02

### 🚀 Migração para PyQt6

- **Nova UI em PyQt6**: Interface completamente reescrita — visual moderno Ocean/Teal, sidebar fixa, `QStackedWidget` para navegação entre abas
- **Drag & drop nativo**: Sem dependência de `tkinterdnd2`; funciona via eventos padrão do Qt
- **Workers assíncronos**: Todas as operações (OCR, Comprimir, Dividir, Juntar, PDF→Word) rodam em `QThread` com signals `progress` / `finished` / `error`
- **SpinnerDialog animado**: Modal com dois círculos orbitais em todas as operações longas
- **GradientProgressBar**: Barra de progresso gradiente teal→sky em cada aba
- **Estrutura multi-arquivo**: `pdf_ocr_qt/` com `main.py`, `workers.py`, `styles.py`, `pages/`, `widgets/`

---

## [1.0.4] - 2026-03-31

### ✨ Novas Funcionalidades

- **Spinner em todas as operações**: Animação orbital dual agora aparece em Comprimir, Dividir e Juntar — igual ao OCR
- **Página Sobre atualizada**: Versão e changelog exibidos dinamicamente via `APP_VERSION`
- **Release notes do Actions atualizadas**: Body das releases no GitHub agora reflete as funcionalidades atuais

---

## [1.0.3] - 2026-03-31

### 🐛 Correções de Bugs

- **Drag & drop externo corrigido**: Arrastar PDFs do Explorer para a janela de Juntar agora funciona corretamente (integração com `tkinterdnd2`)
- **Pré-visualização maior**: Thumbnails de Dividir e Juntar aumentados de 180px para 300px de altura

---

## [1.0.2] - 2026-03-31

### 🎨 Redesign Visual Completo

- **Paleta Ocean/Teal**: Cores modernizadas (#2dd4bf primária, #38bdf8 secundária)
- **Sidebar expandível**: Animação suave (56px → 180px ao passar o mouse)
- **Spinner dual orbital**: Dois arcos animados em velocidades diferentes
- **Progress bar gradiente**: Animação de shimmer com transição de cores
- **Glassmorphism**: Cards e botões com efeitos de vidro e hover melhorados
- **Listbox estilizada**: Cards por item para melhor hierarquia visual
- **Tipografia e espaçamento**: Aprimoramentos gerais em todas as páginas

### 🔧 Melhorias

- **Auto-update simplificado**: Botão de atualização agora abre a página de releases no browser em vez de baixar e instalar automaticamente

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
