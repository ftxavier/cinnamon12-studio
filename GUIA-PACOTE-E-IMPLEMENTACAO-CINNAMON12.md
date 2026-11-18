# Cinnamon12 Studio — inventário auditado, uso e roteiro de integração

**Documento de transferência para um agente de desenvolvimento**  
**Projeto:** Cinnamon12 Studio (v0.2.0, pacote beta)  
**Sistema de destino:** Ubuntu 24.04 LTS + Cinnamon **6.0.4** (instalação existente)  
**Referência:** `assets/previews/conceito-original.png`  
**Fonte analisada:** `Cinnamon12-Studio-completo.zip` e o `.deb` distribuído separadamente  
**Estado da auditoria:** estrutura extraída, inventário conferido e `scripts/validate.py` executado com sucesso; **não foi realizado teste gráfico em um Cinnamon 6.0.4 real**.

> **A instrução central ao agente é: APROVEITAR OS ASSETS JÁ CRIADOS.** Não há motivo para redesenhar os ícones, gerar novos wallpapers ou refazer a identidade visual do zero. **Mas** isso não transforma protótipos e CSS parciais em uma implementação final: as críticas técnicas abaixo são pertinentes. O trabalho restante é **integrar, completar, testar e empacotar corretamente** os componentes existentes.

---

## 1. Qual é o objetivo do projeto?

Aplicar ao Cinnamon 6.0.4 um conceito **original** de desktop futurista, inspirado em propostas de interfaces Windows 12, **sem depender do Windows nem de seus arquivos proprietários**:

- Painel inferior azul-escuro/translúcido, altura-alvo de **48 px**, com aplicativos agrupados e visual centralizado.
- Janelas em azul-gelo (tema claro) ou azul-petróleo (escuro), cabeçalhos consistentes e cantos **discretamente** arredondados (**4–8 px**).
- Ícones vetoriais modernos para pastas, dispositivos, menus e ações.
- Launcher/Start com pesquisa, categorias, favoritos e controles de sessão.
- Central de ajustes rápidos que mostre **estados reais** e execute ações reais.
- Desklets de relógio, calendário, clima (com consentimento), desempenho e rede.
- Duas variantes, Light e Dark, com alternância segura e restauração da configuração original.
- Instalação local reversível; distribuição `.deb` como opção, não pré-requisito.

O mockup é **objetivo visual**, não screenshot de componentes já implementados. **Não prometer transparência com blur real**: o Cinnamon pode renderizar translucidez, mas CSS isolado não fornece necessariamente desfoque do fundo.

## 2. O que existe de fato no ZIP

Os caminhos a seguir são **relativos à pasta raiz `Cinnamon12-Studio/`** após extração.

