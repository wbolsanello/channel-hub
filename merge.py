import re, urllib.request

BASE = "https://raw.githubusercontent.com/Ramys/Iptv-Brasil-2026/master/"
FONTES = ["Canais.m3u8", "CanaisBR01.m3u8", "CanaisBR02.m3u8",
          "CanaisBR03.m3u8", "CanaisBR04.m3u8"]

# (nome final, trechos do grupo original, procurar também no nome do canal?)
GRUPOS = [
    ("🌾 | A Fazenda", ["FAZENDA"], True),
    ("🔴 | Notícias", ["NOTÍCIAS", "NOTICIAS"], False),
    ("📺 | TV Aberta", ["ABERT", "RECORD", "BAND", "REDETV"], False),
    ("🌎 | Documentários", ["DOCUMENTÁRIOS", "DOCUMENTARIOS", "DISCOVERY"], False),
    ("🎬 | Filmes e Séries", ["FILMES E SÉRIES", "FILMES E SERIES", "HBO", "CINE SKY"], False),
    ("⚽ | Esportes", ["ESPORTES", "ESPN", "PREMIERE", "LIBERTADORES", "PRIME VIDEO"], False),
    ("🧸 | Desenhos", ["DESENHOS", "INFANTIS"], False),
]

def ler(txt):
    atual, extras = None, []
    for linha in txt.splitlines():
        linha = linha.strip()
        if not linha:
            continue
        if linha.startswith("#EXTINF"):
            atual, extras = linha, []
        elif linha.startswith("#"):
            if atual:
                extras.append(linha)
        elif atual:
            yield atual, extras, linha
            atual, extras = None, []

def grupo_de(l):
    m = re.search(r'group-title="([^"]*)"', l)
    return m.group(1) if m else ""

def novo_grupo(l, nome):
    if 'group-title="' in l:
        return re.sub(r'group-title="[^"]*"', f'group-title="{nome}"', l, count=1)
    return re.sub(r'^(#EXTINF:\s*-?\d+)', rf'\1 group-title="{nome}"', l, count=1)

vistos, itens, contagem = set(), [], {}
for f in FONTES:
    try:
        txt = urllib.request.urlopen(BASE + f, timeout=30).read().decode("utf-8", "ignore")
    except Exception as e:
        print("Falhou:", f, e)
        continue
    for l, extras, url in ler(txt):
        g = grupo_de(l)
        nome = l.rsplit(",", 1)[-1]
        destino = None
        for i, (novo, trechos, tambem_nome) in enumerate(GRUPOS):
            alvo = (g + " " + nome if tambem_nome else g).upper()
            if any(t in alvo for t in trechos):
                destino = i
                break
        c = contagem.setdefault(g, [0, 0])
        c[0] += 1
        if destino is None or url in vistos:
            continue
        vistos.add(url)
        c[1] += 1
        itens.append((destino, novo_grupo(l, GRUPOS[destino][0]), extras, url))

itens.sort(key=lambda x: x[0])
saida = ["#EXTM3U"]
for _, l, extras, url in itens:
    saida += [l, *extras, url]

open("minha_lista.m3u8", "w", encoding="utf-8").write("\n".join(saida) + "\n")
open("grupos.txt", "w", encoding="utf-8").write(
    "\n".join(f"{g or '[sem grupo]'}: {a} de {t}" for g, (t, a) in sorted(contagem.items())))
