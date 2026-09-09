# Photo Compare - Comparador de Imagens

Aplicação desktop desenvolvida em **Python** e **Tkinter** para comparação visual lado a lado de imagens de alta resolução, com suporte a **2 ou 3 colunas**, **pan** (arrastar) e **zoom** sincronizados ou independentes.

---

## 🚀 Funcionalidades

- **2 ou 3 Colunas Dinâmicas**: Inicia com 2 colunas para comparação direta. É possível adicionar ou ocultar uma 3ª coluna a qualquer momento através da barra superior.
- **Navegação com Pan & Zoom**:
  - **Pan**: Clique e arraste com o botão esquerdo do mouse para navegar pela imagem.
  - **Zoom**: Roda do mouse (*mouse scroll wheel*) com ampliação ou redução centrada exatamente onde o cursor do mouse está apontando.
- **Controles Travados / Sincronizados**:
  - **🔒 Sincronização Travada**: Mover ou aplicar zoom em uma das imagens reflete instantaneamente em todas as outras colunas.
  - **🔓 Sincronização Destravada**: Permite alinhar ou reposicionar uma imagem individualmente antes de travar novamente.
- **Ajustes Rápidos**:
  - Botão **⤢ Ajustar Todas** (ajusta as imagens para caberem 100% na janela).
  - Botão **1:1 (Tamanho Real)** (define a escala em 100% no centro da imagem).
  - Botão **🎯 Alinhar ao Painel 1** (alinha o enquadramento e escala das outras colunas com base no primeiro painel).
  - Duplo clique no canvas para ajustar a imagem à tela.
- **Alta Performance (Viewport Crop)**:
  - Utiliza recorte da região visível (*viewport cropping*) com a biblioteca Pillow, garantindo navegação a 60 FPS mesmo para fotos pesadas de 24MP, 50MP ou superiores.
- **Formatos Suportados**: JPG, JPEG, PNG, WEBP, BMP, TIFF, GIF, etc.

---

## 📦 Executável Portátil (.EXE)

Você pode executar o aplicativo diretamente sem precisar ter o Python instalado! O executável já contém todas as bibliotecas e o ícone personalizado embutidos:

- O arquivo gerado está em: **[`dist/PhotoCompare.exe`](file:///c:/Dev/photo-compare/dist/PhotoCompare.exe)**
- Basta dar um duplo clique em `PhotoCompare.exe` para usar!

---

## 🛠️ Como Executar a Partir do Código-Fonte

### 1. Pré-requisitos
Certifique-se de ter o Python 3.9+ instalado.

### 2. Instalação das Dependências
Instale os pacotes necessários listados no `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 3. Execução
Execute o arquivo principal:
```bash
python main.py
```

### 4. Gerar Novo Executável
Caso faça alterações no código e deseje recompilar o `.exe`:
```bash
pyinstaller --noconsole --onefile --icon="assets\icon.ico" --add-data="assets;assets" --name="PhotoCompare" main.py
```

---

## ⌨️ Atalhos de Teclado

| Tecla | Ação |
| :--- | :--- |
| `Espaço` | Alternar trava de sincronização (Travada / Destravada) |
| `F` | Ajustar todas as imagens abertas à tela |
| `Ctrl + O` | Abrir imagem na primeira coluna vazia |
| `Duplo Clique` | Ajustar a imagem da coluna clicada à tela |
| `Scroll do Mouse` | Zoom In / Zoom Out centrado no cursor |
| `Arrastar (Botão Esquerdo)` | Pan (mover imagem) |