| Caminho | Conteúdo verificado | Estado real | Conduta do agente |
|---|---|---|---|
| `icons/Cinnamon12-Icons/` | `index.theme`, **202 SVGs**, **1.126 PNGs** em tamanhos diferentes | **Asset reutilizável**, com fallback Yaru/Adwaita/hicolor | **Preservar**, testar cobertura, ajustar nomes específicos conforme necessário |
| `assets/wallpapers/` | Três séries (`c12-arctic`, `c12-aurora`, `c12-midnight`), cada uma com PNG original + JPG 1920×1080, 2560×1440 e 3840×2160 | **Pronto para uso**; 4K é imagem redimensionada | **Reutilizar** e otimizar os arquivos para distribuição |
| `assets/ui/` | **11 SVGs** de superfícies/controles e **22 PNGs** (1x/2x) | **Materiais gráficos**, ainda sem vínculo com interface funcional | **Integrar se fizer sentido**; não confundir mockup gráfico com controle GTK/GJS |
| `assets/previews/` | `conceito-original.png`, galerias de ícones, wallpapers e vitrine | Referências visuais | Usar no QA; não incluir mockup no pacote público sem revisar direitos de uso |
| `design/tokens.json` | Cores, raios, sombras e medidas Light/Dark | **Base de design existente** | Preservar como fonte de verdade e estender sem quebrar consistência |
| `design/assets-manifest.json` | Contagem de ícones, categorias e tamanhos | Inventário gerado | Usar como referência, e não inventar ícones extras em relatórios |
| `themes/Cinnamon12-Light/` | Tema shell Cinnamon, GTK3 e GTK4, cada qual com CSS | **Incompleto** como tema de produção | Corrigir herança/base, cobertura de widgets e decoração |
| `themes/Cinnamon12-Dark/` | Mesmas camadas em cores escuras | **Incompleto** | Aplicar as mesmas correções, sem divergência funcional |
| `applets/c12-start@cinnamon12.local/` | `metadata.json` + `applet.js` | **Protótipo**, NÃO launcher final | Evoluir o applet; manter o menu nativo até validação |
| `applets/c12-quicklinks@cinnamon12.local/` | `metadata.json` + `applet.js` | **Lista de atalhos**, NÃO switches | Implementar estados e toggles reais depois de validação |
| `desklets/c12-clock@cinnamon12.local/` | Relógio/data em GJS | **Protótipo textual** | Preservar lógica, melhorar renderização, preferências e QA |
| `desklets/c12-performance@cinnamon12.local/` | Métricas CPU/RAM lidas de `/proc` | **Protótipo textual** | Evoluir para gráficos, disco/rede e controles de atualização |
| `extras/terminal/` | Paletas para Kitty, Alacritty e Xresources | Arquivos opcionais de configuração | Reutilizar; não alterar configurações pessoais automaticamente |
| `extras/vscode-theme/` | Light/Dark para VS Code | Arquivos opcionais | Reutilizar; não instalar como extensão global sem consentimento |
| `scripts/manage.py` + `cinnamon12` | CLI `doctor`, `install`, `apply`, `restore`, `uninstall` | Instalação local e rollback de **preferências selecionadas** | Auditar/testar; ampliar com backup de painel antes de implementar C04 |
| `scripts/generate-*.py` | Geradores de ícones, temas, UI, extras e mostruários | Código-fonte de geração disponível | **Não são necessários para consumir os arquivos gerados** |
| `scripts/prepare-wallpapers.py` | Preparação de resoluções dos wallpapers | Usa caminhos absolutos do ambiente de criação | Tornar portátil antes de qualquer novo build reproduzível |
| `scripts/build-deb.py` | Script de montagem de pacote Debian | **Protótipo de empacotamento** | Corrigir metadados, seleção de arquivos e conformidade de distribuição |
| `scripts/validate.py` | Verificações estáticas sobre assets e estrutura | Executou com sucesso na auditoria | Conservar e ampliar para verificar integrações e CSS |
| `docs/SPEC-original.md` | Spec maior, com fases e critérios de aceite | Requisito de produto | Ler antes de redesenhar arquitetura; atualizar estado de implementação |
| `docs/AGENTE.md` | Instruções anteriores ao agente | Guia útil, mas otimista em partes | Complementar por **este documento auditado** |
| `docs/COMPATIBILITY.md` | Cuidados com versões e rollback | Guia de segurança | Reutilizar e atualizar com testes reais |
| `README.md`, `LICENSE.md`, `CHANGELOG.md` | Uso, licenciamento/informações de proveniência e histórico | Documentação inicial | Atualizar para a release final |

**Detalhes verificados:** as categorias dos 202 SVGs são `apps` (53), `places` (26), `devices` (13), `mimetypes` (15), `actions` (52) e `status` (43). Os PNGs já estão rasterizados; instalar ou usar o tema **não requer CairoSVG**.

## 3. Problemas apontados pela outra IA: avaliação e ação correta

### P0. CSS de Cinnamon incompleto — **procedente, crítico**

- `themes/Cinnamon12-Light/cinnamon/cinnamon.css`: **125 linhas**.
- `themes/Cinnamon12-Dark/cinnamon/cinnamon.css`: **125 linhas**.
- Não há `@import` nem um CSS de base completo anexado ao tema.
- Isso não cobre com segurança todas as classes e estados do shell (switcher/Alt-Tab, Expo, overview, calendários, mensagens, menus de applets, diálogos, OSD e outros).

**Ação obrigatória:** sobrepor as regras Cinnamon12 a uma **base completa e compatível com a instalação alvo 6.0.4**. O agente deve inspecionar os arquivos e recursos presentes no **Ubuntu do usuário** e escolher, mediante testes, entre: importar uma base válida com caminho suportado pelo Cinnamon; ou derivar/empacotar uma base compatível, respeitando sua licença. Não assumir que um `@import` de caminho arbitrário funcionará só porque funciona em CSS de navegador. Preservar todos os seletores e estados essenciais; deixar os ajustes autorais de tokens no final. Não modificar `/usr/share/cinnamon/theme/cinnamon.css` do sistema.

