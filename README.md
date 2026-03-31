# PDF Tools

Conjunto de ferramentas para PDF com interface gráfica: OCR, compressão, divisão e junção de arquivos.

![Windows](https://img.shields.io/badge/Windows-10%2F11-blue?logo=windows)
![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![License](https://img.shields.io/badge/license-MIT-green)
![Release](https://img.shields.io/github/v/release/nicolastd5/pdf-ocr)

---

## Funcionalidades

### OCR
- Converte PDFs escaneados (imagens) em PDFs com texto pesquisável
- OCR em **Português** e **Inglês** (Tesseract)
- Destaque automático de nomes de pessoas

### Comprimir
- Reduz o tamanho de PDFs com opções de qualidade (100–250 DPI)
- Formatos de compressão: JPEG ou PNG

### Dividir PDF
- Intervalo único: extraia um trecho específico (De / Até)
- Múltiplos intervalos: campo de texto livre (`1-3, 5-8`) ou linhas visuais De/Até
- Todas as páginas individualmente em um clique

### Juntar PDF
- Une múltiplos PDFs em um único arquivo
- Reordene arrastando com o mouse ou usando os botões ↑↓
- Suporte a drag & drop de arquivos do Explorer

---

## Download

Baixe o executável mais recente na página de [Releases](https://github.com/nicolastd5/pdf-ocr/releases/latest).

Nenhuma instalação necessária. Basta executar `PDF_Tools.exe`.

---

## Como usar

### OCR
1. Execute `PDF_Tools.exe`
2. Clique em **Adicionar PDFs** e selecione os arquivos desejados
3. Escolha a pasta de saída (padrão: mesma pasta dos originais)
4. Selecione o idioma (Português / Inglês)
5. Clique em **Aplicar OCR**
6. Os arquivos processados serão salvos com o sufixo `_ocr.pdf`

### Dividir PDF
1. Selecione o PDF que deseja dividir
2. Escolha o modo: intervalo único, múltiplos intervalos ou todas as páginas
3. Marque "Salvar na mesma pasta do arquivo original" ou escolha o destino
4. Clique em **Dividir**

### Juntar PDF
1. Adicione os PDFs via botão ou arrastando do Explorer
2. Reordene a lista conforme necessário
3. Marque "Salvar na mesma pasta do primeiro PDF" ou escolha o destino
4. Clique em **Juntar**

---

## Atualização automática

O aplicativo verifica automaticamente se há uma nova versão disponível ao iniciar. Se houver, uma janela de notificação será exibida com a opção de baixar e instalar a atualização sem precisar acessar o GitHub manualmente.

Você também pode verificar manualmente clicando em **Verificar atualização** na aba **Sobre**.

---

## Histórico de versões

Veja [CHANGELOG.md](CHANGELOG.md) para detalhes das mudanças em cada versão.

---

## Compilando do código-fonte

Para compilar o código-fonte, use `PyInstaller` com a configuração fornecida:

```bash
pyinstaller pdf_ocr.spec
```

O executável será gerado em `dist/PDF_Tools.exe`.

> **Nota:** Para gerar o EXE com Tesseract e Poppler embutidos, copie os binários para `deps/tesseract/` e `deps/poppler/bin/` antes de rodar o PyInstaller. O workflow do GitHub Actions faz isso automaticamente.

---

## Licença

MIT License — veja [LICENSE](LICENSE) para detalhes.

---

## Autor

**Nicolas Almeida Hader Dias**
