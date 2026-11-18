# Cinnamon 12 Concept

**Especificação de produto, design, arquitetura, desenvolvimento, instalação e distribuição**  
**Alvo obrigatório:** Ubuntu **24.04 LTS** + Cinnamon **6.0.4**, já instalados  
**Arte de referência:** [`referencia-visual.png`](./referencia-visual.png)  
**Status:** especificação para implementação por agente de programação  
**Idioma da interface proposto:** pt-BR, com estrutura preparada para traduções  
**Versão desta especificação:** 1.0

> **Missão do agente:** transformar a instalação *existente* do Cinnamon 6.0.4 em um desktop de estética moderna, inspirado em conceitos visuais de um hipotético “Windows 12”, sem instalar outro desktop, sem substituir Cinnamon/Muffin, sem atualizar o Ubuntu, sem modificar arquivos de pacotes do sistema e sem colocar em risco as configurações pessoais. Implementar código real e instalável, não apenas uma demonstração HTML. A imagem é uma referência estética, **não** uma captura de software funcional. O projeto deve oferecer instalação local, ativação, backup/restauração, desinstalação e construção de pacote `.deb` opcional.

---

## 1. Contexto e decisões fechadas

| Item | Decisão |
|---|---|
| Distribuição | Ubuntu 24.04 LTS (Noble Numbat) |
| Ambiente desktop | Cinnamon 6.0.4, versão **mínima e alvo prioritário** de compatibilidade |
| Sessão | Priorizar **X11**; detectar sessão real. Wayland em Cinnamon 6.0 é experimental e fica fora do escopo inicial |
| Gerenciador de janelas | Muffin existente; **não** substituir |
| Gerenciador de arquivos | Nemo existente; tema GTK, sem fork do Nemo |
| Filosofia | Tema nativo + ícones + configuração de painel + applets/desklets, apenas quando necessários |
| Formatos | Código-fonte, instalação local por usuário, pacote `.deb` de distribuição opcional |
| Identidade | “Cinnamon 12 Concept”; **não** apresentar como Windows oficial, nem usar logotipos proprietários como marca do projeto |
| Padrão inicial | **Light Blue**: superfícies azul-claro, painel escuro translúcido e destaques cyan |
| Alternância | Variante **Dark Blue** desde a arquitetura; implementar sem comprometer a versão clara |
| Geometria | Cantos **pouco arredondados** (4–8 px na maioria dos componentes), conforme segunda referência aprovada |
| Foco | Usabilidade diária, estabilidade, acessibilidade, desempenho e reversibilidade |

**Importante:** a imagem mostra *simultaneamente* menu aberto, configuração rápida, widgets e várias janelas para demonstrar o visual. No uso normal, os painéis de menu e quick settings devem abrir **sob demanda**, sem ocupar permanentemente a tela.

### 1.1 Não objetivos

- Não instalar Windows nem executar binários Windows para simular a interface.
- Não instalar KDE Plasma, GNOME Shell, Hyprland, Compiz ou outro gerenciador de janelas.
- Não alterar o esquema de partições, bootloader, login manager, kernel ou sistema de arquivos.
- Não substituir pacotes `cinnamon`, `muffin`, `nemo`, `cinnamon-session` ou dependências por builds próprios.
- Não prometer desfoque de fundo real (*backdrop blur*) ou integração perfeita com apps GTK4/libadwaita se o compositor/API existente não suportar.
- Não modificar o `cinnamon.css` original em `/usr/share/cinnamon/theme/`.
- Não afirmar que layout, localização, métricas de CPU/RAM, data ou texto da imagem representam o sistema real.

---

## 2. Regras obrigatórias para o agente executor

1. **Inspecionar o sistema antes de escrever scripts ou alterar configurações.** Não presumir que toda instalação do Ubuntu 24.04 usa a mesma coleção de pacotes/temas.
2. Produzir **código-fonte versionado, reproduzível, auditável**; nunca entregar só uma imagem ou mockup web.
3. Fazer **backup das configurações impactadas** antes de `apply` e oferecer `restore` com caminho testado.
4. `install` (copiar arquivos) e `apply` (mudar preferência do usuário) devem ser **ações diferentes**.
5. O projeto deve funcionar **sem root na instalação local**, utilizando `~/.themes`, `~/.local/share/icons`, `~/.local/share/cinnamon` etc.
6. Qualquer `sudo` é autorizado **somente** na instalação do `.deb` ou dependências consentidas. Nunca executar `gsettings` como root para configurar a sessão do usuário.
7. Cada applet customizado deve ter UUID próprio e não sobrescrever os de Cinnamon ou terceiros.
8. Testar e documentar **Cinnamon 6.0.4 especificamente**. Exemplos e APIs de Cinnamon 6.2+ não comprovam compatibilidade.
9. Scripts precisam ser idempotentes. Reaplicar não deve duplicar applets, quebrar painel ou destruir preferências.
10. Qualquer recurso não implementado deve ser marcado como “planejado/limitado” e não exibido como controle funcional.
11. Não criar dependência de serviços online para funções essenciais do desktop.
12. Se houver conflito entre beleza e confiabilidade, escolher confiabilidade; oferecer modo conservador.
13. Não coletar nem transmitir dados pessoais. Consulta de clima só com opt-in; mostrar fonte e política de cache.
14. Não usar códigos, imagens, fontes ou ícones de licença incompatível. Criar ou licenciar claramente os assets.
15. Após cada etapa utilizável, entregar instruções de teste, resultado e forma de reverter.

---

## 3. Referência visual e linguagem do design

### 3.1 Leitura da imagem

O arquivo `referencia-visual.png` é a principal referência visual e deve acompanhar esta especificação em todo briefing do agente. As principais características são:

- Wallpaper azul, com curvas/ribbons tridimensionais luminosas, gradientes entre azul profundo, azul celeste e cyan.
- Painel inferior **flutuante visualmente**, longo, pouco afastado das bordas, com fundo azul-marinho semitransparente, **não** uma ilha com cantos exageradamente redondos.
- Ícones de aplicativos centralizados no painel; informação de clima à esquerda; status, relógio e notificações à direita.
- Menu de aplicativos centralizado, mais largo que o menu padrão do Cinnamon; campo de busca no topo; categorias à esquerda; fixados e recentes à direita.
- “Central de configurações rápidas” à direita, com cartões Wi-Fi, Bluetooth, modo escuro, brilho, volume etc.
- Widgets à esquerda (clima, calendário, monitor de recursos), preferencialmente desklets reposicionáveis ou um painel retrátil.
- Janelas de Nemo, navegador, terminal, configurações e gerenciador de aplicativos com estilo coordenado.
- Cor das janelas clara e levemente azulada, cabeçalhos discretos e sombras suaves.
- Bordas com **raio pequeno**, geometria quase retangular, visual tecnológico sem excesso de efeito de vidro.
- Ícones de pastas com gradiente azul/cyan e alguns acentos violeta.
- Tela limpa; a composição com todas as janelas abertas é uma **vitrine**, não o layout padrão ao iniciar.