### P0. GTK3 parcial e GTK4 copiado — **procedente, crítico**

- `gtk-3.0/gtk.css`: **123 linhas por variante**, sem importação de base.
- `gtk-4.0/gtk.css`: **idêntico byte a byte** ao GTK3 em ambas as variantes.

**Ação obrigatória:** basear GTK3 em CSS completo, compatível com GTK3 do Ubuntu 24.04, ou em importação **testada** do recurso Adwaita/tema-base correspondente, e sobrepor os tokens do Cinnamon12. Validar seletor por seletor. Para GTK4, criar CSS **específico para GTK4** e não apenas copiar GTK3. Apps libadwaita, Qt, Flatpak e Electron podem ignorar parte das regras: registrar limitações em vez de forçar hacks globais.

### P0/P1. Falta decoração de janela (`metacity-1`) — **procedente**

- O ZIP **não** contém `themes/Cinnamon12-{Light,Dark}/metacity-1/`.
- Portanto nem toda decoração gerenciada pelo Muffin seguirá o conceito; parte pode continuar Yaru.

**Ação:** implementar decoração de janela compatível, clara/escura, verificando em quais janelas o gerenciador desenha borda/título e em quais os próprios aplicativos usam CSD/headerbar GTK. A mesma imagem-base visual deve ser preservada, mas é normal precisar estilizar **ambas** as camadas. Testar Nemo, Terminal, Configurações e janelas com barra de título tradicional.

### P1. Layout do painel C04 não implementado — **procedente**

- Há CSS e `assets/ui/panel-light.svg`, mas **não existe perfil aplicável de painel** de 48 px e ícones centralizados.
- A CLI **não altera** applets nem painel. Isso foi intencional para evitar dano ao desktop existente, mas **não satisfaz o MVP visual da spec**.

**Ação:** criar um perfil opcional, com preview/dry-run e snapshot reversível de painel, applets, alturas e zonas (via chaves verificadas em Cinnamon 6.0.4). Testar em painel alternativo ou perfil de testes antes de aplicar no painel principal. Usar, sempre que suficiente, applets nativos como lista de janelas agrupadas; não construir um dock do zero sem necessidade.

### P1. Menu `c12-start` — **protótipo, não produto**

O código atual usa `Gio.AppInfo.get_all()` para listar programas, permite filtrar nomes em um submenu e fornece alguns atalhos. Não oferece ainda grid de fixados, categorias completas, integração com favoritos/uso recente, seleção acessível por teclado nem bloco de energia do conceito. O protótipo limita a lista a **65 aplicativos** por preenchimento. Não possui `settings-schema.json`.

**Ação:** desenvolver em cima da estrutura atual **apenas se ela passar no teste de API** do Cinnamon 6.0.4; caso contrário, substituir a implementação do applet, **não os assets**. Incluir opções configuráveis, favoritos, busca utilizável, ações de sessão e fallback para o menu nativo.

### P1. `c12-quicklinks` — **somente atalhos**

O código atual chama comandos `cinnamon-settings` para rede, Bluetooth, áudio, tela, energia e temas. **Não existe toggle nem leitura de estado** de Wi-Fi/BT/brilho etc. Não possui `settings-schema.json`.

**Ação:** preservar o protótipo como fallback. Implementar controles com leitura do estado real e integrações seguras/disponíveis no sistema (ex.: NetworkManager, interfaces de áudio e brilho); se um recurso não estiver disponível, desabilitar/ocultar o controle. Sem efeitos simulados.

### P1/P2. Desklets — **parciais**

- `c12-clock`: relógio e data em texto.
- `c12-performance`: CPU e RAM em texto, com leituras de `/proc`.
- Não há desklet funcional de clima, calendário visual, gráficos históricos, disco ou rede.

**Ação:** reutilizar leitura de métricas e classes `.c12-*`, renderizar cards reais, adicionar settings-schema e tratar timers ao remover desklets. Se houver clima, exigir escolha explícita de local/fonte e evitar acesso à localização automática sem permissão.

### P2. `.deb` e qualidade Debian — **parcialmente procedente**

**Esclarecimento importante:** o arquivo `.deb` **existe e foi gerado separadamente**, em `Cinnamon12-Studio/dist/cinnamon12-studio_0.2.0_all.deb` na entrega original, **mas não foi incluído no ZIP `Cinnamon12-Studio-completo.zip`**. O ZIP tem `scripts/build-deb.py`, que pode recriá-lo.

