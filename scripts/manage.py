#!/usr/bin/env python3
"""Safe per-user Cinnamon12 installer and reversible GSettings activation.
Install != Apply.  No root required. Never edits Cinnamon's system files or panel layout.
"""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
VERSION='0.3.0'
HOME=Path.home()
STATE=Path(os.environ.get('XDG_STATE_HOME',HOME/'.local'/'state'))/'cinnamon12-studio'
USER_THEME=HOME/'.themes'
USER_ICON=HOME/'.local'/'share'/'icons'
USER_BG=HOME/'.local'/'share'/'backgrounds'/'cinnamon12-studio'
USER_APPLET=HOME/'.local'/'share'/'cinnamon'/'applets'
USER_DESKLET=HOME/'.local'/'share'/'cinnamon'/'desklets'
BACKUP=STATE/'gsettings-original.json'
MARK='.cinnamon12-studio-owned'


def command(args, check=False):
 try:
  p=subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=check)
  return (p.returncode,p.stdout.strip(),p.stderr.strip())
 except (OSError,subprocess.CalledProcessError) as e:
  return (1,'',str(e))

def die(message):raise SystemExit('ERRO: '+message)

def can(schema,key):
 code, out,_=command(['gsettings','list-keys',schema])
 return code == 0 and key in out.splitlines()

def value(schema,key):
 code,out,err=command(['gsettings','get',schema,key])
 if code:die('Não consegui ler '+schema+' '+key+': '+err)
 return out

def set_value(schema,key,v):
 code,out,err=command(['gsettings','set',schema,key,v])
 if code:die('Falha em '+schema+' '+key+': '+err)

def atomic_json(p, obj):
 p.parent.mkdir(parents=True,exist_ok=True)
 tmp=p.with_suffix('.tmp')
 tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 tmp.replace(p)

def targets():
 r=[]
 for name in ['Cinnamon12-Light','Cinnamon12-Dark']:
  r.append((ROOT/'themes'/name,USER_THEME/name))
 r.append((ROOT/'icons'/'Cinnamon12-Icons',USER_ICON/'Cinnamon12-Icons'))
 r.append((ROOT/'assets'/'wallpapers',USER_BG))
 for kind,dest in (('applets',USER_APPLET),('desklets',USER_DESKLET)):
  if (ROOT/kind).is_dir():
   for d in sorted((ROOT/kind).iterdir()):r.append((d,dest/d.name))
 return r

PANEL_BACKUP=STATE/'panel-original.json'
PANEL_KEYS=['enabled-applets','panels-height']
CENTER_UUIDS=['menu@cinnamon.org','c12-start@cinnamon12.local','grouped-window-list@cinnamon.org','panel-launchers@cinnamon.org']
DROP_UUIDS=['separator@cinnamon.org']

def wallpaper_size():
 """Smallest shipped wallpaper that covers the largest monitor."""
 rc,out,_=command(['xrandr','--listmonitors'])
 widest=1920
 if rc==0:
  import re
  for m in re.finditer(r'\s(\d+)/\d+x(\d+)/',out):widest=max(widest,int(m.group(1)))
 if widest>2560:return '3840x2160'
 if widest>1920:return '2560x1440'
 return '1920x1080'

def gvar_list(text):
 import ast
 text=text.strip()
 if text.startswith('@as '):text=text[4:]
 return list(ast.literal_eval(text))

def gvar_str(items):
 return '['+', '.join("'"+i.replace("'","\\'")+"'" for i in items)+']'

