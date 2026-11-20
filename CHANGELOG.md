# Histórico

## 0.4.0 (2026-11-19, testado em Ubuntu 24.04 + Cinnamon 6.0.4, X11)

- Nemo escuro no tom da referência: barra de título azul-marinho com brilho e filete claro, barra de ferramentas e breadcrumb mais escuros, área de arquivos #122039, barra lateral #0f1b2b, seleção azul com texto branco (4,9:1), hover acinzentado, item selecionado em ícones com contorno azul, barra inferior uniforme. Cores do Nemo viram tokens `fm_*` nas duas variantes.
- Nemo: caminho em migalhas (breadcrumb) numa caixa arredondada única, pasta atual em negrito e seta › após cada pasta; barra de ferramentas no tom da referência (#d8e8fb). Ctrl+L continua abrindo o caminho em texto.
- Barra de título em azul mais vivo com brilho suave e sem a linha escura de divisão; barra de ferramentas do Nemo em tom próprio, com linha inferior suave (variantes Light e Dark).
- Nemo: barra lateral com linhas mais altas e seleção de borda a borda, seleção forte também sem foco; visualização em ícones com item selecionado em bloco claro com contorno de destaque; botão de visualização ativo com contorno. Cantos da seleção da barra lateral ficam retos: o GtkTreeView pinta a seleção por coluna.
- **Ícones simbólicos**: os 38 ícones de status padrão do pacote (rede, Bluetooth, volume, bateria, clima, notificações…) eram contornos com traço e um ponto em `currentColor`. O GTK recolore simbólicos forçando `fill` em todas as formas, então viravam borrões com partes pretas, e os PNGs nem eram recoloridos. Esses nomes saíram do pacote e vêm do Yaru (via `Inherits`); os 5 simbólicos próprios (`cinnamon12-*`) foram redesenhados só com formas preenchidas e ficam só em SVG. O pacote passa de 202 para 164 nomes. Quick Settings: o sino de "Não perturbe" desligado usa `preferences-system-notifications-symbolic` (o `notifications-symbolic` só existia no nosso pacote). O catálogo `assets/previews/catalogo-icones.jpg` precisa ser regerado com `generate-assets.py` (requer cairosvg).
- **GTK, janela inativa**: o Adwaita pinta o estado `:backdrop` com cinzas fixos (#353535, #303030...) e esses seletores venciam os nossos, então a janela sem foco ficava cinza. Agora fundo, listas, barras laterais, abas, campos, menus, switches, sliders e botões (inclusive marcados, desabilitados e de ação principal, que o Adwaita pinta com `background-image`) seguem as cores do tema também sem foco. Os botões de escolha de tema/ícones/cursor do cinnamon-settings (classe `.gtkstyle-fallback`, cinza fixo no Adwaita) também seguem o tema. O fundo cinza do arranjo de monitores em Configurações > Tela vem do CSS do próprio cinnamon-control-center, com prioridade acima do tema.
- **GTK, item selecionado com o mouse em cima**: a regra de hover (fundo claro) vencia a de seleção, que mantinha o texto branco; no tema claro o nome sumia. Seleção agora prevalece no hover (barra lateral do Nemo, listas, GtkListBox).
- **Nemo**: a seleção na barra lateral (e na lista em modo detalhes) aparecia como uma corrente de bolhas arredondadas, porque o GtkTreeView pinta a seleção por célula. Linhas de árvore agora são retas e contínuas; itens de ícone e linhas de GtkListBox continuam arredondados.
- **Barra de tarefas de largura total**, como a do Windows: barra sólida de 48 px de borda a borda, no mesmo azul-marinho translúcido, com filete fino do lado da área de trabalho. Os destaques de hover, janela ativa (com indicador ciano), janela aberta e "pedindo atenção" são pílulas inset 4 px, desenhadas como `border-image`. Funciona em painéis horizontais e verticais.
- Pílulas da lista de janelas quadradas (40×40, via `min-width`, pois o applet zera o padding inline). "Mostrar área de trabalho" virou uma faixa de 14 px no canto, estilo Windows: vai até a borda da tela (basta jogar o mouse no canto), um pouco mais clara que a barra em repouso e mais clara no hover, afastada 8 px do relógio. O painel não tem padding nesse lado; pressupõe o applet como o último, como no layout padrão e no perfil `panel apply`.
- `panel apply`: altura padrão 48 px, ícones de 28 px nas zonas esquerda e central (`panel-zone-icon-sizes`) e ícones de status (rede, som, energia, quick settings) de 16 para 20 px (`panel-zone-symbolic-icon-sizes`), com backup e restore; backups antigos são completados.
- Destaque dos applets: quadrado e centralizado (32×32 nas pontas, 40×40 no centro, igual à lista de janelas), por padding simétrico; antes era uma faixa estreita e alta com listra no meio.
- **Launcher** abre 10 px acima da barra, como o menu Iniciar do Windows.
- **Contraste WCAG AA** nas duas variantes: no Light, azul de destaque como texto `#056bbb` e preenchimento sob texto branco `#0571c4`; no Dark, o azul vivo é mantido e o texto sobre ele passa a ser azul-marinho `#06203d` (6,5:1 em vez de 2,5:1). Vale para shell, GTK3/GTK4 e para os SVG de checkbox, rádio e toggle. O `validate.py` agora reprova pares de texto abaixo de 4,5:1.
- **Launcher**: barras de rolagem finas (8 px) no shell; categorias cabem sem rolagem. Categorias, variante Dark e botões de sessão verificados (sair, reiniciar e desligar sempre pedem confirmação).
- **Desklets**: `c12-calendar` (mês, navegação, hoje destacado, início da semana automático/domingo/segunda, números de semana opcionais), `c12-performance` reescrito como Monitor do sistema (CPU e RAM com gráfico de histórico, barras de CPU/RAM/disco, velocidade de rede; leitura de /proc e do sistema de arquivos; intervalo 1–5 s) e `c12-weather` (Open-Meteo, **desligado por padrão**: exige cidade digitada + permissão de rede; cache local, atualização mínima de 30 min, modo offline). Todos com configurações e tradução pt-BR.
- `cinnamon12 widgets apply [--weather] | restore`: coloca os desklets na coluna esquerda do monitor principal, com backup de `enabled-desklets`; `uninstall` também restaura.
- Cartões dos widgets mais opacos (tokens `widget`).
- **Cinnamon12 Quick Settings** (`c12-quicksettings@cinnamon12.local`): cabeçalho com data/hora, cartões Wi-Fi (NetworkManager), Bluetooth (BlueZ), Modo escuro (alterna Cinnamon12 Light/Dark + `org.x.apps.portal color-scheme`), Não perturbe, Luz noturna (só onde o Cinnamon implementa, 6.2+) e Modo de energia (só com power-profiles-daemon); sliders de volume (Cvc) e brilho (csd-power); atalhos Tela, Modo avião (desliga Wi-Fi/WWAN/Bluetooth e restaura o estado anterior), Captura de tela e Configurações. Estados atualizados por sinais, sem polling; controles sem backend ficam ocultos. Tradução pt-BR.
- `cinnamon12 panel apply --quick-settings` coloca o applet antes do relógio; `apply` também guarda/restaura `org.x.apps.portal color-scheme`; `restore` reconhece a troca Light/Dark feita pelo cartão.
- **Cinnamon12 Search** (`c12-search@cinnamon12.local`), busca no estilo do Windows ao lado do Iniciar. No painel: campo de busca em que se digita direto (o painel captura o teclado com um grab modal ao clicar; Esc ou clique fora devolve), ícone de lupa ou oculto (só atalho). Os resultados abrem no primeiro caractere: Melhor correspondência, Aplicativos, Configurações (itens do menu com categoria Settings), Arquivos e Pastas da home. Painel de detalhes ao lado com as ações do item selecionado: app (abrir, ações do .desktop, abrir local do atalho, fixar na barra de tarefas e no Iniciar, recentes que o app abre); arquivo (abrir com o padrão e com outros apps recomendados, abrir local, copiar caminho, local/tipo/tamanho/data); pasta (idem, mais abrir no terminal). Setas trocam a seleção, Enter abre, Ctrl+Enter abre o local; o hover não troca o painel, a seta (›) da linha sim. Índice de nomes da home feito por `indexer.py` em processo separado com prioridade baixa (pastas ocultas, `node_modules`, `vendor`, `target` etc. e pastas configuráveis ficam de fora; padrão `go, snap`), consultado com `grep -P`, sem acento e sem diferenciar maiúsculas; o shell não varre o disco nem guarda o índice. `cinnamon12 panel apply --search` coloca o applet depois do menu. Tradução pt-BR.
- `c12-quicklinks` permanece como alternativa simples (só atalhos).
- **Cinnamon12 Start** (`c12-start@cinnamon12.local`) reescrito: busca (nome, descrição, palavras-chave, executável, sem acento), categorias do menu do sistema, grade de fixados (favoritos do Cinnamon; clique direito fixa/desafixa), arquivos recentes (histórico local do GTK, desligável), Locais, usuário (AccountsService) e botões bloquear/sair/reiniciar/desligar com as confirmações do próprio Cinnamon.
- Atalho Super configurável, navegação por setas/Tab/Enter, `settings-schema.json` (largura, altura, colunas, recentes, atalho), tradução pt-BR (gettext).
- `cinnamon12 panel apply --launcher cinnamon12` troca o menu nativo pelo Cinnamon12 Start (o `panel restore` devolve o menu original).
- Estilo do launcher nos temas Light/Dark.
- O menu abre alinhado à borda esquerda do botão e cresce para a direita (RTL: espelhado), sem sair da tela; opção "Centralizado no botão" nas configurações.

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
