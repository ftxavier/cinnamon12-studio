# Histórico

## 0.1.0 (2026-11-19)

Primeira release pública. Conceito de como seria um Windows 12, funcionando de verdade sobre o Cinnamon. Testado no Ubuntu 24.04 LTS com Cinnamon 6.0.4 (X11).

- **Temas Cinnamon12 Light e Dark** para o shell do Cinnamon, GTK 3 e GTK 4: azul-marinho, cantos discretos, barras de título, Nemo, janelas sem foco e seletores do cinnamon-settings nas cores do tema; contraste de texto WCAG AA.
- **Barra de tarefas de borda a borda** (48 px), apps no centro e faixa de "mostrar área de trabalho" no canto.
- **Cinnamon12 Search**: digite direto no campo da barra; melhor correspondência, aplicativos, configurações, arquivos e pastas da home, com painel de ações (abrir com, abrir local, fixar na barra e no Iniciar, copiar caminho, terminal). Também como ícone ou só atalho (Super+F). Índice local, sem rede.
- **Cinnamon12 Start**: menu com busca, categorias, fixados, recentes e botões de sessão.
- **Cinnamon12 Quick Settings**: Wi-Fi, Bluetooth, modo escuro, não perturbe, volume, brilho e modo avião com estados reais.
- **Widgets**: calendário, monitor do sistema e clima (desligado por padrão, com opt-in de rede).
- **Ícones e 3 wallpapers originais** (até 4K); ícones de status simbólicos vêm do Yaru.
- **CLI `cinnamon12`** reversível: `apply`/`restore`, `panel apply|restore`, `widgets apply|restore`, `doctor`, `uninstall`, sempre com backup.
- **Extras opcionais**: cores para terminal (Kitty, Alacritty, Xresources) e tema de cores para VS Code.
- **Pacote `.deb` passivo**: só instala arquivos; nada muda até cada usuário rodar `cinnamon12 apply`.