def panel_plan(applets,heights,height,launcher='native',quick=False):
 """Return new (applets, heights) for the 'balanced' profile, keeping instance ids."""
 rows=[a.split(':') for a in applets]
 if launcher=='cinnamon12':
  ids=[int(r[4]) for r in rows if len(r)>=5 and r[4].isdigit()]
  nxt=max(ids+[0])+1
  has=any(len(r)>=5 and r[3]=='c12-start@cinnamon12.local' for r in rows)
  swapped=[]
  for r in rows:
   if len(r)>=5 and r[3]=='menu@cinnamon.org':
    if not has:swapped.append([r[0],r[1],r[2],'c12-start@cinnamon12.local',str(nxt)]);has=True
    continue
   swapped.append(r)
  rows=swapped
 if quick and not any(len(r)>=5 and r[3]=='c12-quicksettings@cinnamon12.local' for r in rows):
  ids=[int(r[4]) for r in rows if len(r)>=5 and r[4].isdigit()]
  cal=[r for r in rows if len(r)>=5 and r[3]=='calendar@cinnamon.org']
  panel_id=cal[0][0] if cal else (rows[0][0] if rows else 'panel1')
  rights=[r for r in rows if len(r)>=5 and r[0]==panel_id and r[1]=='right']
  pos=int(cal[0][2]) if cal else len(rights)
  for r in rights:
   if r[2].isdigit() and int(r[2])>=pos:r[2]=str(int(r[2])+1)
  rows.append([panel_id,'right',str(pos),'c12-quicksettings@cinnamon12.local',str(max(ids+[0])+1)])
 out=[];center=[]
 for r in rows:
  if len(r)<5:out.append(r);continue
  panel,zone,order,uuid,inst=r[0],r[1],r[2],r[3],':'.join(r[4:])
  if uuid in DROP_UUIDS and zone!='center':continue
  if uuid in CENTER_UUIDS:center.append([panel,'center',order,uuid,inst]);continue
  out.append(r)
 # stable order inside the center zone: menu first, then launchers, then window list
 center.sort(key=lambda r:(r[0],CENTER_UUIDS.index(r[3]),int(r[2]) if r[2].isdigit() else 0))
 counters={}
 for r in center:
  counters[r[0]]=counters.get(r[0],-1)+1
  r[2]=str(counters[r[0]])
 new=[':'.join(r) for r in out+center]
 new_h=[h.split(':')[0]+':'+str(height) for h in heights]
 return new,new_h

def panel(args):
 schema='org.cinnamon'
 for k in PANEL_KEYS:
  if not can(schema,k):die('Chave '+schema+' '+k+' indisponível; perfil de painel não suportado aqui.')
 if args.panel_action=='restore':
  if not PANEL_BACKUP.is_file():
   print('Não há backup de painel. Nada a fazer.');return
  data=json.loads(PANEL_BACKUP.read_text())
  for k in PANEL_KEYS:
   cur=value(schema,k)
   if not args.force and data['applied'].get(k) is not None and cur!=data['applied'][k]:
    print('PULADO (painel alterado depois do perfil):',k,'  use --force');continue
   set_value(schema,k,data['original'][k]);print('Restaurado:',schema,k)
  PANEL_BACKUP.unlink();print('Painel restaurado.');return
 cur={k:value(schema,k) for k in PANEL_KEYS}
 applets,heights=gvar_list(cur['enabled-applets']),gvar_list(cur['panels-height'])
 new_a,new_h=panel_plan(applets,heights,args.height,args.launcher,args.quick_settings)
 plan={'enabled-applets':gvar_str(new_a),'panels-height':gvar_str(new_h)}
 print('Perfil de painel "balanced" (altura',args.height,'px, menu e janelas no centro):')
 for a in sorted(set(applets)-set(new_a)):print('  - ',a)
 for a in sorted(set(new_a)-set(applets)):print('  + ',a)
 print('  altura:',cur['panels-height'],'->',plan['panels-height'])
 if args.dry_run:print('(dry-run: nada foi alterado)');return
 if not PANEL_BACKUP.exists():
  atomic_json(PANEL_BACKUP,{'version':1,'created':time.strftime('%Y-%m-%dT%H:%M:%S'),'original':cur,'applied':{}})
  print('Backup do painel:',PANEL_BACKUP)
 data=json.loads(PANEL_BACKUP.read_text())
 for k in PANEL_KEYS:
  set_value(schema,k,plan[k]);data['applied'][k]=value(schema,k)
 atomic_json(PANEL_BACKUP,data)
 print('Painel aplicado. Para desfazer: ./cinnamon12 panel restore')

