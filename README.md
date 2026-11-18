# Cinnamon12 Studio | v0.3.0

Tema conceitual **original**, inspirado por interfaces modernas de desktop, para **Ubuntu 24.04 LTS + Cinnamon 6.0.4**. Não tem relação com a Microsoft, nem é uma versão real de Windows. Ícones de aplicativos de terceiros **não** são copiados ou falsificados.

> **Status: BETA (assets + temas reais, extensões opcionais em protótipo).** Os SVG, PNG e wallpapers são artefatos prontos. Os arquivos CSS e o instalador passaram por testes estáticos e testes locais de empacotamento; **não** houve teste gráfico numa sessão real de Cinnamon 6.0.4. Alguns seletores exigirão pequenos ajustes após abrir no seu Ubuntu. Os applets/desklets são experimentais, não são ativados automaticamente e devem ser validados in situ. A imagem de referência é um mockup e nem todos os seus elementos já estão implementados.

## O que há neste pacote

| Componente | Conteúdo | Status |
|---|---|---|
| Ícones freedesktop | 202 nomes; SVG vetorial + PNGs de 16, 24, 32, 48, 64 e 128 px (symbolic até 48 px) | Gerado, verificar ícones dos apps específicos |
| Wallpapers originais | 3 designs; originais PNG, JPEG 1920×1080, 2560×1440, 3840×2160 | Prontos (4K é redimensionado do original gerado, não render nativo 4K) |
| Temas Cinnamon | `Cinnamon12-Light` e `Cinnamon12-Dark` em `cinnamon/cinnamon.css` | Base implementada, testar visualmente |
| Temas GTK | GTK3 e GTK4 CSS com paletas e variantes | GTK3 base pronta; GTK4 pode ser ignorado por libadwaita |
| Material UI | 11 SVGs de componentes + PNG 1x/2x | Recursos de apoio ao agente (não substituem controles funcionais) |
| Menu personalizado | Applet `c12-start@cinnamon12.local` com busca no inventário local | Protótipo, opt-in |
| Centro de atalhos | Applet `c12-quicklinks@cinnamon12.local`, abre configurações reais | Protótipo, **não** são toggles de Wi-Fi etc. |
| Desklets | Relógio local e medidor CPU/RAM lendo `/proc` | Protótipos, opt-in |
| Aparência do terminal | Exemplos Kitty, Alacritty e Xresources (claro/escuro) | Opcional, configuração manual |
| VS Code | Extensão local de tema de cores claro/escuro | Opcional, NÃO instalada automaticamente |
| Instalador | CLI Python, backup e restauração seletiva de GSettings | Implementado; verificar na máquina do usuário |
| `.deb` | Pacote passivo `cinnamon12-studio_0.3.0-1_all.deb` | Empacotado, sem mudar preferências automaticamente |
| Documentação | Spec original + instruções para agente e checklist de QA | Incluída |

## Instalação recomendada no seu Ubuntu (reversível, sem sudo)

Descompacte o **ZIP completo** em uma pasta. Execute no terminal dentro dela:

```bash
./cinnamon12 doctor
./cinnamon12 install
./cinnamon12 apply light
```

Ou ative a versão escura:

```bash
./cinnamon12 apply dark
```

**Painel no estilo da referência (opcional, 48 px, menu e janelas no centro, com backup):**

```bash
./cinnamon12 panel apply --dry-run   # mostra o que muda
./cinnamon12 panel apply
./cinnamon12 panel restore           # volta o painel exatamente como estava
```

**Para restaurar as preferências anteriores:**

```bash
./cinnamon12 restore
```

**Para remover o pacote local (os temas instalados por este script):**

```bash
./cinnamon12 uninstall
```

- O instalador **não precisa de `sudo`** e só escreve em sua pasta pessoal.
- `install` **não ativa nada**. Só `apply` muda GSettings (tema Cinnamon, GTK, ícones e wallpaper, se disponível).
- Na primeira ativação, grava o valor original de cada preferência em `~/.local/state/cinnamon12-studio/gsettings-original.json`.
- `restore` ignora preferências alteradas manualmente após `apply`; `restore --force` as reverte de qualquer modo.
- `install` não substitui diretórios existentes sem `--force`; forçando, o conteúdo anterior é arquivado no diretório de estado.
- O layout do painel, o menu original, as extensões existentes, os programas instalados e a sessão **não** são modificados pelo instalador.
- A transparência do painel não produz automaticamente desfoque real atrás das janelas.

## Alternativa `.deb`

O arquivo `cinnamon12-studio_0.3.0-1_all.deb` pode ser instalado via:

