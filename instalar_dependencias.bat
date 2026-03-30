@echo off
echo ============================================
echo  Instalando dependencias do PDF OCR
echo ============================================
echo.

pip install pytesseract pillow pdf2image reportlab PyPDF2

echo.
echo ============================================
echo  Dependencias instaladas!
echo.
echo  ATENCAO: Voce ainda precisa instalar:
echo.
echo  1. Tesseract OCR (motor de reconhecimento):
echo     https://github.com/UB-Mannheim/tesseract/wiki
echo     (marque "Portuguese" durante a instalacao)
echo.
echo  2. Poppler (converte PDF para imagem):
echo     https://github.com/oschwartz10612/poppler-windows/releases
echo     Extraia e adicione a pasta "bin" ao PATH do Windows
echo     OU coloque em: C:\Program Files\poppler\Library\bin
echo ============================================
echo.
pause