WIDGETS_BACKUP=STATE/'desklets-original.json'

def primary_monitor():
 rc,out,_=command(['xrandr','--listmonitors'])
 import re
 if rc==0:
  for line in out.splitlines():
   m=re.search(r'\+\*?\S+\s+(\d+)/\d+x(\d+)/\d+\+(-?\d+)\+(-?\d+)',line)
   if m and '*' in line:return tuple(int(v) for v in (m.group(3),m.group(4),m.group(1),m.group(2)))
 return (0,0,1920,1080)

def widgets(args):
 schema='org.cinnamon'
 keys=['enabled-desklets','next-desklet-id']
 for k in keys:
  if not can(schema,k):die('Chave '+schema+' '+k+' indisponível.')
 if args.widgets_action=='restore':
  if not WIDGETS_BACKUP.is_file():print('Não há backup de desklets. Nada a fazer.');return
  data=json.loads(WIDGETS_BACKUP.read_text())
  cur=value(schema,'enabled-desklets')
  if not args.force and data['applied'] is not None and cur!=data['applied']:
   print('PULADO: os desklets mudaram depois do perfil. Use --force.');return
  set_value(schema,'enabled-desklets',data['original']['enabled-desklets'])
  WIDGETS_BACKUP.unlink();print('Desklets restaurados.');return
 cur=value(schema,'enabled-desklets')
 items=gvar_list(cur)
 ids=[int(i.split(':')[1]) for i in items if len(i.split(':'))>=4 and i.split(':')[1].isdigit()]
 nxt=max(ids+[int(value(schema,'next-desklet-id').split()[-1])-1])+1
 wanted=(['c12-weather@cinnamon12.local'] if args.weather else [])+['c12-calendar@cinnamon12.local','c12-performance@cinnamon12.local']
 heights={'c12-weather@cinnamon12.local':215,'c12-calendar@cinnamon12.local':275,'c12-performance@cinnamon12.local':235}
 mx,my,mw,mh=primary_monitor()
 x,y=mx+20,my+20
 new=[i for i in items if i.split(':')[0] not in wanted]
 for uuid in wanted:
  new.append(f'{uuid}:{nxt}:{x}:{y}');nxt+=1;y+=heights[uuid]+14
 print('Desklets Cinnamon12 na coluna esquerda do monitor principal:')
 for i in new:
  if i not in items:print('  + ',i)
 for i in items:
  if i not in new:print('  - ',i)
 if args.dry_run:print('(dry-run: nada foi alterado)');return
 if not WIDGETS_BACKUP.exists():
  atomic_json(WIDGETS_BACKUP,{'version':1,'created':time.strftime('%Y-%m-%dT%H:%M:%S'),'original':{'enabled-desklets':cur},'applied':None})
  print('Backup dos desklets:',WIDGETS_BACKUP)
 set_value(schema,'enabled-desklets',gvar_str(new))
 set_value(schema,'next-desklet-id',str(nxt))
 data=json.loads(WIDGETS_BACKUP.read_text());data['applied']=value(schema,'enabled-desklets');atomic_json(WIDGETS_BACKUP,data)
 print('Pronto. Para desfazer: ./cinnamon12 widgets restore')

def doctor(args):
 print('Cinnamon12 Studio | diagnóstico somente leitura')
 for label,cmd in [('Sistema',['lsb_release','-ds']),('Cinnamon',['cinnamon','--version']),
                   ('Sessão',['printenv','XDG_SESSION_TYPE']),('GSettings',['gsettings','--version'])]:
  rc,out,err=command(cmd)
  print(f' {label:12s}: {out if rc==0 else (err or "não detectado")}')
 for schema,key in [('org.cinnamon.theme','name'),('org.cinnamon.desktop.interface','gtk-theme'),
                    ('org.cinnamon.desktop.interface','icon-theme'),('org.cinnamon.desktop.background','picture-uri')]:
  if can(schema,key):print(f' {schema}.{key}: {value(schema,key)}')
  else:print(f' {schema}.{key}: indisponível nesta sessão')
 for _,target in targets():print((' [ok] ' if target.exists() else ' [--] ')+str(target))
 print('Observação: o agente deve testar as partes interativas em Cinnamon 6.0.4 real.')