### 3.2 Tokens sugeridos

São pontos de partida, não amostras exatas extraídas por colorimetria. A equipe deverá ajustá-los olhando a imagem lado a lado com capturas reais no Cinnamon.

| Token | Light Blue | Dark Blue | Uso |
|---|---|---|---|
| `accent-primary` | `#078FE8` | `#2BAAFF` | Seleção, botões, foco |
| `accent-hover` | `#0A72C8` | `#56BBFF` | Hover |
| `accent-secondary` | `#13C8F3` | `#36CCF6` | Realce cyan |
| `text-primary` | `#172A43` | `#EAF3FF` | Texto geral |
| `text-secondary` | `#546B87` | `#A9BDD4` | Legendas |
| `surface-window` | `#EAF3FE` | `#182A40` | Superfície GTK |
| `surface-sidebar` | `#D8E9FB` | `#142438` | Sidebars |
| `surface-selected` | `#C1E2FF` | `#244C70` | Itens selecionados |
| `panel-bg` | `rgba(15,44,86,0.84)` | `rgba(9,20,40,0.90)` | Painel inferior |
| `popover-bg` | `rgba(228,241,255,0.96)` | `rgba(24,41,61,0.97)` | Menu/quick settings |
| `widget-bg` | `rgba(26,75,126,0.84)` | `rgba(13,33,57,0.92)` | Widgets escuros |
| `border-subtle` | `rgba(255,255,255,0.38)` | `rgba(169,206,248,0.16)` | Contorno |
| `shadow-color` | `rgba(5,30,65,0.20)` | `rgba(0,0,0,0.38)` | Sombras |
| `success` | `#28B89A` | `#42D5AD` | Status positivo |
| `warning` | `#F3B34D` | `#F6C262` | Avisos |
| `danger` | `#D9516A` | `#F17189` | Erros |

**Regras de aplicação de tokens:** o estilo do Cinnamon/St **não** é o CSS completo de um browser. Não assumir suporte a variáveis `--css`, `backdrop-filter`, `filter` e propriedades modernas. Manter os tokens em `design/tokens.json` para gerar CSS com **valores literais resolvidos** por um build script, se necessário. CSS GTK3 e CSS Cinnamon devem ser compilados/testados **separadamente**.

### 3.3 Medidas e tipografia

| Elemento | Padrão | Detalhe |
|---|---:|---|
| Raio das janelas GTK | 6 px | Respeitar as limitações do WM/GTK |
| Raio do menu de aplicativos | 8 px | Evitar visual excessivamente “pill” |
| Raio das caixas de widget | 6 px | Borda suave e discreta |
| Raio dos botões | 4–6 px | Hover e focus visíveis |
| Raio das tiles de quick settings | 6 px | Bordas limpas |
| Painel inferior | 46–52 px de altura | Configurável; testar HiDPI |
| Margens visuais do painel | 8–14 px nas laterais e base | Se possível sem hacks no gerenciador |
| Ícones do painel | 22–26 px | Centralizados verticalmente |
| Espaçamento entre itens | 6–10 px | Sem desperdício |
| Sidebar GTK | 210–240 px, conforme janela | Responsiva |
| Menu | largura-alvo 550–650 px | Adaptável para 1366×768 |
| Quick settings | largura-alvo 320–360 px | Não cortar em telas pequenas |
| Fonte interface | `Ubuntu`, `Noto Sans` ou `Inter` se disponível | Nunca exigir Segoe UI proprietária |
| Fonte monospace | fonte existente de boa leitura | Terminal não precisa ser modificado globalmente |

**Acessibilidade:** contraste preferencial AA para texto regular; estados `hover`, `active`, `disabled`, `focus` distinguíveis; tamanho de fonte configurável; alto contraste básico; zoom/font scaling respeitado; não usar cor como única indicação de estado.

### 3.4 Wallpaper e ícones

- **Não** extrair a área de wallpaper da imagem como resultado final: ela está parcialmente coberta por janelas e ícones. Criar um **wallpaper original** com estética similar.
- Fornecer 1920×1080, 2560×1440 e, se viável, 3840×2160; o mesmo design com corte responsivo.
- Versões light/dark; evitar marca Windows ou logos oficiais desnecessários.
- Criar ícones próprios para menu/tema e/ou adaptar um conjunto open source com licença auditada (por exemplo, inspiração Fluent, **não** copiar arquivos de origem desconhecida).
- Um pacote de ícones precisa incluir `index.theme`, herança adequada, nomes de ícones freedesktop, tamanhos e fallbacks (não basta desenhar PNGs).
- Manter ícones reais dos aplicativos de terceiros sempre que necessário para reconhecimento. Não substituir logos de Firefox/VS Code etc. por versões fraudulentas.
- Estabelecer `assets/LICENSES.md`, atribuições, licenças e origem de cada asset.

---

## 4. Arquitetura: quais peças compõem um tema Cinnamon de verdade

O resultado exige **componentes separados**, com graus diferentes de complexidade:

| Camada | Tecnologia | Responsabilidade | Viabilidade |
|---|---|---|---|
| Shell Cinnamon | `cinnamon/cinnamon.css`, assets | Painel, popups, menus, applets, calendário e notificações gerenciados pelo Cinnamon | Alta |
| Aplicativos GTK3 | `gtk-3.0/gtk.css` | Nemo e outros programas compatíveis com GTK3 | Alta |
| GTK2 (opcional) | `gtk-2.0` ou herança | Aplicativos legados | Média |
| Decoração de janela | GTK/Muffin; `metacity-1` apenas se suportado pelo setup | Cabeçalhos, bordas, botões, sombras | Parcial; testar implementação real |
| Ícones e cursores | Icon theme, cursor theme | Visual do Nemo, menu, desktops e apontador | Alta |
| Wallpaper | PNG/JPEG/SVG (conforme suporte) | Fundo da área de trabalho | Alta |
| Layout do painel | GSettings + applets existentes | Três áreas: esquerda, centro, direita | Alta, conforme limitações |
| Novo menu | Applet Cinnamon em JS/CJS + St/Clutter | Launcher moderno, busca, favoritos | Média/alta, exige desenvolvimento |
| Quick settings | Applet Cinnamon em JS/CJS + APIs locais | Wi-Fi, áudio, brilho etc. | Média; depende dos backends |
| Widgets | Desklets Cinnamon | Clima, calendário, desempenho | Alta/média |
| Configurador | CLI primeiro, UI opcional em GTK3/Python | Perfis, ajustes, prévia, ativação | Média |
| Instalador/rollback | Bash/Python + dconf/GSettings | Instalação reversível e suporte | Alta |
| Distribuição | `.deb` + instalação manual | Instalação sistêmica opcional | Alta |

### Limitações reais a documentar

