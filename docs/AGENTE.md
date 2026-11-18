# Instruções para o agente executor

Você recebeu os recursos **Cinnamon12 Studio** criados para um usuário com **Ubuntu 24.04 LTS + Cinnamon 6.0.4**. Referência visual principal: `assets/previews/conceito-original.png`. Especificação completa de produto: `docs/SPEC-original.md`. Este ZIP não é uma implementação pixel-perfect do conceito; já contém componentes reais para evitar que você precise desenhar o projeto do zero.

## Inventário técnico

1. `design/tokens.json`: fonte única de cores e raios.
2. `scripts/generate-themes.py`: CSS do Cinnamon e GTK, claro e escuro; compile sem CSS variables JS/browser.
3. `icons/Cinnamon12-Icons`: **202 nomes** de ícones e seus PNG/SVG em layout freedesktop, com `index.theme` e herança Yaru, Adwaita e hicolor.
4. `scripts/generate-assets.py`: fontes vetoriais geradas por caminhos SVG editáveis no próprio script.
5. `assets/wallpapers`: três papéis de parede originais, mais 3 resoluções JPEG por variante.
6. `assets/ui`: 11 elementos de interface SVG e raster, para uso nos menus, widgets e materiais gráficos.
7. `themes/Cinnamon12-{Light,Dark}`: temas de sistema prontos para copiar na home.
8. `applets` e `desklets`: protótipos funcionais a validar num Cinnamon 6.0.4 real.
9. `scripts/manage.py`: CLI de instalação e ativação com backup seletivo e rollback.
10. `scripts/build-deb.py`: pacotização passiva de `/usr/share/themes`, `/usr/share/icons`, `backgrounds`, Cinnamon apple(t|desk)lets.

## Sequência de engenharia recomendada

**Fase A: validação do CSS**. Entre na sessão real do usuário/VM: `./cinnamon12 doctor; ./cinnamon12 install; ./cinnamon12 apply light`. Capturar Nemo, menu, painel, tooltips, calendário, diálogos, notifications e bug reports. Corrigir seletores não suportados sem remover o fallback ao tema do sistema. Compare com a referência. Repetir variante dark.

**Fase B: ícones**. Revisar no Nemo nomes de pastas, miniaturas, ações e symbolic. A camada de ícones **não deve** sobrescrever marcas genuínas Firefox, VS Code etc.; completar os nomes freedesktop úteis que faltarem com arte original. Testar fallback de ícones e escala 200%.

**Fase C: menu**. Inspecionar o protótipo `c12-start@cinnamon12.local`. Validar `Applet.AppletPopupMenu`, `PopupMenu.PopupSubMenuMenuItem`, busca e seleção por teclado; corrigir funções incompatíveis. Evoluir para layout central de duas colunas, categorias, fixados, recentes e busca acessível. Não desabilitar o menu original por default.

**Fase D: quick settings**. Inspecionar `c12-quicklinks@cinnamon12.local`, que só abre configurações reais. Migrar a aparência para cartões claros/escuros (`assets/ui`) e, somente com integração real validada, acrescentar switches Wi-Fi/BT, áudio, brilho e modo escuro. Não representar valores fictícios. Tratar permissões e erros.

**Fase E: desklets**. Testar relógio e CPU/RAM sob atualização periódica, monitorar erros. Implementar calendário e meteorologia apenas com consentimento de rede. Posicionamento livre; sem sobreposições em tela 1366×768.

**Fase F: distribuição**. Confirmar `.deb` via `dpkg-deb --info` e `--contents`, instalar e remover em VM. O pacote deve ser passivo, sem scripts root executando `gsettings`. Atualizar README e imagens reais, não apenas mockup.

## Aceitação

- O usuário consegue instalar, ativar, alternar claro/escuro e restaurar **sem quebrar sua sessão**.
- O Cinnamon original permanece instalado. Os applets existentes não são desabilitados.
- Os elementos reais têm visual próximo da referência, **cantos 4–8 px**, paleta azul/cyan, painel escuro e janelas claras na variante Light.
- Menu/atalhos/desklets só prometem o que fazem. Falhas não impedem abrir o menu original.
- A lista de ícones é derivada do `design/assets-manifest.json`, não inventada em relatório.
- Caso não tenha acesso a Cinnamon 6.0.4 real, registrar **'não validado'**. Não declarar compatibilidade comprovada sem execução.

## Restrições importantes

- Evite comandos destrutivos, configurações do desktop como root e alterações globais irreversíveis.
- Não copie logos ou CSS proprietários de conceitos Windows. Use os assets originais deste projeto.
- Não faça geolocalização ou consultas de clima sem opt-in.
- Não invente que o desfoque de fundo (background blur) é suportado por CSS do Cinnamon.
- Não crie um `postinst` que altere a aparência de todos os usuários.