def install(args):
 if not (ROOT/'themes'/'Cinnamon12-Light'/'cinnamon'/'cinnamon.css').is_file():
  if Path('/usr/share/themes/Cinnamon12-Light').is_dir():
   print('Instalado pelo pacote .deb: os arquivos já estão em /usr/share. Use: cinnamon12 apply light');return
  die('Execute a partir do projeto completo, não só do script isolado.')
 for src,dst in targets():
  if not src.is_dir():die('Recurso ausente: '+str(src))
  if dst.exists():
   if not args.force:
    print('Já existe, mantido: '+str(dst)+'  (use --force para atualizar com cópia de segurança)')
    continue
   STATE.mkdir(parents=True,exist_ok=True)
   archive=STATE/'replaced-assets'/time.strftime('%Y%m%d-%H%M%S')/dst.name
   archive.parent.mkdir(parents=True,exist_ok=True)
   shutil.copytree(dst,archive,symlinks=True)
   shutil.rmtree(dst)
   print('Cópia de segurança de arquivos existente:',archive)
  dst.parent.mkdir(parents=True,exist_ok=True)
  shutil.copytree(src,dst)
  (dst/MARK).write_text('Installed by Cinnamon12 Studio local installer.\n')
  print('Instalado:',dst)
 print('Instalação concluída. Nenhuma configuração do usuário foi alterada.')
 print('Ative explicitamente: ./cinnamon12 apply light  (ou dark)')

def apply(args):
 name='Cinnamon12-'+args.variant.capitalize()
 if not ((USER_THEME/name).is_dir() or (Path('/usr/share/themes')/name).is_dir()):
  die(name+' não encontrado. Rode ./cinnamon12 install ou instale o .deb primeiro.')
 if not ((USER_ICON/'Cinnamon12-Icons').is_dir() or Path('/usr/share/icons/Cinnamon12-Icons').is_dir()):
  die('Tema de ícones não instalado.')
 settings=[('org.cinnamon.theme','name',name),
           ('org.cinnamon.desktop.interface','gtk-theme',name),
           ('org.cinnamon.desktop.interface','icon-theme','Cinnamon12-Icons'),
           ('org.x.apps.portal','color-scheme',"'prefer-dark'" if args.variant=='dark' else "'default'")]
 if not args.no_wallpaper:
  w={'light':'c12-arctic','dark':'c12-midnight'}[args.variant]+'-'+wallpaper_size()+'.jpg'
  p=USER_BG/w
  if not p.exists():p=Path('/usr/share/backgrounds/cinnamon12-studio')/w
  if p.exists():settings.append(('org.cinnamon.desktop.background','picture-uri',p.resolve().as_uri()))
  else:print('AVISO: wallpaper não encontrado; mantendo o existente')
 available=[(s,k,v) for s,k,v in settings if can(s,k)]
 if not available:die('GSettings do Cinnamon não encontrado. Rode na sessão do seu desktop.')
 if BACKUP.exists():
  backup=json.loads(BACKUP.read_text())
  print('Reutilizando backup original existente:',BACKUP)
 else:
  backup={'version':1,'created':time.strftime('%Y-%m-%dT%H:%M:%S'), 'entries':{}}
  for s,k,_ in available:
   key=s+'::'+k
   backup['entries'][key]={'schema':s,'key':k,'original':value(s,k),'applied':None}
  atomic_json(BACKUP,backup)
  print('Backup de preferências criado:',BACKUP)
 # If this operation touches a new key, preserve its original value first.
 for s,k,_ in available:
  key=s+'::'+k
  if key not in backup['entries']:
   backup['entries'][key]={'schema':s,'key':k,'original':value(s,k),'applied':None}
   atomic_json(BACKUP,backup)
 for s,k,v in available:
  set_value(s,k,v)
  backup['entries'][s+'::'+k]['applied']=value(s,k)
  atomic_json(BACKUP,backup)
  print('Aplicado:',s,k,'=',v)
 print('Pronto. Para restaurar: ./cinnamon12 restore')