1. `cinnamon.css` permite translúcidez de superfícies, mas **não garante o desfoque do conteúdo atrás da janela**. Fazer fallback sem blur e não depender de extensões experimentais.
2. Nem todos os apps respeitam tema GTK3: GTK4/libadwaita, Firefox, Chrome/Chromium, Electron, Qt e Flatpaks podem usar decoração/tema próprio. Fornecer integração opcional ou recomendações, nunca prometer correspondência pixel-perfect.
3. Cantos da **janela inteira** e sombras externas dependem de WM/cliente, não apenas de CSS do Cinnamon.
4. Centralização de **ícones fixados** é factível com configuração do painel; centralização geométrica **perfeita de todos os ícones em qualquer largura e combinação de applets** pode exigir um applet de layout e deve ser tratada como recurso avançado.
5. O painel nativo não necessariamente permite área de clique realmente separada da borda. Simular painel flutuante visualmente se isso preservar estabilidade.
6. Implementar uma central de configurações rápidas real exige usar APIs do sistema e respeitar permissões. **Nunca** simular “Wi-Fi ligado” se o estado real estiver desligado.
7. Cinnamon 6.0.4 utiliza APIs JavaScript/CJS próprias; exemplos de versões posteriores precisam ser validados antes de reutilizar.

---

## 5. Descoberta prévia obrigatória (fase zero)

O agente deve criar `scripts/doctor.sh` (somente leitura) e registrar resultados **sem publicar dados pessoais**. Verificações sugeridas:

```bash
cat /etc/os-release
cinnamon --version
cinnamon-session --version 2>/dev/null || true
nemo --version 2>/dev/null || true
echo "${XDG_CURRENT_DESKTOP:-unset}"
echo "${XDG_SESSION_TYPE:-unset}"
command -v gsettings; command -v dconf
command -v dpkg-deb; command -v python3
command -v xrandr; command -v gdbus
command -v pactl; command -v wpctl
command -v nmcli; command -v bluetoothctl
command -v upower
ls -la /usr/share/themes
ls -la ~/.themes 2>/dev/null || true
ls -la /usr/share/cinnamon/applets
ls -la ~/.local/share/cinnamon/applets 2>/dev/null || true
gsettings list-schemas | grep -E '^org\.cinnamon|^org\.gnome\.desktop\.interface'
gsettings list-recursively org.cinnamon.theme 2>/dev/null || true
gsettings list-recursively org.cinnamon.desktop.interface 2>/dev/null || true
gsettings list-recursively org.cinnamon 2>/dev/null || true
```

**O agente deve verificar schema/key antes de escrever:**

```bash
gsettings list-keys org.cinnamon.theme
gsettings list-keys org.cinnamon.desktop.interface
gsettings list-keys org.cinnamon.desktop.background
# Testar existência antes de assumir que chave como "enabled-applets" é válida.
gsettings list-keys org.cinnamon | grep -E 'panel|applet|enabled'
```

**Diagnóstico:** versão real, sessão X11/Wayland, escalas/multi-monitor, tema ativo, GTK/icon/cursor ativo, lista de applets e posições, número de painéis, resoluções, dependências disponíveis, extensões instaladas, mecanismos de áudio e conexão, arquivos legíveis. Criar um relatório local sem tokens, SSIDs, nome completo do usuário, identificadores ou caminho completo da home em logs destinados à distribuição. Resultado: **GO/NO-GO** e ajustes de compatibilidade.

---

## 6. Implementação detalhada por componente

### C01. Tema Cinnamon / Shell (obrigatório, MVP)

**Objetivo:** painel, menu/popup existentes, tooltip, notificações e applets visualmente coordenados.

**Entregáveis:**

```text
themes/Cinnamon12-Light/cinnamon/cinnamon.css
themes/Cinnamon12-Dark/cinnamon/cinnamon.css
themes/*/cinnamon/assets/*
```

**Etapas:**

1. Copiar uma base de `cinnamon.css` **compatível com 6.0.4** do tema atual/instalação para o repositório, respeitando a licença e creditando origem. Evitar gerar uma folha parcial que deixe selectors essenciais sem estilos.
2. Mapear seletor por seletor do CSS real 6.0.4: painel, launcher, applets, calendário, status, notificações, menus de contexto, popup menus, systray, task list, volume, seletor de janelas.
3. Criar CSS claro e escuro a partir de design tokens resolvidos; **sem propriedades não suportadas**.
4. Ajustar fundo/transparência/hover/focus/disabled, tipografia, tamanhos e padding sem corromper layouts.
5. Testar barras no topo, base, esquerda e direita. A proposta prioriza bottom, mas o tema não pode quebrar se a pessoa mudar a posição.
6. Verificar logs ao carregar CSS: `~/.cinnamon/glass.log` e `~/.xsession-errors` quando existirem; não assumir que todo sistema produz ambos.

**Classes de referência para conferir no CSS instalado:** `#panel`, `.panel-button`, `.panel-top`, `.panel-bottom`, `.panel-left`, `.panel-right`, `.popup-menu-content`, `.popup-menu-item`, `.menu`, `.calendar`, `.notification`, `.tooltip`. **Não** inserir seletor sem verificar que existe ou tem o efeito pretendido na versão 6.0.4.

**Critério de aceite:** nenhum painel desaparece; menu e relógio legíveis; estilos claros/escuros completos; nenhuma mensagem de parse e nenhum fallback para tema padrão por CSS quebrado.

### C02. Tema GTK3 para janelas/Nemo (obrigatório, MVP)

**Entregáveis:**

```text
themes/Cinnamon12-Light/gtk-3.0/gtk.css
themes/Cinnamon12-Dark/gtk-3.0/gtk.css
# Assets e metadados adicionais, conforme tema-base e teste de descoberta.
```

**Requisitos visuais:** cabeçalho azul muito pálido, widgets de seleção com azul forte, sidebars levemente diferenciadas, botões com raio 4–6px, linhas divisórias finas, campos de busca suaves, barras de rolagem discretas, progress bars, caixas de diálogo, cards e toolbar.

**Itens obrigatórios:** `window`, `decoration`, `headerbar`, `menubar`, `toolbar`, `notebook`, `popover`, `entry`, `button`, `treeview`, `placessidebar`, `scrolledwindow`, `scrollbar`, `selection`, `tooltip`, `dialog` (ajustar aos seletores GTK3 válidos). Testar `:hover`, `:selected`, `:backdrop`, `:disabled`, `:focus`.

**Nemo:** ícones grandes, sidebar e breadcrumbs coerentes, grid/lista legíveis, seleção visível, miniaturas não quebradas, favoritos/montagens com contraste.

**Decoração:** verificar o que Muffin/GTK respeitam efetivamente nesta instalação. Se `metacity-1` for relevante, implementar um tema consistente e testá-lo; **não** assumir que esse diretório sozinho controla toda janela ou existe uma chave de `wm.preferences/theme` funcional.

**Limites:** temas Firefox/Electron/Qt/Flatpak/GTK4/libadwaita são integração extra, não requisitos centrais. Não tentar forçar CSS de sistema em apps sandbox por padrão.

