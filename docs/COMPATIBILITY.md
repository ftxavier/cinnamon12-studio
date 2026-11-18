# Compatibilidade e regras de segurança

**Plataforma-alvo**: Ubuntu 24.04 LTS (Noble), Cinnamon 6.0.4, preferencialmente X11. O gerador de assets foi executado fora desta sessão, portanto isto é um **alvo de projeto**, não um relatório de certificação.

## O que cada camada personaliza

- **Cinnamon shell**: CSS em `themes/Cinnamon12-{Light,Dark}/cinnamon/cinnamon.css` define painel, menu, popovers, notificações, calendário, OSD e classes `.c12-*` dos desklets. Não gera sozinho um novo layout de menu.
- **GTK3**: `gtk-3.0/gtk.css` define Nemo, cabeçalhos e aplicações que leem temas GTK3.
- **GTK4**: CSS experimental em `gtk-4.0/gtk.css` com esquema semelhante. Não é uma modificação forçada de libadwaita, que pode ignorar a aparência.
- **Ícones**: `icons/Cinnamon12-Icons/index.theme`, diretórios `scalable` e por tamanho. Herança Yaru, Adwaita, hicolor para nomes faltantes.
- **Wallpaper**: alteração opcional via GSettings somente após `apply`, com arquivo local.
- **Applets**: 2 protótipos em GJS. **Não substitua** o menu padrão antes de testá-los.
- **Desklets**: 2 protótipos GJS. Não consultam serviços externos.
- **Metacity/Muffin**: não substituídos; as bordas externas podem depender do gerenciador e cliente de janelas.

## Passos de teste numa máquina REAL

1. `cinnamon --version`; conferir versão 6.0.4 e sessão (`echo "$XDG_SESSION_TYPE"`).
2. `./cinnamon12 doctor` e `./cinnamon12 install` sem sudo; verificar pastas e `index.theme`.
3. Abrir Configurações → Temas, selecionar Cinnamon12 Light, Controles, Ícones; observar painel, menus, Nemo, caixas de diálogo.
4. `./cinnamon12 apply light`, reiniciar apps GTK3 já abertos se necessário.
5. Verificar 100%, 125%, 150% e 200% (se disponíveis), 1366×768, 1920×1080, dois monitores e variantes light/dark.
6. Abrir applets/desklets opcionais **um a um**, observando Looking Glass / journal local. Se houver crash, remover imediatamente o protótipo pela interface.
7. Alterar apenas o wallpaper manualmente, executar `./cinnamon12 restore` e confirmar que a alteração manual foi preservada e outras preferências foram restauradas.
8. Com tema original ativo, testar `./cinnamon12 uninstall`; confirmar ausência de alterações em painel, lista de applets, sistema de pacotes.
9. Testar o `.deb` em máquina virtual limpa primeiro; instale o pacote, ative via Configurações → Temas, remova via APT.
10. Em problemas de visualização, use um tema estável do sistema e reporte o elemento e captura de tela para ajuste dos seletores CSS.

## Comportamento seguro

- Não executar `sudo ./cinnamon12 apply` ou `sudo ./cinnamon12 install`.
- Não editar `/usr/share/cinnamon/theme/cinnamon.css` diretamente.
- Não sobrescrever `/etc`, `/usr/share/cinnamon/applets/*@cinnamon.org`, dconf completo ou preferência de painel.
- O `.deb` **não possui** `postinst`, `prerm` ou `postrm` para alterar usuário.
- Não exigir `xcursorgen` ou cursor pack adicional.
- Segurança visual: os ícones symbolic são simples e estáticos, estados exatos de wifi/bateria cabem aos applets reais.

## Escopo pendente para versão 1.0

- Menu próprio com layout 2 colunas e busca fluida sem limitações, acessibilidade e gerenciamento de favoritos.
- Quick settings com estados e ações reais via NetworkManager, Bluetooth, áudio e brilho, com permissões e acessibilidade.
- Translucidez do painel com geometria flutuante testada; Cinnamon não garante blur real.
- Implementação e documentação de sinalizações de brilho e energia em ambientes com diferentes backends.
- Tela de login/lockscreen opcional, testada sem alterar o login manager.
- Verificação de GTK 4/libadwaita, apps Flatpak e instalação de terceiros.
- Revisão de contraste e ajustes de escala/touch.

## Referências oficiais e padrões

- Cinnamon, tutorial oficial de applets: https://github.com/linuxmint/cinnamon/blob/master/docs/reference/cinnamon-tutorials/write-applet.xml
- Cinnamon, temas: https://github.com/linuxmint/cinnamon-spices-themes
- GSettings: https://docs.gtk.org/gio/class.Settings.html
- Freedesktop icon theme spec: https://specifications.freedesktop.org/icon-theme-spec/latest/
- XDG base directories: https://specifications.freedesktop.org/basedir-spec/latest/
- GTK3 CSS: https://docs.gtk.org/gtk3/css-overview.html

## Resultados de teste real (0.3.0, 2026-11-18)

Ambiente: Ubuntu 24.04.5 LTS, Cinnamon 6.0.4, X11, dois monitores (2560×1440 + 1920×1080).

| Verificação | Resultado |
|---|---|
| `@import url("/usr/share/cinnamon/theme/cinnamon.css")` no tema do shell | Funciona; sem erro de parse no log do Cinnamon |
| Margem no ator `#panel` (painel "flutuante") | **Ignorada** pelo Cinnamon 6.0; painel fica de borda a borda com filete superior |
| Barras de título SSD (Nemo etc.) | Desenhadas pelo Muffin com o CSS GTK3 (`headerbar.titlebar.default-decoration`); `metacity-1` não é usado |
| GTK3 / GTK4 CSS | 0 erros de parse (GtkCssProvider) nas duas variantes |
| Light e Dark | Nemo, menu nativo, calendário e painel conferidos por captura de tela |
| `apply` → `restore` e `panel apply` → `panel restore` | Valores idênticos ao snapshot anterior (tema, GTK, ícones, wallpaper, applets, altura) |
| `.deb` 0.3.0-1 | `dpkg-deb -I/-c` ok; lintian: 0 erros, 2 avisos (sem manpage; changelog sem bug) |
| Instalação/remoção via APT | **Pendente** (requer sudo do usuário) |

### Quick Settings (0.4.0-dev, mesmo ambiente)

| Controle | Backend | Teste |
|---|---|---|
| Wi-Fi | libnm (`WirelessEnabled`, conexão ativa) | Estado e nome da conexão exibidos corretamente. **Alternância não executada** (derrubaria a sessão de teste); permissão via NetworkManager/polkit |
| Bluetooth | BlueZ `Adapter1.Powered` | Estado exibido; `Set Powered` permitido ao usuário (verificado com `gdbus`). **Desligar não executado** (dispositivos do usuário) |
| Modo escuro | GSettings (tema shell + GTK + portal) | Alternado 3× pelo cartão; menu reabre; `restore` reverte |
| Não perturbe | `org.cinnamon.desktop.notifications display-notifications` | Alternado ida e volta |
| Volume | Cvc (sink padrão) | Mudança externa via `pactl` refletida no slider |
| Brilho | `org.cinnamon.SettingsDaemon.Power.Screen` | Mudança externa via D-Bus refletida no slider |
| Luz noturna | `org.cinnamon.settings-daemon.plugins.color night-light-enabled` | Chave inexistente no 6.0.4 → cartão oculto (correto) |
| Modo de energia | power-profiles-daemon | Serviço ausente → cartão oculto (correto) |
| Modo avião | NetworkManager + BlueZ | **Não executado** (derrubaria a sessão de teste) |
