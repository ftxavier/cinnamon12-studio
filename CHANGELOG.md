# Histórico

## 0.4.0 (em desenvolvimento)

- **Cinnamon12 Start** (`c12-start@cinnamon12.local`) reescrito: busca (nome, descrição, palavras-chave, executável, sem acento), categorias do menu do sistema, grade de fixados (favoritos do Cinnamon; clique direito fixa/desafixa), arquivos recentes (histórico local do GTK, desligável), Locais, usuário (AccountsService) e botões bloquear/sair/reiniciar/desligar com as confirmações do próprio Cinnamon.
- Atalho Super configurável, navegação por setas/Tab/Enter, `settings-schema.json` (largura, altura, colunas, recentes, atalho), tradução pt-BR (gettext).
- `cinnamon12 panel apply --launcher cinnamon12` troca o menu nativo pelo Cinnamon12 Start (o `panel restore` devolve o menu original).
- Estilo do launcher nos temas Light/Dark.

## 0.3.0 (validado em Ubuntu 24.04.5 + Cinnamon 6.0.4, X11)

- Tema do shell passa a importar o `cinnamon.css` instalado no sistema e sobrepor só as cores/geometria Cinnamon12: cobertura completa de Alt-Tab, Expo, OSD, calendário, notificações, som, teclado virtual e desklets. Toggle, checkbox, radio e setas do calendário redesenhados em `cinnamon/assets/`.
- GTK3 baseado no Adwaita embutido no GTK + overrides; estiliza também as barras de título que o Muffin desenha (não é preciso `metacity-1` no Cinnamon 6).
- GTK4 com CSS próprio (base Default do GTK4), não mais cópia do GTK3.
- Perfil de painel `balanced` (48 px, menu e janelas no centro) com backup/restore próprio: `cinnamon12 panel apply|restore`.
- Wallpaper aplicado na resolução do maior monitor.
- `.deb` 0.3.0-1: CLI em `/usr/bin/cinnamon12`, lista de wallpapers no Cinnamon Settings, `copyright`, `changelog.Debian.gz`, `md5sums`; sem PNG masters; sem scripts de mantenedor; lintian sem erros.
- Gerador `scripts/generate-themes.py` reescrito (versão anterior em `scripts/legacy/`).

## 0.2.0 beta

- Três wallpapers originais, com resoluções de desktop e masters.
- 202 nomes de ícones vetoriais e 1.126 PNG rasterizados aproximadamente (quantidade exata no inventário de arquivos).
- Temas Cinnamon e GTK claros/escuros com raios discretos e paleta azul.
- Applets opcionais de menu e atalhos de configuração; desklets de relógio e CPU/RAM.
- Recursos decorativos de interface em SVG/PNG.
- CLI reversível com instalação, diagnóstico, ativação, backup e restauração.
- Pacote `.deb` passivo.
- Extras de cores de terminal e temas para VS Code.
- Documentação de compatibilidade, lacunas e testes de aceitação.
