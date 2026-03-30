# PDF OCR

Converte PDFs escaneados em PDFs pesquisáveis aplicando OCR com Tesseract, sem necessidade de instalação de dependências externas.

![Windows](https://img.shields.io/badge/Windows-10%2F11-blue?logo=windows)
![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![License](https://img.shields.io/badge/license-MIT-green)
![Release](https://img.shields.io/github/v/release/nicolastd5/pdf-ocr)

---

## Funcionalidades

- Converte PDFs escaneados (imagens) em PDFs com texto pesquisável
- OCR em **Português** e **Inglês** (Tesseract)
- Interface gráfica simples e intuitiva
- Barra de progresso por página
- Seleção de pasta de saída personalizada
- Atualização automática via GitHub Releases
- Executável único — Tesseract e Poppler já embutidos

---

## Download

Baixe o executável mais recente na página de [Releases](https://github.com/nicolastd5/pdf-ocr/releases/latest).

Nenhuma instalação necessária. Basta executar `PDF_OCR.exe`.

---

## Como usar

1. Execute `PDF_OCR.exe`
2. Clique em **Adicionar PDFs** e selecione os arquivos desejados
3. Escolha a pasta de saída (padrão: mesma pasta dos originais)
4. Selecione o idioma (Português / Inglês)
5. Clique em **Aplicar OCR**
6. Os arquivos processados serão salvos com o sufixo `_ocr.pdf`

---

## Atualização automática

O aplicativo verifica automaticamente se há uma nova versão disponível ao iniciar. Se houver, uma janela de notificação será exibida com a opção de baixar e instalar a atualização sem precisar acessar o GitHub manualmente.

Você também pode verificar manualmente clicando em **Verificar atualização** na aba **Sobre**.

---

## Compilando do código-fonte

### Pré-requisitos

- Python 3.11
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) instalado
- [Poppler para Windows](https://github.com/oschwartz10612/poppler-windows/releases)

### Instalação das dependências

```bash
pip install -r requirements.txt
```

### Executando sem compilar

```bash
python pdf_ocr.py
```

### Gerando o executável

```bash
pyinstaller pdf_ocr.spec
```

O executável será gerado em `dist/PDF_OCR.exe`.

> **Nota:** Para gerar o EXE com Tesseract e Poppler embutidos, copie os binários para `deps/tesseract/` e `deps/poppler/bin/` antes de rodar o PyInstaller. O workflow do GitHub Actions faz isso automaticamente.

---

## Estrutura do projeto

```
pdf_ocr/
├── pdf_ocr.py          # Código principal
├── pdf_ocr.spec        # Configuração do PyInstaller
├── requirements.txt    # Dependências Python
├── deps/               # Binários bundled (Tesseract + Poppler) — não versionado
└── .github/
    └── workflows/
        └── build.yml   # CI/CD: build e release automático
```

---

## Tecnologias utilizadas

| Biblioteca | Finalidade |
|---|---|
| [pytesseract](https://github.com/madmaze/pytesseract) | Wrapper Python para o Tesseract OCR |
| [pdf2image](https://github.com/Belval/pdf2image) | Conversão de páginas PDF em imagens |
| [Pillow](https://python-pillow.org/) | Processamento de imagens |
| [reportlab](https://www.reportlab.com/) | Geração de overlay de texto invisível |
| [PyPDF2](https://github.com/py-pdf/pypdf) | Mesclagem de camadas PDF |
| [PyInstaller](https://pyinstaller.org/) | Empacotamento do executável |

---

## Licença

MIT License — veja [LICENSE](LICENSE) para detalhes.

---

## Autor

**Nicolas Almeida Hader Dias**