O arquivo `.deb` separado foi inspecionado com `dpkg-deb -I` e contém `Package: cinnamon12-studio`, `Version: 0.2.0`, `Architecture: all` e `Depends: cinnamon (>= 6.0)`. **Isso prova integridade básica do formato, não aprovação para publicação nem testes de instalação em Cinnamon real**.

Pendências reais:

- `Maintainer: Cinnamon12 Studio Contributors <noreply@example.invalid>` é placeholder e deve ser substituído antes da publicação.
- A versão `0.2.0` é aceita como sintaxe de versão Debian, mas o agente deve escolher conscientemente o esquema de release (por exemplo, `0.2.0-1` se fizer empacotamento não nativo).
- `LICENSE.md` e `CHANGELOG.md` existem no projeto; o build atualmente copia `README.md`, `LICENSE.md` e `COMPATIBILITY.md` para `/usr/share/doc`, **não copia o changelog** nem cria os arquivos padronizados de copyright/changelog Debian.
- O build inclui os PNGs originais e JPGs 4K dos três wallpapers. Criar perfil de empacotamento enxuto sem remover os masters do **repositório de desenvolvimento**.
- Executar `lintian` e resolver alertas pertinentes; ainda não há evidência de `lintian` concluído.
- O pacote deve continuar **passivo**, sem `postinst` que altere tema ou preferências de usuários.

### P2. Scripts e assets UI não integrados — **procedente**

- Os 11 SVGs e 22 PNGs de `assets/ui` são referências visuais utilizáveis, **não componentes GJS automaticamente ativos**.
- Geradores usam Python/Pillow/CairoSVG conforme a tarefa. Isso **não é dependência de instalação do tema pronto**.
- `scripts/prepare-wallpapers.py` contém entradas absolutas como `/mnt/data/a_clean_high_resolution_abstract_wallpaper_in_the.png`. Em outra máquina, não são portáteis.
- `assets/wallpapers` já contém os resultados, portanto os wallpapers **não precisam ser recriados**. Ajustar o script para ler os masters relativos ao projeto caso regeneração seja realmente necessária.

---

## 4. Instruções para o agente: o que preservar e o que implementar

### NÃO recriar desnecessariamente

1. Ícones em SVG e PNG existentes; `index.theme` e estrutura freedesktop.
2. Os três wallpapers em todas as resoluções já entregues.
3. Design tokens (`design/tokens.json`) e conceito de cores/medidas.
4. `assets/ui` como biblioteca de referência, com uso seletivo.
5. Scripts de instalação/backup como ponto de partida.
6. Protótipos de applets/desklets quando o código for aproveitável.
7. Extras de terminal e VS Code.

### Implementar, reparar ou testar de verdade

1. **Base completa Cinnamon 6.0.4 + overrides** para duas variantes, testada no shell.
2. **Base GTK3 completa + overrides**; GTK4 corretamente separado.
3. **Decoração `metacity-1`/Muffin** e coerência com CSD GTK.
4. **Perfil aplicável e reversível do painel**, sem mexer no layout nativo sem confirmação.
5. Launcher com busca real, grid de fixados, categorias e sessão.
6. Central de ajustes rápidos com estados e toggles reais, quando suportados.
7. Desklets gráficos e configurações, incluindo calendário e clima opcional.
8. Testes, empacotamento reprodutível, documentação e `.deb` de qualidade.

**Evite “refazer tudo”**: o pacote atual é uma **biblioteca de recursos + implementação parcial**, não uma versão 1.0 pronta. Consertar CSS e construir interfaces é trabalho legítimo e necessário; produzir novamente 202 ícones e 3 wallpapers, sem motivo funcional claro, é desperdício.

## 5. Como abrir, inspecionar e usar o pacote agora

### 5.1 Extrair e inspecionar, sem alterar nada no desktop

```bash
unzip Cinnamon12-Studio-completo.zip
cd Cinnamon12-Studio

# Inspeção da máquina e chaves disponíveis, sem alterações
./cinnamon12 doctor

# Verificação estática do material
python3 scripts/validate.py

# Listagens importantes
ls -la themes/ icons/Cinnamon12-Icons/ assets/wallpapers/ assets/ui/
cat design/tokens.json
```

Se a extração criar pasta com nome diferente, entre na pasta onde está o executável `cinnamon12`.

### 5.2 Instalação local dos arquivos, sem ativar (após conferência)

```bash
./cinnamon12 install
```