### C03. Tema de ícones e cursor (obrigatório, MVP)

**Entregáveis:**

```text
icons/Cinnamon12-Icons/index.theme
icons/Cinnamon12-Icons/scalable/{actions,apps,devices,mimetypes,places,status}/...
icons/Cinnamon12-Icons/{16x16,24x24,32x32,48x48,64x64}/...
# Cursor: integrar um pacote existente legalmente reutilizável OU criar o próprio.
```

**Prioridades:** Home, Documents, Downloads, Desktop, Music, Pictures, Videos, Trash, drive, terminal, settings, software center, network, volume, battery, notifications, calendário, clima. Preferir ícones SVG próprios e rasterizar nos tamanhos necessários. `index.theme` com `Inherits` robusto (ex.: `Yaru`, `Adwaita`, `hicolor`, conforme verificação real). Testar 16/24/32/48 px e não depender de escala de SVG para tudo.

**Cuidado:** ícones de apps de terceiros ficam reconhecíveis; seguir nomes freedesktop existentes; cursor opcional, nunca dependência impeditiva.

### C04. Painel inferior inspirado em “Windows 12” (obrigatório, MVP)

**Layout pretendido:**

```text
┌────────────────────────────────────────────────────────────────────────┐
│ ☀ 24°C                 ◈  📁  🌐  >_  ⚙  [apps...]        ⌃ ◉ 🔊 16:52 │
└────────────────────────────────────────────────────────────────────────┘
   esquerda                       centro                       direita
```

- **Esquerda:** clima compacto opcional e/ou atalho de exibição de widgets.
- **Centro:** botão original do projeto, Nemo, navegador, terminal, apps fixados e executando. Usar *grouped-window-list* nativo quando possível.
- **Direita:** systray real, rede, som, notificações, relógio, status, botão Quick Settings.
- Preservar indicadores de app ativo, quantidade de instâncias, ordenação por arrastar e menu de contexto.
- Padrão de 48px, painel na base, visual com borda leve e arredondamento pequeno.
- Criar perfis `balanced`, `minimal` e `showcase`; o usuário deve poder voltar ao painel anterior.
- Se a mudança de layout automatizada não for 100% segura, fornecer modo **guiado** com instruções no Cinnamon Settings, e automatizar somente o que for comprovado.

**Implementação:** obter configuração do painel com `gsettings`/dconf em tempo de execução; preservar IDs, painel por monitor, instâncias de applets e áreas em vez de sobrescrever cegamente listas. Usar applets padrões para som, rede, relógio, janela e notificação sempre que possível.

**Critério de aceite:** ícones centralizados em monitor primário a 1366×768/1920×1080; barra funcional com teclado e mouse; autohide opcional; não quebrar múltiplos monitores.

### C05. Launcher / Menu de aplicativos moderno (fase 2)

**Não** é uma simples decoração do menu padrão. Para obter layout da imagem, criar applet próprio, sem patch direto em `menu@cinnamon.org`.

**Estrutura Cinnamon:**

```text
applets/launcher@cinnamon12.local/
  metadata.json
  applet.js
  settings-schema.json
  stylesheet.css           # somente se comprovado suporte/uso apropriado; caso contrário CSS no tema
  icons/
  locale/                  # quando adotada internacionalização
```

**Tecnologia:** CJS de Cinnamon 6.0.4, com `imports.ui.applet`, `imports.ui.popupMenu`, `imports.gi.St`, `imports.gi.Clutter`, `Gio`, `GLib` e APIs *efetivamente disponíveis* nessa versão. Não adotar sintaxe ES modules moderna nem APIs exclusivas do GNOME Shell.

**Interface esperada:**

- Busca no topo com foco ao abrir, placeholder em pt-BR e pesquisa incremental com debounce.
- Coluna esquerda: Todos, Favoritos, Acessórios, Gráficos, Internet, Escritório, Som e Vídeo, Administração, Preferências, Locais.
- Grade de fixados (5 colunas no layout amplo; menos colunas em tela pequena).
- “Recomendados/Recentes” **somente se houver fonte local real**, privacidade e opção de ocultar. Sem inventar histórico.
- Rodapé com usuário, bloquear tela, sair, reiniciar, desligar, usando mecanismos de sessão autorizados e confirmação quando apropriado.
- Ícones conforme temas freedesktop e arquivos `.desktop`; pesquisa deve usar APIs de aplicativos Gio/Cinnamon, não comandos de shell concatenados a entradas do usuário.
- Configurações: tamanho do menu, categorias, fixados, histórico, ocultar/reordenar seções, posição em relação ao botão.
- Escapar HTML/texto e validar qualquer chamada de shell; evitar `eval`, `sudo` e comandos construídos de resultados da pesquisa.
- Navegação de teclado: Super (se integração viável sem conflito), Esc, setas, Enter, Tab; screen-reader quando suportado.

**Comportamento:** no clique, popup abre ancorado ao painel, com sensação de centralizado; se o Cinnamon 6.0.4 não permitir âncora central sem hack, documentar e implementar posição próxima ao botão com boa UX. Fechar ao perder foco, ao iniciar app ou pressionar Esc.

**Padrão de vida do applet:** expor `main(metadata, orientation, panelHeight, instanceId)` somente conforme assinatura comprovada em código-fonte compatível; limpar sinais, timers e subscriptions em `on_applet_removed_from_panel()` e no teardown aplicável; sem vazamentos/duplicação após recarregar.

**Alternativa de menor custo:** avaliar o applet padrão ou um menu comunitário compatível e licenciado; se uso dele não atingir o conceito, criar applet próprio. Não carregar xlets desenvolvidos para Cinnamon 6.4/6.6 sem teste.

### C06. Central de configurações rápidas (fase 2/3)

**Applet próprio:** `quicksettings@cinnamon12.local`, seguindo a mesma estrutura do launcher.

**Visual:** popup de 320–360 px alinhado à borda direita, tiles pouco arredondados (6 px), grade de duas colunas, fundo azul-claro ou escuro, sliders de áudio e brilho, acesso a configurações reais.

| Controle | Fonte de verdade | Requisito |
|---|---|---|
| Wi-Fi / conectividade | NetworkManager via D-Bus/Gio ou integração já presente | Exibir estado real; alternar somente se autorizado |
| Bluetooth | BlueZ e adaptadores disponíveis | Ocultar/desabilitar quando inexistente |
| Volume | API de áudio existente, PulseAudio/PipeWire compatível ou applet nativo | Estado sincronizado bidirecionalmente |
| Brilho | Backlight via interfaces disponíveis/Power API | Se indisponível, mostrar “não suportado” ou ocultar |
| Modo escuro | Troca coordenada de temas (Cinnamon + GTK + ícones quando necessário) | Persistência e rollback |
| Luz noturna | Usar serviço/integração suportados pelo ambiente | Nunca botão decorativo fingindo ativação |
| Não perturbe | Integração de notificações do Cinnamon, se API disponível | Refletir estado real |
| Energia | Serviço de perfis de energia, se instalado | Não forçar governor ou alterar sistema sem permissão |
| Configurações | Chamar `cinnamon-settings`/módulo suportado | Funcionar mesmo com controles ausentes |

