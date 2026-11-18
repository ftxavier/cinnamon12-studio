# Pedido de assets complementares — Cinnamon12 Studio

**Para:** agente de imagens
**Contexto:** auditoria feita em Ubuntu 24.04.5 + Cinnamon 6.0.4 (X11) real, em 2026-11-18.
**Regra geral:** os 202 ícones, os 3 wallpapers e `assets/ui` **estão aprovados e serão reaproveitados**. Este pedido lista **apenas nomes que não existem** em `icons/Cinnamon12-Icons/` e que o sistema ou o mockup realmente usam. Hoje, sem eles, o tema cai no fallback Yaru/Adwaita, o que mistura estilos.

## Formato de entrega (igual ao pacote atual)

- SVG em `scalable/<contexto>/<nome>.svg` + PNG em 16, 24, 32, 48 (symbolic) ou 16–128 (coloridos), gerados pelo mesmo `scripts/generate-assets.py`, para manter traço, gradientes e paleta (`design/tokens.json`).
- **Symbolic:** monocromático, cor `#bebebe`, traço igual aos `*-symbolic` existentes (ex.: `status/audio-volume-high-symbolic.svg`), para o GTK/St poderem recolorir.
- Atualizar `design/assets-manifest.json` e manter `scripts/validate.py` passando.
- Nada de logos de terceiros.

---

## P1 — Clima (necessário para o desklet de clima e o applet do painel)

**Evidência:** o mockup mostra ícones de clima coloridos no painel (canto inferior esquerdo) e no widget com previsão de 5 dias. No pacote existem só 3 symbolic (`weather-clear`, `weather-clear-night`, `weather-few-clouds`) e **nenhum colorido**.

```
--  weather-overcast            --  weather-overcast-symbolic
--  weather-showers             --  weather-showers-symbolic
--  weather-showers-scattered   --  weather-showers-scattered-symbolic
--  weather-snow                --  weather-snow-symbolic
--  weather-storm               --  weather-storm-symbolic
--  weather-fog                 --  weather-fog-symbolic
--  weather-few-clouds-night    --  weather-few-clouds-night-symbolic
--  weather-severe-alert        --  weather-severe-alert-symbolic
```

**Pedido:** versões **coloridas** (contexto `status`, 16–128 px) de: `weather-clear`, `weather-clear-night`, `weather-few-clouds`, `weather-few-clouds-night`, `weather-overcast`, `weather-showers`, `weather-showers-scattered`, `weather-snow`, `weather-storm`, `weather-fog`, `weather-severe-alert`. Também as **symbolic** que faltam (lista acima). Estilo: sol amarelo/laranja e nuvem branco-azulada, como no widget do mockup.

## P1 — Categorias do menu de aplicativos

**Evidência:** o Cinnamon pega o ícone das categorias do `Icon=` em `/usr/share/desktop-directories/*.directory`. Nenhum deles existe no tema:

```
--  applications-accessories   --  applications-development  --  applications-games
--  applications-graphics      --  applications-internet     --  applications-multimedia
--  applications-office        --  applications-other        --  applications-science
--  applications-system        --  applications-utilities    --  preferences-desktop-accessibility
--  preferences-desktop-peripherals  --  preferences-desktop-personal  --  preferences-other
```

O mockup (coluna esquerda do menu: Acessórios, Gráficos, Internet, Escritório, Som e Vídeo, Administração, Preferências, Locais) usa **ícones de linha monocromáticos**.

**Pedido:** os 15 nomes acima no contexto `apps` (coloridos, mesmo estilo dos `apps` atuais, para o menu nativo) **e** as versões `-symbolic` (para o menu novo do projeto, como no mockup).

## P2 — Symbolic do Nemo, da barra lateral e dos quick settings

**Evidência:** o binário do Nemo instalado referencia `folder-symbolic`, `folder-documents-symbolic`, `folder-download-symbolic`, `folder-music-symbolic`, `folder-pictures-symbolic`, `drive-harddisk-symbolic` etc. (`strings $(command -v nemo)`). A barra lateral do Nemo no mockup usa ícones de linha. Nenhum destes existe no tema:

```
Nemo/lateral: folder-symbolic folder-documents-symbolic folder-download-symbolic
              folder-music-symbolic folder-pictures-symbolic folder-videos-symbolic
              folder-publicshare-symbolic folder-templates-symbolic folder-open-symbolic
              folder-new-symbolic user-home-symbolic user-desktop-symbolic
              user-trash-symbolic user-trash-full-symbolic drive-harddisk-symbolic
              drive-removable-media-symbolic media-optical-symbolic computer-symbolic
              network-workgroup-symbolic starred-symbolic
Toolbar:      go-previous-symbolic go-next-symbolic go-up-symbolic pan-down-symbolic
              pan-end-symbolic view-grid-symbolic view-list-symbolic edit-find-symbolic
              open-menu-symbolic
Quick settings (mockup, painel direito):
              power-profile-balanced-symbolic power-profile-power-saver-symbolic
              power-profile-performance-symbolic video-display-symbolic
              applets-screenshooter-symbolic emblem-system-symbolic
              preferences-system-symbolic dark-mode-symbolic night-light-symbolic
```

## P3 — Ícones do Cinnamon Settings (opcional)

**Evidência:** `cinnamon-settings` usa ícones `cs-*` (35 nomes, ex.: `cs-themes`, `cs-backgrounds`, `cs-applets`, `cs-desklets`, `cs-extensions`, `cs-fonts`, `cs-desktop-effects`, `cs-panel`, `cs-sound`, `cs-network`, `cs-power`, `cs-display`, `cs-keyboard`, `cs-mouse`, `cs-user`, `cs-windows`, `cs-workspaces`, `cs-notifications`, `cs-privacy`, `cs-screensaver`, `cs-startup-programs`, `cs-date-time`, `cs-default-applications`, `cs-general`, `cs-gestures`, `cs-overview`, `cs-tiling`, `cs-universal-access`, `cs-details`, `cs-color`, `cs-tablet`, `cs-actions`, `cs-desktop`). O mockup mostra a janela de Configurações com esses ícones em linha monocromática. Sem eles, continuam os originais do Cinnamon, que funcionam bem. **Prioridade baixa.**

---

## O que NÃO precisa ser feito pelo agente de imagens

| Item | Motivo |
|---|---|
| Novos wallpapers | Os 3 atuais estão aprovados (só a seleção do que vai no `.deb` muda) |
| Redesenho dos 202 ícones | Aprovados |
| Botões da barra de título (`metacity-1`) | Gerados em código junto com o tema de janela |
| Checkbox, radio, toggle, setas do calendário e scroll do shell | São SVGs simples do `cinnamon.css` original; serão recoloridos por script com os tokens |
| Ícones de apps de terceiros (Chrome, LibreOffice, GIMP, AnyDesk etc.) | Marcas de terceiros: ficam com o ícone original do app |