def restore(args):
 if not BACKUP.is_file():
  print('Não há backup de preferências. Nenhuma alteração foi feita.')
  return
 data=json.loads(BACKUP.read_text()); remaining={};restored=0
 for key,row in data['entries'].items():
  s,k=row['schema'],row['key']
  if not can(s,k):
   print('AVISO: chave não existe, mantida no backup:',key)
   remaining[key]=row;continue
  current=value(s,k)
  ours=current.strip("'").startswith('Cinnamon12-') or (row['key']=='color-scheme' and current in ("'default'","'prefer-dark'"))
  if not args.force and row['applied'] is not None and current!=row['applied'] and not ours:
   print('PULADO (modificado manualmente depois):',key,'Atual:',current)
   remaining[key]=row;continue
  set_value(s,k,row['original'])
  print('Restaurado:',key)
  restored+=1
 if remaining:
  data['entries']=remaining
  atomic_json(BACKUP,data)
  print('Backup parcial preservado:',BACKUP)
 else:
  BACKUP.unlink()
 print(f'Restauração concluída: {restored} configuração(ões) revertida(s).')

def uninstall(args):
 if BACKUP.exists():restore(args)
 if PANEL_BACKUP.exists():
  args.panel_action='restore';panel(args)
 if WIDGETS_BACKUP.exists():
  args.widgets_action='restore';widgets(args)
 for src,dst in targets():
  if not dst.is_dir():continue
  if not (dst/MARK).exists():
   print('PULADO: não é uma instalação local marcada como Cinnamon12:',dst)
   continue
  if args.keep_files:
   print('Mantido a pedido:',dst)
   continue
  shutil.rmtree(dst)
  print('Removido:',dst)
 print('Desinstalação local concluída. Para o .deb use: sudo apt remove cinnamon12-studio')

def main():
 p=argparse.ArgumentParser(description='Cinnamon12 Studio | instalador local reversível')
 sub=p.add_subparsers(dest='action',required=True)
 sub.add_parser('doctor',help='inspeção, sem alterações')
 q=sub.add_parser('install',help='instala os arquivos do tema, sem ativar');q.add_argument('--force',action='store_true',help='substituir após salvar backup dos arquivos antigos')
 q=sub.add_parser('apply',help='faz backup das preferências antes de ativar');q.add_argument('variant',choices=['light','dark']);q.add_argument('--no-wallpaper',action='store_true')
 q=sub.add_parser('restore',help='restaura as preferências anteriores, preservando mudanças manuais');q.add_argument('--force',action='store_true',help='reverter até as preferências alteradas manualmente')
 q=sub.add_parser('uninstall',help='restaura preferências e remove apenas pastas que instalamos');q.add_argument('--force',action='store_true');q.add_argument('--keep-files',action='store_true')
 q=sub.add_parser('panel',help='perfil de painel 48 px centralizado, com backup');q.add_argument('panel_action',choices=['apply','restore']);q.add_argument('--height',type=int,default=48);q.add_argument('--launcher',choices=['native','cinnamon12'],default='native',help='cinnamon12 troca o menu nativo pelo Cinnamon12 Start');q.add_argument('--quick-settings',action='store_true',help='adiciona o Cinnamon12 Quick Settings antes do relógio');q.add_argument('--dry-run',action='store_true');q.add_argument('--force',action='store_true')
 q=sub.add_parser('widgets',help='desklets Cinnamon12 (calendário, monitor e, opcional, clima) na lateral esquerda, com backup');q.add_argument('widgets_action',choices=['apply','restore']);q.add_argument('--weather',action='store_true');q.add_argument('--dry-run',action='store_true');q.add_argument('--force',action='store_true')
 args=p.parse_args()
 {'doctor':doctor,'install':install,'apply':apply,'restore':restore,'uninstall':uninstall,'panel':panel,'widgets':widgets}[args.action](args)
if __name__=='__main__':main()