Usar sinais D-Bus/observadores em vez de polling frequente. Não incluir senha, SSID ou dados de conexão em logs. Acessos privilegiados devem seguir PolicyKit/DBus; **nunca** conceder root a applets.

**Critério:** todos os toggles que aparecem são funcionais, atualizam quando outro app muda o estado e mantêm feedback correto em ausência de hardware.

### C07. Widgets / desklets (fase 2)

**Estrutura:** `desklets/weather@cinnamon12.local`, `calendar@cinnamon12.local`, `sysmon@cinnamon12.local`, cada um com `metadata.json`, `desklet.js`, `settings-schema.json` e assets próprios, conforme APIs de Cinnamon 6.0.4.

**Clima:** escolher cidade manualmente, temperatura, descrição, ícone e previsão simplificada; **nunca assumir Londres como localização**; provider documentado, acesso externo opt-in, cache local, limite de consultas, fallback “indisponível”, respeito a rate limits. Não embutir chave privada de API.

**Calendário:** localidade pt-BR, início da semana configurável, data e horário do sistema, integração com calendário existente **opcional** e explicitamente autorizada; não inventar compromissos.

**Monitor:** CPU, memória, disco e rede via fontes locais Linux (ex. `/proc/stat`, `/proc/meminfo`, `/proc/net/dev`, `statvfs`); mostrar taxas calculadas ao longo de intervalos e não o valor da imagem; frequência configurável de 1–5 s; desempenho eficiente; labels acessíveis.

**Posição:** cards lado esquerdo reposicionáveis, possibilidade de desligar cada desklet, salvar layout sem alterar os desklets do usuário existentes. Sem exigir 3 widgets ativos por padrão.

### C08. Tema de configurações e outros apps (fase 3)

Aplicar estilo GTK3 genericamente a `cinnamon-settings`, Nemo e gerenciadores GTK3; não falsificar internamente a interface desses programas. Telas GTK4/Qt/Electron poderão diferir. Criar guia para Firefox (*theme extension* opcional), VS Code (tema do editor opcional), terminal (paleta opcional), Qt (QGnomePlatform/Kvantum **apenas se viável**, sem dependência mandatória).

### C09. Alternância Light/Dark (fim do MVP, antes da v1)

- Perfis de tema: `light`, `dark`.
- Trocar Shell Cinnamon, GTK3, ícones compatíveis e preferências relevantes **como uma transação lógica com rollback**.
- Não redefinir papel de parede ou fonte do usuário sem consentimento específico.
- Respeitar outros serviços de modo escuro quando possível; testar applets abertos durante a mudança.
- `cinnamon12ctl apply --profile light|dark` deve mostrar o que mudou e permitir `restore`.

---

## 7. Estrutura recomendada do repositório

```text
cinnamon12-concept/
├── README.md
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SPEC.md
├── assets/
│   ├── referencia-visual.png
│   ├── LICENSES.md
│   ├── wallpapers/
│   │   ├── cinnamon12-light-1920x1080.png
│   │   ├── cinnamon12-light-2560x1440.png
│   │   ├── cinnamon12-dark-1920x1080.png
│   │   └── cinnamon12-dark-2560x1440.png
│   └── sources/                 # fontes originais editáveis (SVG, etc.)
├── design/
│   ├── tokens.json
│   ├── typography.md
│   └── components.md
├── themes/
│   ├── Cinnamon12-Light/
│   │   ├── cinnamon/cinnamon.css
│   │   ├── gtk-3.0/gtk.css
│   │   └── ...
│   └── Cinnamon12-Dark/
│       ├── cinnamon/cinnamon.css
│       ├── gtk-3.0/gtk.css
│       └── ...
├── icons/
│   └── Cinnamon12-Icons/
│       ├── index.theme
│       └── ...
├── applets/
│   ├── launcher@cinnamon12.local/
│   └── quicksettings@cinnamon12.local/
├── desklets/
│   ├── weather@cinnamon12.local/
│   ├── calendar@cinnamon12.local/
│   └── sysmon@cinnamon12.local/
├── bin/
│   └── cinnamon12ctl             # CLI de ativação/configuração e rollback
├── scripts/
│   ├── doctor.sh
│   ├── install-local.sh
│   ├── activate.sh
│   ├── restore.sh
│   ├── uninstall-local.sh
│   ├── build-assets.sh
│   ├── build-deb.sh
│   ├── lint.sh
│   └── smoke-test.sh
├── packaging/
│   └── debian/
│       ├── control.in
│       └── ...
├── tests/
│   ├── fixtures/
│   ├── shell/
│   ├── xlets/
│   └── screenshots/
└── docs/
    ├── INSTALL.md
    ├── RESTORE.md
    ├── COMPATIBILITY.md
    ├── DESIGN-LIMITATIONS.md
    └── QA-CHECKLIST.md
```

O agente pode simplificar a árvore **se justificar** e se mantiver separação clara entre fonte, assets, artefatos compilados, scripts e empacotamento.

---

## 8. Instalação local, ativação e desinstalação

### 8.1 Diretórios-alvo

| Item | Instalação por usuário | Instalação sistêmica por `.deb` |
|---|---|---|
| Tema Cinnamon + GTK | `~/.themes/Cinnamon12-{Light,Dark}/` | `/usr/share/themes/Cinnamon12-{Light,Dark}/` |
| Ícones | `~/.local/share/icons/Cinnamon12-Icons/` | `/usr/share/icons/Cinnamon12-Icons/` |
| Cursores (opcional) | `~/.local/share/icons/<nome-cursor>/` | `/usr/share/icons/<nome-cursor>/` |
| Applets | `~/.local/share/cinnamon/applets/<uuid>/` | `/usr/share/cinnamon/applets/<uuid>/` |
| Desklets | `~/.local/share/cinnamon/desklets/<uuid>/` | `/usr/share/cinnamon/desklets/<uuid>/` |
| Wallpapers | `~/.local/share/backgrounds/cinnamon12/` | `/usr/share/backgrounds/cinnamon12/` |
| CLI | `~/.local/bin/cinnamon12ctl` | `/usr/bin/cinnamon12ctl` |
| Configuração de usuário | `~/.config/cinnamon12/` | **Nunca** em `/etc` com dados pessoais |
| Backup | `~/.local/state/cinnamon12/backups/<timestamp>/` | **Sempre** na home do usuário que aplicou |

Usar `$XDG_CONFIG_HOME`, `$XDG_DATA_HOME` e `$XDG_STATE_HOME` quando adequados, com fallbacks para os caminhos acima. Não confiar apenas no caminho hard-coded da home.

### 8.2 Comandos de experiência pretendida (a serem implementados)

> Os comandos abaixo são **contrato de interface para o software que o agente construirá**; não são comandos de um pacote já existente.