```bash
sudo apt install ./cinnamon12-studio_0.3.0-1_all.deb
```

Isso instala os recursos para todos os usuários em `/usr/share/...` e **não ativa** o tema. Ative em **Configurações do Sistema → Temas**, selecionando os itens Cinnamon, Controles/Aplicativos e Ícones. Você também pode executar `./cinnamon12 apply light` **a partir do ZIP extraído** após instalar o `.deb`.

Com o `.deb` instalado, cada usuário ativa sem sudo com `cinnamon12 apply light` (ou `dark`) e `cinnamon12 panel apply`.

Para remover o `.deb` (primeiro desfaça a ativação no seu usuário, depois remova):

```bash
cinnamon12 panel restore; cinnamon12 restore
sudo apt remove cinnamon12-studio
```

O pacote não tem scripts de instalação/remoção: ele nunca altera preferências de usuários. Se o tema ainda estiver ativo quando o pacote for removido, o Cinnamon e o GTK voltam aos temas padrão no próximo login.

**Não misture instalação local e `.deb` ao testar:** arquivos locais normalmente têm precedência. Prefira começar pelo ZIP e só depois instalar o pacote do sistema.

## Estrutura

```text
Cinnamon12-Studio/
├── themes/Cinnamon12-Light/          # Cinnamon CSS + GTK CSS
├── themes/Cinnamon12-Dark/
├── icons/Cinnamon12-Icons/            # 202 SVG + variações PNG + index.theme
├── assets/wallpapers/                # 3 fundos, 3 resoluções + originais
├── assets/ui/                        # componentes visuais SVG e PNG
├── assets/previews/                  # galerias e conceito aprovado
├── applets/                          # dois applets opcionais
├── desklets/                          # dois desklets opcionais
├── extras/terminal/                  # cores opcionais de terminal
├── extras/vscode-theme/              # tema opcional para VS Code
├── design/                            # tokens e inventário de ícones
├── docs/                              # compatibilidade, plano de QA e spec
├── scripts/                           # build, instalação e validação
├── cinnamon12                         # CLI local
└── dist/                               # .deb (entregue separadamente)
```

## Ativação manual sem script

- Tema do shell: **Cinnamon12-Light** ou **Cinnamon12-Dark**.
- Tema dos aplicativos/controles: mesma variante do shell.
- Ícones: **Cinnamon12 Icons**.
- Wallpaper: `~/.local/share/backgrounds/cinnamon12-studio/`.
- Posicione o painel embaixo, altura sugerida **48 px**; mantenha o menu e os applets atuais até testar os novos.
- Para centralizar aplicativos, experimente mover o applet de lista de janelas agrupadas para a área **central** do painel, no modo de edição do Cinnamon. Isso é manual e depende do painel existente.
- Adicione applets/desklets em **Configurações → Applets / Desklets**, apenas quando desejar testá-los; mantenha o menu original enquanto verifica o novo.

## Reconstrução a partir dos fontes

Com `python3`, Pillow e CairoSVG instalados para **desenvolvimento**:

```bash
python3 scripts/generate-assets.py
python3 scripts/prepare-wallpapers.py
python3 scripts/generate-ui-assets.py
python3 scripts/generate-themes.py
python3 scripts/generate-extras.py
python3 scripts/validate.py
python3 scripts/build-deb.py
```

Os scripts de geração **não** são necessários para usar os assets pré-compilados. `prepare-wallpapers.py` espera os três arquivos originais de geração de imagem nos caminhos citados dentro do script; esse script é para o ambiente de criação, não uma obrigação para instalação. Os PNG originais já estão em `assets/wallpapers`.

## Limitações importantes

1. Cinnamon 6.0.4 **não foi executado neste ambiente**; a validação visual e funcional deverá acontecer no seu Ubuntu.
2. Alguns ícones são genéricos, não substituem logos de apps como Firefox, Chrome, VS Code ou Spotify.
3. Nem todos os apps GTK4, Qt, Firefox ou Electron respeitam o tema GTK3.
4. Os protótipos de applets não equivalem ainda ao menu e painel de configurações rápidas completo do mockup.
5. O `.deb` **não** instala fonte Segoe, cursor proprietário, barra de tarefas estilo Windows 12 nem atualizações do sistema.

**Próxima tarefa para o agente:** leia `docs/AGENTE.md`, `docs/SPEC-original.md` e a imagem `assets/previews/conceito-original.png`. Instale em uma sessão de testes, inspecione logs de Looking Glass, corrija o CSS e aprimore os applets até alcançar o visual da imagem.
