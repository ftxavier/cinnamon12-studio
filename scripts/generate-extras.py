#!/usr/bin/env python3
"""Optional terminal colors and editor theme examples, never activated automatically."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
E=R/'extras'
series={
 'Dark':{'background':'#0b1c34','foreground':'#e8f4ff','cursor':'#5cd5ff',
         'normal':['#10223a','#ee6b8b','#3fceaa','#e9c06e','#51aaf5','#a698ff','#55cce9','#acc6e2'],
         'bright':['#476582','#ff8fa7','#70e6c4','#ffdf93','#82c7ff','#c3b7ff','#8ae6f3','#ffffff']},
 'Light':{'background':'#f1f8ff','foreground':'#203b5d','cursor':'#0c9ce9',
         'normal':['#1a395d','#cb486a','#188d73','#a8752a','#176eaf','#7555b6','#1b91a7','#587796'],
         'bright':['#476582','#ee6b8b','#21b898','#d29c3b','#388ee1','#a185eb','#36bad1','#102e4c']}
}
for variant,c in series.items():
 p=E/'terminal'/('cinnamon12-'+variant.lower());p.mkdir(exist_ok=True)
 (p/'kitty.conf').write_text('# Cinnamon12 Studio, optional. Use with include statement.\n'+'\n'.join([f'{k} {v}' for k,v in [('background',c['background']),('foreground',c['foreground']),('cursor',c['cursor'])]]+[f'color{i} {col}' for i,col in enumerate(c['normal']+c['bright'])])+'\n')
 (p/'alacritty.toml').write_text('[colors.primary]\n'+f'background = "{c["background"]}"\nforeground = "{c["foreground"]}"\n\n' + '[colors.cursor]\n' + f'cursor = "{c["cursor"]}"\ntext = "{c["background"]}"\n\n' + '[colors.normal]\n'+'\n'.join(f'{name} = "{co}"' for name,co in zip(['black','red','green','yellow','blue','magenta','cyan','white'],c['normal']))+'\n\n[colors.bright]\n'+'\n'.join(f'{name} = "{co}"' for name,co in zip(['black','red','green','yellow','blue','magenta','cyan','white'],c['bright']))+'\n')
 (p/'Xresources').write_text('! Cinnamon12 Studio colors; import manually.\n'+f'*.background: {c["background"]}\n*.foreground: {c["foreground"]}\n*.cursorColor: {c["cursor"]}\n'+''.join(f'*.color{i}: {co}\n' for i,co in enumerate(c['normal']+c['bright'])))

V=E/'vscode-theme';(V/'themes').mkdir(parents=True,exist_ok=True)
(V/'package.json').write_text(json.dumps({'name':'cinnamon12-color-themes','displayName':'Cinnamon12 Studio Themes','description':'Optional matching colors for VS Code','version':'0.2.0','publisher':'cinnamon12-studio-local','engines':{'vscode':'^1.80.0'},'categories':['Themes'],'contributes':{'themes':[{'label':f'Cinnamon12 {n}', 'uiTheme':'vs-dark' if n=='Dark' else 'vs','path':f'./themes/cinnamon12-{n.lower()}.json'} for n in ['Light','Dark']]}},indent=2)+'\n')
for n,c in series.items():
 dark=(n=='Dark');accent='#2baaff' if dark else '#078fe8';bg=c['background'];fg=c['foreground'];card='#1a3556' if dark else '#dfebfa'
 ui={'editor.background':bg,'editor.foreground':fg,'editorCursor.foreground':accent,
 'activityBar.background':card,'activityBar.foreground':fg,'sideBar.background':bg,
 'sideBar.foreground':fg,'sideBarTitle.foreground':accent,
 'statusBar.background':card,'statusBar.foreground':fg,'titleBar.activeBackground':card,
 'titleBar.activeForeground':fg,'tab.activeBackground':bg,'tab.activeForeground':fg,
 'editor.lineHighlightBackground':'#ffffff08' if dark else '#00000008',
 'editor.selectionBackground':'#3c7baa77','editorWhitespace.foreground':'#90adce55',
 'panel.background':bg,'terminal.background':bg,'terminal.foreground':fg,
 'terminalCursor.foreground':accent,'focusBorder':accent,'input.background':card,
 'input.foreground':fg,'button.background':accent,'button.foreground':'#ffffff'}
 syntax={'name':'Cinnamon12 '+n,'type':'dark' if dark else 'light','colors':ui,
 'tokenColors':[
  {'scope':['keyword','storage','storage.type'],'settings':{'foreground':'#9f8aff' if dark else '#7059c6'}},
  {'scope':['string','string.quoted'],'settings':{'foreground':'#57d6ae' if dark else '#148568'}},
  {'scope':['comment','punctuation.definition.comment'],'settings':{'foreground':'#6d93b4','fontStyle':'italic'}},
  {'scope':['entity.name.function','support.function'],'settings':{'foreground':'#6dccff' if dark else '#1179c9'}},
  {'scope':['constant.numeric'],'settings':{'foreground':'#f6bb67' if dark else '#b57c2c'}}]}
 (V/'themes'/f'cinnamon12-{n.lower()}.json').write_text(json.dumps(syntax,indent=2)+'\n')
print('Terminal palettes + two VS Code themes created')