```bash
# Conferência sem alterações
./scripts/doctor.sh

# Listar arquivos e ações; não modificar ainda
./scripts/install-local.sh --dry-run

# Instalar arquivos apenas para o usuário atual
./scripts/install-local.sh

# Criar snapshot e aplicar visual (apenas após confirmação)
./scripts/activate.sh --profile light

# Ver a configuração efetivamente ativa
cinnamon12ctl status

# Trocar para modo escuro
cinnamon12ctl apply --profile dark

# Restaurar alterações do projeto
cinnamon12ctl restore --latest

# Desinstalar arquivos locais (restaurar antes, ou solicitar confirmação)
./scripts/uninstall-local.sh
```

### 8.3 Ativação: GSettings/dconf

A implementação deve consultar schemas/chaves presentes e só executar mudanças suportadas. Exemplos **plausíveis e sujeitos a verificação pelo `doctor`**:

```bash
# Tema do shell (Cinnamon) existente
gsettings set org.cinnamon.theme name 'Cinnamon12-Light'

# Aparência de aplicativos GTK3 compatíveis
gsettings set org.cinnamon.desktop.interface gtk-theme 'Cinnamon12-Light'

# Ícones
gsettings set org.cinnamon.desktop.interface icon-theme 'Cinnamon12-Icons'
```

O aplicativo deve **salvar os valores anteriores** antes de cada mudança, confirmar a disponibilidade do tema escolhido e mostrar erro claro em caso de falha. Configuração de fonte, cursor, wallpaper, painel e applets só com chave validada e consentimento.

**Não** executar `gsettings reset-recursively` em schemas do Cinnamon; **não** fazer `dconf reset -f /org/cinnamon/` ou equivalentes; **não** reescrever o dconf inteiro durante restauração comum.

### 8.4 Snapshot e restauração

Antes da primeira ativação:

1. Capturar `dconf dump /org/cinnamon/` **apenas como backup de contingência**, sem restaurar tudo indiscriminadamente.
2. Capturar chaves específicas alteradas com schema/key, valor anterior em representação válida para GSettings e existência da chave.
3. Capturar lista/posição/instâncias de applets/painéis e estado de desklets que serão mexidos.
4. Registrar hashes dos arquivos gerenciados pelo projeto para evitar apagar arquivo editado pelo usuário.
5. Criar manifesto `snapshot.json` com versão do projeto, Cinnamon, timestamp, perfil e alterações.
6. Marcar backup mais recente para restauração; manter pelo menos os últimos 3 snapshots configuráveis.
7. Aplicar mudanças em ordem segura; em falha, fazer rollback **apenas das chaves alteradas neste ciclo**.
8. Restaurar somente as chaves que o Cinnamon12 modificou, respeitando alterações do usuário ocorridas depois. Em conflito, avisar e perguntar antes de sobrescrever.
9. Sempre permitir restaurar o tema original da GUI Cinnamon Settings, mesmo que o script falhe.

**Teste de restauração:** comparar, de forma normalizada, os valores gerenciados antes do `apply` com os valores após `restore`; o resultado precisa ser idêntico nos campos gerenciados sem apagar valores estranhos ao projeto.

### 8.5 Recuperação de problema visual

Documentar, pelo menos:

- Como sair da sessão e entrar novamente em Cinnamon X11.
- Como abrir TTY para restaurar com comandos de usuário, se painel/menu ficar inoperante.
- Como escolher tema padrão via `gsettings` usando os **valores salvos** (não nomes inventados).
- Como desabilitar **somente** um applet recém-adicionado, sem apagar todos os applets.
- Como iniciar o Cinnamon Settings por terminal/atalho se o menu do projeto falhar.
- Onde olhar logs relevantes de Cinnamon, X11, user journal e mensagens de xlets.

**Jamais** usar `rm -rf ~/.config/cinnamon`, `dconf reset -f /org/cinnamon/`, substituição de arquivos do sistema ou reinstalação de Cinnamon como primeira medida.

---

## 9. Distribuição `.deb` (opcional, mas prevista desde o início)

### 9.1 Resposta objetiva

**Um `.deb` não é necessário para personalizar o Cinnamon.** Para um computador, a instalação em diretórios do próprio usuário é mais segura e rápida. O `.deb` será útil para distribuir versões, atualizar/remover com APT e instalar para múltiplos usuários.

### 9.2 Proposta de pacote

- Nome Debian: `cinnamon12-concept` (nome provisório, sem colisão com pacotes do repositório).
- Versão inicial: `0.1.0-1`.
- Arquitetura: `all` **somente** se código/assets forem independentes de arquitetura (JS/Python/Shell, SVG/PNG/CSS).
- Categoria: `x11` ou `misc` conforme política Debian.
- Dependências mínimas reais: ajustar após `doctor` e inspeção do código, por exemplo `cinnamon (>= 6.0), python3, bash` se de fato usados. Não criar dependência que atualize o Cinnamon 6.0.4 à força.
- `Recommends` para integrações opcionais só quando justificadas; considerar `Suggests` para programas opcionais.
- Licenças e atribuições incluídas no pacote em `/usr/share/doc/cinnamon12-concept/`.

**Exemplo ilustrativo de `DEBIAN/control`:**

```debcontrol
Package: cinnamon12-concept
Version: 0.1.0-1
Section: x11
Priority: optional
Architecture: all
Maintainer: Cinnamon12 Project <maintainer@example.invalid>
Depends: cinnamon (>= 6.0), python3, bash
Description: Modern light and dark visual theme for Cinnamon
 Theme, icons, wallpapers and optional applets for Cinnamon 6.0.4.
 Activation is explicit and reversible for each user.
```

O campo `Maintainer` acima é **placeholder**: usar identidade de mantenedor real apenas quando fornecida. Checar dependências via `dpkg-checkbuilddeps`/`lintian` se disponíveis. Não incluir um e-mail inventado em pacote final.

### 9.3 Conteúdo do `.deb`

```text
/usr/share/themes/Cinnamon12-Light/...
/usr/share/themes/Cinnamon12-Dark/...
/usr/share/icons/Cinnamon12-Icons/...
/usr/share/backgrounds/cinnamon12/...
/usr/share/cinnamon/applets/launcher@cinnamon12.local/...
/usr/share/cinnamon/applets/quicksettings@cinnamon12.local/...
/usr/share/cinnamon/desklets/weather@cinnamon12.local/...
/usr/share/cinnamon/desklets/calendar@cinnamon12.local/...
/usr/share/cinnamon/desklets/sysmon@cinnamon12.local/...
/usr/bin/cinnamon12ctl
/usr/share/doc/cinnamon12-concept/...
```

**Regra crítica:** `postinst`/`prerm`/`postrm` **não** devem alterar `gsettings` de um usuário arbitrário nem executar scripts de configuração de sessão como root. Instalar via APT disponibiliza arquivos para todos; cada usuário ativa explicitamente com `cinnamon12ctl apply`. A remoção do `.deb` não deve apagar backups pessoais. Se um tema ativo for removido, documentar/gerenciar fallback seguro mediante comando prévio executado pelo usuário.