O comando copia temas para `~/.themes/`, ícones para `~/.local/share/icons/`, fundos para `~/.local/share/backgrounds/cinnamon12-studio/` e componentes experimentais para `~/.local/share/cinnamon/{applets,desklets}/`.

**Recomendação nesta versão:** experimentar **primeiro apenas os ícones e o wallpaper** pelo painel gráfico de Temas/Planos de Fundo, mantendo um tema Cinnamon/GTK estável. **Não ativar o `cinnamon.css` incompleto como tema principal em uma sessão de trabalho importante.** Para desenvolver e testar os CSS incompletos, usar uma conta de teste, sessão recuperável ou VM.

### 5.3 Comandos de ativação e reversão existentes (apenas após corrigir P0)

```bash
# Somente quando o agente já tiver validado a cobertura do CSS:
./cinnamon12 apply light
./cinnamon12 apply dark

# Restaura as chaves que a CLI gravou antes de aplicar
./cinnamon12 restore

# Remove arquivos instalados localmente e tenta restaurar as preferências
./cinnamon12 uninstall
```

O `apply` tenta alterar apenas tema do Cinnamon, tema GTK, ícones e wallpaper através de GSettings, se as chaves existirem. Grava valores anteriores em `~/.local/state/cinnamon12-studio/gsettings-original.json`. **Não faz backup do layout do painel** porque não o altera. Se o agente implementar perfil de painel, deve criar um backup adicional, explícito e testado. Não executar `sudo ./cinnamon12 ...`.

### 5.4 Se você também recebeu o `.deb` separado

```bash
# Só depois de revisar/testar uma versão corrigida:
dpkg-deb --info cinnamon12-studio_0.2.0_all.deb
dpkg-deb --contents cinnamon12-studio_0.2.0_all.deb
# Instalação futura, após QA:
# sudo apt install ./cinnamon12-studio_0.2.0_all.deb
```

`dpkg-deb --info` só inspeciona; `apt install` altera o sistema. **Não misturar install local e `.deb` durante QA**, pois as cópias do tema do usuário podem ter precedência sobre `/usr/share`.

### 5.5 Geradores: quando usar

- **Usar os arquivos pré-gerados** é suficiente para instalar/revisar os assets.
- Só rodar `scripts/generate-assets.py` se precisar editar/recriar SVG/PNG; nesse caso, provisionar Pillow e CairoSVG no ambiente de desenvolvimento.
- Só rodar `scripts/prepare-wallpapers.py` depois de corrigir os caminhos absolutos e definir entradas relativas ao projeto.
- Atualizar `scripts/generate-themes.py` com as mudanças de CSS; não editar só CSS gerado para depois perdê-lo na próxima execução.
- Para gerar `.deb` depois de corrigir o empacotador, usar `python3 scripts/build-deb.py` num ambiente com `dpkg-deb`.

## 6. Ordem de execução sugerida (com critérios de aceite)

| Fase | Entrega obrigatória | Aceite verificável |
|---|---|---|
| **0. Inventário** | Conferir versão 6.0.4, session type, caminhos e recursos já gerados | Relatório sem alegações de teste inexistente, comparação visual e snapshot de preferências |
| **1. CSS Shell** | Base completa + overrides Light/Dark | Menu e applets nativos, OSD, notificações, Alt-Tab, Expo/overview e calendário legíveis |
| **2. GTK e janela** | GTK3 completo, GTK4 independente, decoração de janela | Nemo, diálogos, preferências e janelas com SSD/CSD coerentes; sem visual cru |
| **3. Ícones + fundo** | Ajustar `index.theme`/nomes e aplicar assets existentes | Pastas e dispositivos no Nemo; 100% e 200%; wallpapers sem distorção |
| **4. Painel C04** | Perfil 48 px com centralização e rollback | Aplicar/restaurar sem perder applets; testar 1366×768 e Full HD |
| **5. Launcher** | Menu moderno com favoritos, categorias, busca, energia | Teclado e mouse, desempenho, atalhos, sem quebrar menu nativo |
| **6. Quick settings** | Controles com estados reais | Wi-Fi/BT/volume/brilho quando disponíveis, erros/ausência tratados |
| **7. Desklets** | Calendário, relógio, CPU/RAM, disco/rede, clima opcional | Fontes reais, atualizações corretas, limpeza de timers, preferência por usuário |
| **8. Distribuição** | `.deb` mínimo + docs + teste de remoção | `dpkg-deb`, `lintian`, VM/teste real, não alterar tema automaticamente |

