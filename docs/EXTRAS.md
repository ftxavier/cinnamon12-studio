# Extras opcionais

Estes componentes **não são ativados** pelo instalador do Cinnamon.

## Terminal

- Kitty: em seu `kitty.conf`, use `include /CAMINHO/Cinnamon12-Studio/extras/terminal/cinnamon12-dark/kitty.conf` ou a variante light.
- Alacritty: copie as seções do `extras/terminal/cinnamon12-dark/alacritty.toml` para seu arquivo de configuração, ou importe o arquivo conforme sua versão do Alacritty.
- Xresources: revise e carregue `extras/terminal/cinnamon12-dark/Xresources` manualmente com `xrdb -merge` se você usa um aplicativo que o respeite.
- GNOME Terminal e Nemo Terminal (quando instalado) podem exigir perfis específicos; o projeto **não** altera os seus perfis automaticamente.

## VS Code

`extras/vscode-theme` contém o manifesto e dois temas JSON. Para desenvolver/instalar como extensão, use o VS Code e suas ferramentas de extensões; **não** é um pacote VSIX pronto. Os temas podem ser importados pelo agente executor em uma extensão local.

## UI assets

SVGs/PNGs em `assets/ui/` são modelos de marca, widget, painel, tile, busca e menu. São **imagens**; não representam botões clicáveis nem estados reais do sistema. Para controles funcionais, desenvolva applets GJS sobre as APIs do Cinnamon e serviços do Ubuntu.