### 9.4 Build e instalação

```bash
# Exemplos do fluxo final a implementar
./scripts/build-assets.sh
./scripts/build-deb.sh

# Inspecionar conteúdo antes da instalação
# dpkg-deb --contents dist/cinnamon12-concept_0.1.0-1_all.deb
# dpkg-deb --info dist/cinnamon12-concept_0.1.0-1_all.deb

# Instalar via APT para resolver dependências (usuário decide)
# sudo apt install ./dist/cinnamon12-concept_0.1.0-1_all.deb

# Ativação SEM sudo
# cinnamon12ctl doctor
# cinnamon12ctl apply --profile light
```

**Build reproducível:** staging em diretório temporário, ownership/permissões corretos, nenhum arquivo fora de prefixos permitidos, `dpkg-deb --build`, opção lintian, checksums, versionamento, sem fazer downloads ocultos durante `postinst`. O agente deve entregar a instrução exata usada, testes e arquivo final.

### 9.5 Estratégia de atualização

Versão semântica do projeto (`MAJOR.MINOR.PATCH`), migrar settings próprios quando necessário, manter UUIDs estáveis, diferenciar atualização de assets de reconfiguração de usuário, deixar backup intacto, não sobrescrever customizações do usuário silenciosamente.

---

## 10. Critérios de qualidade, testes e performance

### 10.1 Matriz de teste obrigatória

| Cenário | Requisito |
|---|---|
| Ubuntu 24.04 + Cinnamon 6.0.4 | **Obrigatório** em ambiente real, VM ou ambiente de testes equivalente |
| X11 | Obrigatório |
| Wayland Cinnamon 6.0 | Apenas diagnóstico, sem garantia |
| 1366×768 | Menu, applets e quick settings sem corte |
| 1920×1080 | Visual fiel à referência |
| 2560×1440 | Sem imagens pixeladas e sem widgets minúsculos |
| 100%, 125%, 150% escala/fontes | Quando suportados pela sessão; controles legíveis |
| Claro/escuro | Todos os componentes funcionais |
| 1 e 2 monitores | Painel e widgets não “somem” |
| Mouse e teclado | Menus utilizáveis sem mouse, foco visível |
| Sem Wi-Fi/Bluetooth/backlight | Controls ocultos/desabilitados corretamente |
| Offline | Shell, menu, painel e monitor local continuam utilizáveis |
| Reiniciar sessão | Configurações persistem |
| `apply` 2× | Sem duplicação/efeitos colaterais |
| `restore` | Restitui configurações gerenciadas anteriores |
| Remover arquivos locais ou `.deb` | Sistema continua inicializando e desktop pode usar tema original |

### 10.2 Testes técnicos

- Syntax/parse de JSON, Python, Bash (`shellcheck` se disponível), CSS GTK/Cinnamon (validação no carregamento real, não somente linter web).
- Verificar sinal de errores nos logs do Cinnamon, GTK, applets e desklets.
- Instalar em home de teste e/ou VM; não testar alterações destrutivas primeiro no desktop principal.
- Exercitar applets com eventos: conectar/desconectar Wi-Fi, Bluetooth ausente, controle de volume externo, login/logout, reiniciar Cinnamon, trocar tema repetidamente.
- Testar com temas/ícones ausentes e dependências opcionais ausentes.
- Verificar timers, sinais, subprocessos e uso de memória em applets que abrem/fecham repetidas vezes.
- Monitorar CPU em idle: widgets de estatística não devem fazer polling excessivo ou manter wakeups desnecessários.
- Testar acentos/labels em português, string longa, fuso local, 12/24h e data variável.
- Garantir que o papel de parede, a localização do clima e o texto de terminal da imagem **não** sejam interpretados como valores reais.

### 10.3 Critérios de aceite visuais

1. Painel inferior moderno, predominantemente azul escuro translúcido, ícones na região central, cantos pouco arredondados.
2. Nemo com barra de título/cabeçalho azul claro, sidebar diferenciada e ícones de pastas modernos.
3. Seleções, inputs e botões uniformes em GTK3 e shell.
4. Popup de menu e quick settings com aparência coordenada com o painel.
5. Contraste e leitura melhores ou iguais ao tema atual em todas as áreas essenciais.
6. Sem artefatos de janelas, menus fora da tela ou ícones ilegíveis.
7. Comparar capturas com `referencia-visual.png` e registrar diferenças reais, em vez de declarar visual “100% igual”.
8. Desktop utilizável com **uma única janela aberta**: não depender da composição artificial com 5–6 janelas da imagem.
9. No MVP, todos os componentes implementados são reais e clicáveis; componentes futuros não devem aparecer como funcionalidades falsas.
10. Restauração do tema original em poucos comandos e sem reinstalar pacotes.

---

## 11. Fases de implementação e ordem das entregas

### Fase 0: reconhecimento e base segura

**Entregar:** `doctor`, inventário da instalação, auditoria de tema-base e assets, visão de arquitetura, plano de rollback. Sem alterar o desktop ainda.

**Pronto quando:** são conhecidos versão de Cinnamon, schemas suportados, estrutura real de tema, sessão e riscos específicos.

### Fase 1: MVP visual, sem applets próprios

**Entregar:** wallpaper original, temas Light/Dark para Cinnamon e GTK3, pacote de ícones mínimo, painel inferior ajustado **com recursos nativos**, script `install-local`, `activate`, `restore`, comparativos de screenshots.

**Pronto quando:** já parece muito mais moderno e funciona diariamente, mesmo usando menu de aplicativos e controle de rede/áudio padrões.

### Fase 2: launcher e widgets

**Entregar:** launcher moderno que funcione em Cinnamon 6.0.4, desklets opcionais (monitor/calendário/clima), configuração de preferências, automação segura de layout.

**Pronto quando:** o centro e a lateral da referência ficam representados por componentes nativos funcionais.

### Fase 3: quick settings e polimento

**Entregar:** quick settings integrado com backends reais, refinamentos de UI, acessibilidade, perfis de tema mais completos, testes multi-monitor/escala, documentação de limitações.

**Pronto quando:** uma pessoa consegue usar o ambiente sem depender de terminais para funções cotidianas.

### Fase 4: distribuição

**Entregar:** `.deb`, build reproducível, documentação de instalação e recuperação, `lintian` quando possível, testes de instalar/atualizar/desinstalar, changelog.

**Pronto quando:** é possível instalar com APT sem alterar preferências do usuário automaticamente, aplicar o tema sem sudo e voltar à aparência anterior com segurança.

**Recomendação de execução:** completar a Fase 1 de ponta a ponta **antes** de desenvolver o menu e a central de configurações rápidas. Não gastar todo o esforço em telas bonitas se falta um instalador reversível.

---

## 12. Checklist de tarefas para o agente (backlog técnico)

### Segurança / ferramentas

