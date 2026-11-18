# Tokens do Cinnamon12 Studio

**Estética:** conceito de desktop moderno com superfícies retangulares de cantos discretos, panel/OSD escuro azulado, janelas de vidro fosco simulado (sem blur real), destaque cyan e azul vivo. O projeto não replica a identidade Windows nem seus arquivos proprietários.

- **Light Blue:** superfícies `#edf5ff`, header `#e2efff`, sidebar `#d9eafa`, texto `#162e4d`, accent `#078fe8`, painel `rgba(13,39,76,0.89)`.
- **Dark Blue:** superfície `#17283e`, header `#1c334f`, texto `#e9f4ff`, accent `#2baaff`, painel `rgba(8,20,39,0.94)`.
- **Raios:** janelas 7 px, menus 8 px, botões 6 px, cartões 7 px. Evitar 'pill' em todos os componentes.
- **Painel:** altura sugerida 48 px. Compatibilizar com opções do Cinnamon antes de tentar simular uma dock separada da borda.
- **Cores específicas, dimensões e spacing:** `design/tokens.json`.
- **Tipografia:** Ubuntu ou Noto Sans já disponíveis no sistema; fonte monospace do usuário para terminal.
- **Ícones:** gradientes azul/cyan, áreas sólidas simplificadas para 16–32 px. Symbolic não são tiles; são traços monocromáticos.
- **Wallpapers:** `arctic` no tema claro, `midnight` no escuro, `aurora` como variante adicional.
- **Comportamento:** no mockup há menus e janelas simultâneos só para demonstrar, não deixar tudo fixo na tela.