Ao final de cada fase: capturar evidência visual do Cinnamon 6.0.4 real, registrar arquivos alterados, testes, limitações e como desfazer a fase. **Não declarar “funciona” apenas porque um script validou sintaxe/estrutura.**

## 7. Checklist para revisão do produto

- [ ] A biblioteca de ícones existente é reaproveitada; os SVGs permanecem como fonte e os PNGs não são perdidos.
- [ ] Há fallback correto para ícones desconhecidos (Yaru/Adwaita/hicolor).
- [ ] Os wallpapers existentes continuam disponíveis nas 3 variantes e resoluções.
- [ ] Todos os elementos essenciais de Cinnamon 6.0.4 recebem estilo mesmo fora dos elementos do mockup.
- [ ] GTK3 base, GTK4 e decoração de janela são tratados como camadas diferentes.
- [ ] Light/Dark têm contraste, foco, hover, ativo, desabilitado e dimensões testados.
- [ ] Nenhum applet substitui menu/painel padrão sem aprovação e mecanismo de restauração.
- [ ] O layout do painel pode ser reproduzido e desfeito com segurança.
- [ ] Applets/desklets possuem metadados e `settings-schema.json` **quando configurações persistentes forem implementadas**.
- [ ] Controles de rede/áudio/brilho refletem o estado real, sem botões cenográficos.
- [ ] Scripts de build não dependem de caminhos `/mnt/data/` do autor.
- [ ] O `.deb` final não inclui masters enormes desnecessários, mas o repositório-fonte mantém esses masters.
- [ ] Há revisão de empacotamento, licenças, changelog, testes e documentação atualizada.
- [ ] Testado em Ubuntu 24.04/Cinnamon 6.0.4, incluindo restauração após falha.

---

## 8. Prompt curto para colar em um agente

> Trabalhe sobre o projeto **Cinnamon12 Studio** que está neste ZIP, mirando exclusivamente **Ubuntu 24.04 LTS + Cinnamon 6.0.4**. Leia `docs/SPEC-original.md`, `docs/AGENTE.md`, `design/tokens.json` e o arquivo **`GUIA-PACOTE-E-IMPLEMENTACAO-CINNAMON12.md`**. A biblioteca de assets **já existe**: 202 SVGs, 1.126 PNGs, 3 wallpapers completos, 11 SVGs e 22 PNGs de UI, tokens de design, extras e scripts. **Não recrie ícones/wallpapers/identidade visual sem necessidade**. Corrija primeiro as falhas reais: CSS do Cinnamon e GTK3 incompletos, GTK4 copiado, falta de decoração metacity/Muffin e falta de perfil de painel. Em seguida evolua launcher, quick settings e desklets sem trocar o menu original automaticamente. Use versões reais e estados reais, inclua backup/rollback, mantenha os scripts de geração coerentes, crie um `.deb` adequado e teste tudo numa sessão Cinnamon 6.0.4. Antes de qualquer mudança invasiva, explique o plano e preserve o ambiente existente. Sempre distinga **asset pronto**, **protótipo**, **funcional validado** e **pendente**.

## 9. Notas de procedência da auditoria

Este documento foi elaborado pela inspeção direta do ZIP do projeto, da árvore descompactada, dos scripts e do `.deb` separado da entrega anterior. Confirmado nesta auditoria:

- Arquivo ZIP passou em `unzip -t` (nenhum erro de integridade).
- `scripts/validate.py` completou com `Static validation passed`.
- Quantidades verificadas: **202 SVG**, **1.126 PNG**, **3 conjuntos de wallpaper**, **11 SVG UI**, **22 PNG UI**.
- `cinnamon.css`: **125 linhas/variante**; `gtk.css`: **123 linhas/variante**; GTK4 idêntico ao GTK3.
- `metacity-1` e `dist/` **ausentes do ZIP**; `.deb` efetivamente existe **em arquivo separado**.
- `dpkg-deb --info` conseguiu inspecionar o `.deb` anterior.
- **Não foram testados** renderização, estabilidade, atalhos, applets, compatibilidade com Cinnamon 6.0.4 nem instalação/remoção no Ubuntu real.

**Conclusão:** a outra IA está certa em apontar lacunas de engenharia. Ela **não** precisa refazer o pacote de assets; precisa **transformar o material existente em um tema completo, seguro e utilizável**.