- [ ] Criar `doctor.sh` e relatório de compatibilidade com Cinnamon 6.0.4.
- [ ] Mapear schemas e chaves reais de tema, interface, painel e applets.
- [ ] Criar plano de backup/restauração e testes antes de qualquer `apply`.
- [ ] Implementar `--dry-run` e logs sem dados sensíveis.
- [ ] Criar testes básicos de scripts e idempotência.

### Design / base

- [ ] Recriar wallpaper original a partir da referência estética.
- [ ] Finalizar tokens de Light/Dark e biblioteca de SVGs.
- [ ] Implementar tema Cinnamon CSS com base 6.0.4 validada.
- [ ] Implementar tema GTK3 e validar Nemo.
- [ ] Implementar ícones, `index.theme` e heranças.
- [ ] Criar painel inferior e adaptar applets nativos.
- [ ] Implementar ativação/alternância e restauração.
- [ ] Capturar comparativo real contra `referencia-visual.png`.

### Funcionalidade avançada

- [ ] Implementar launcher, busca e fixados em CJS 6.0.4.
- [ ] Implementar menu de energia com chamadas seguras.
- [ ] Implementar desklet de calendário.
- [ ] Implementar desklet de uso de recursos.
- [ ] Implementar desklet de clima com opt-in e cache.
- [ ] Implementar quick settings com estados reais.
- [ ] Implementar adaptações a tela pequena, multi-monitor e scaling.
- [ ] Internacionalizar strings de todos os applets/desklets.

### Distribuição / documentação

- [ ] Criar `build-assets` e `build-deb`.
- [ ] Testar `apt install ./arquivo.deb` em VM.
- [ ] Testar update e remoção do pacote sem quebrar sessão.
- [ ] Registrar licenças e créditos de assets.
- [ ] Escrever README de instalação e manual de rollback.
- [ ] Entregar screenshots e evidências de testes reais.

---

## 13. Contrato de entrega de cada fase

Ao terminar cada fase, o agente deve responder com:

1. **O que foi de fato implementado** (arquivos, funções, componentes); separar do que ainda falta.
2. **Como testar** (comandos exatos e passos no Cinnamon 6.0.4).
3. **Como reverter** (comandos exatos, backup usado e escopo da restauração).
4. **Compatibilidade confirmada**: versão do Cinnamon, X11/Wayland, apps validados, resolução e tema.
5. **Capturas de tela reais** e, quando apropriado, comparação com `referencia-visual.png`.
6. **Problemas conhecidos e limitações**, incluindo diferenças irredutíveis da referência.
7. **Próximas tarefas priorizadas**, sem substituir testes por opinião.

Os scripts e pacotes da especificação **ainda precisam ser desenvolvidos**: jamais declarar que `install-local.sh`, `cinnamon12ctl` ou um `.deb` estão prontos apenas porque aparecem aqui.

---

## 14. Fontes técnicas relevantes (para leitura do agente)

Documentação/repositórios devem ser lidos **com foco na API e nos arquivos compatíveis com Cinnamon 6.0.4**, e não apenas na branch `master`, que muda ao longo do tempo:

- Ubuntu Cinnamon 24.04 LTS release notes (confirma Cinnamon 6.0.4): https://ubuntucinnamon.org/ubuntu-cinnamon-24-04-lts-noble-numbat-release-notes/
- Pacotes oficiais Ubuntu 24.04 (`cinnamon` e temas): https://packages.ubuntu.com/search?keywords=cinnamon&searchon=names&suite=noble
- Cinnamon (código-fonte oficial): https://github.com/linuxmint/cinnamon
- Tutorial oficial de applets (referência, validar versão): https://github.com/linuxmint/cinnamon/blob/master/docs/reference/cinnamon-tutorials/write-applet.xml
- Tutorial oficial de configurações de xlets: https://github.com/linuxmint/cinnamon/blob/master/docs/reference/cinnamon-tutorials/xlet-settings.xml
- Exemplo de `settings-schema.json`: https://github.com/linuxmint/cinnamon/blob/master/files/usr/share/cinnamon/applets/settings-example%40cinnamon.org/settings-schema.json
- Repositório de temas Cinnamon Spices: https://github.com/linuxmint/cinnamon-spices-themes
- Repositório de applets Cinnamon Spices: https://github.com/linuxmint/cinnamon-spices-applets
- Repositório de desklets Cinnamon Spices: https://github.com/linuxmint/cinnamon-spices-desklets
- GTK3 CSS overview: https://docs.gtk.org/gtk3/css-overview.html
- Especificação de ícones freedesktop: https://specifications.freedesktop.org/icon-theme-spec/latest/
- Política de nomes de ícones freedesktop: https://specifications.freedesktop.org/icon-naming-spec/latest/
- Debian Policy (pacotes): https://www.debian.org/doc/debian-policy/

**Atenção de versão:** o repositório `master` do Cinnamon pode conter APIs de 6.2, 6.4, 6.6 ou superiores. Para implementação, preferir um checkout/tag compatível com 6.0.x ou os arquivos realmente instalados no Ubuntu 24.04.

---

## 15. Prompt de início para Codex / agente executor

Copiar o texto abaixo na sessão do agente, anexando **este `.md` e `referencia-visual.png`**:

> Você é um engenheiro de desktop Linux experiente em Cinnamon 6.0.x, temas GTK3 e applets/desklets CJS. Sua tarefa é IMPLEMENTAR o projeto descrito em `SPEC-Cinnamon12-Ubuntu24.04-Cinnamon6.0.4.md`, usando `referencia-visual.png` como referência estética. O ambiente alvo é o Ubuntu 24.04 LTS já instalado, com Cinnamon 6.0.4, prioritariamente em X11. Não atualize Cinnamon/Ubuntu, não substitua o desktop e não modifique arquivos originais de pacotes. Comece pela Fase 0 e construa a Fase 1 utilizável: temas Light/Dark, wallpaper, ícones, painel com applets nativos, instalador local, backup, apply e restore. Inspecione os schemas e código da versão instalada antes de escrever ajustes. Priorize compatibilidade, instalação reversível e provas de teste. Não diga que algo foi implementado sem gerar os arquivos e testar. Depois proponha e implemente as próximas fases, separando componentes que exigem applets próprios. Gere opcionalmente um `.deb` apenas quando o projeto estiver funcional, sem aplicar configurações de usuário nos scripts root do pacote.

---

## 16. Definição de sucesso do projeto

O projeto está concluído quando um usuário de **Ubuntu 24.04 + Cinnamon 6.0.4** consegue instalar, ativar, usar e desativar este visual **sem reinstalar Linux ou Cinnamon**, com aparência claramente próxima da arte, interfaces reais e responsivas, menus e controles funcionais, respeito à privacidade, consumo aceitável de recursos, registro de eventuais diferenças visuais e restauração confiável do estado anterior.

**Prioridade absoluta:** primeiro um Cinnamon real, bonito e seguro; depois um conceito cada vez mais fiel à imagem.
