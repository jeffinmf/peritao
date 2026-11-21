#!/usr/bin/env python3
"""Preenche o modelo oficial da escala de plantão do 1º NRPC Araguatins.

Uso:  python3 -I gerar_escala.py modelo.docx dados.json saida.docx

O modelo é o arquivo .docx do próprio núcleo — é dele que vêm o timbre, as
margens e as fontes. Este script só troca o conteúdo: o mês, a grade de dias,
as duas tabelas de horas, as observações e os nomes das assinaturas.
"""
import json
import sys
from calendar import monthrange
from datetime import date

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor

MESES = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
         'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
CURTO = {'24h': '', '12h': ' (12h)', '12h_noturno': ' (12h*)'}


def escreve(celula, linhas, *, negrito=False, centro=True, tamanho=10):
    """Troca o conteúdo da célula, uma linha por parágrafo, mantendo o estilo."""
    celula.text = ''
    primeiro = celula.paragraphs[0]
    for i, texto in enumerate(linhas or ['']):
        p = primeiro if i == 0 else celula.add_paragraph()
        if centro:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(texto)
        r.font.name = 'Arial'
        r.font.size = Pt(tamanho)
        r.font.bold = negrito
        r.font.color.rgb = RGBColor(0, 0, 0)


def troca_paragrafo(par, texto):
    """Troca o texto de um parágrafo preservando o estilo do primeiro run."""
    if not par.runs:
        par.add_run(texto)
        return
    par.runs[0].text = texto
    for r in par.runs[1:]:
        r.text = ''


def main(caminho_modelo, caminho_dados, caminho_saida):
    dados = json.load(open(caminho_dados, encoding='utf-8'))
    ano, mes = int(dados['ano']), int(dados['mes'])
    doc = Document(caminho_modelo)

    rotulo = MESES[mes - 1].capitalize() + '/' + str(ano)

    # ---- cabeçalho: mês e horários ----
    alvos = {
        'mes': rotulo,
        'turno_24h': 'Horário de início e de término de cada plantão: ' + dados['turno_24h'],
        'turno_12h': 'Horário de início e de término de cada plantão (12h): ' + dados['turno_12h'],
        'turno_12h_noturno': 'Horário de início e de término de cada plantão (12h*): ' + dados['turno_12h_noturno'],
    }
    for p in doc.paragraphs:
        t = p.text.strip()
        if any(t == MESES[m].capitalize() + '/' + str(a)
               for m in range(12) for a in range(2020, 2040)):
            troca_paragrafo(p, alvos['mes'])
        elif t.startswith('Horário de início') and '(12h)' in t:
            troca_paragrafo(p, alvos['turno_12h'])
        elif t.startswith('Horário de início') and '(12h*)' in t:
            troca_paragrafo(p, alvos['turno_12h_noturno'])
        elif t.startswith('Horário de início'):
            troca_paragrafo(p, alvos['turno_24h'])

    # ---- tabela 0: a grade do mês ----
    total = monthrange(ano, mes)[1]
    # domingo = coluna 0
    primeiro = (date(ano, mes, 1).weekday() + 1) % 7
    celulas = [None] * primeiro + list(range(1, total + 1))
    while len(celulas) % 7:
        celulas.append(None)
    semanas = [celulas[i:i + 7] for i in range(0, len(celulas), 7)]

    grade = doc.tables[0]
    precisa = 1 + 2 * len(semanas)
    if len(grade.rows) < precisa:
        raise SystemExit(f'O modelo tem {len(grade.rows)} linhas e este mês precisa de {precisa}.')

    por_dia = {}
    for p in dados['plantoes']:
        por_dia.setdefault(int(p['dia'][8:10]), []).append(p)

    for si, semana in enumerate(semanas):
        linha_num = grade.rows[1 + si * 2]
        linha_con = grade.rows[2 + si * 2]
        for ci in range(7):
            d = semana[ci]
            escreve(linha_num.cells[ci], [str(d) if d else ''], negrito=True)
            itens = sorted(por_dia.get(d, []), key=lambda x: x['turno']) if d else []
            # no modelo, dia de um turno só sai em corpo maior; dia partido sai menor
            escreve(linha_con.cells[ci],
                    [i['nome'] + CURTO.get(i['turno'], '') for i in itens] or [''],
                    tamanho=12 if len(itens) < 2 else 10)

    # sobra de linhas do modelo, quando o mês ocupa menos semanas
    for ri in range(1 + 2 * len(semanas), len(grade.rows)):
        for c in grade.rows[ri].cells:
            escreve(c, [''])

    # ---- tabela 1: integrantes da escala regular ----
    # O chefe entra aqui com as horas dele e aparece de novo na tabela 2,
    # onde consta como compensado por indenização. É assim no modelo.
    regulares = sorted(dados['peritos'], key=lambda p: p['identificacao'])
    integrantes = doc.tables[1]
    while len(integrantes.rows) - 1 > len(regulares):
        integrantes._tbl.remove(integrantes.rows[-1]._tr)
    while len(integrantes.rows) - 1 < len(regulares):
        integrantes.add_row()
    for i, p in enumerate(regulares):
        linha = integrantes.rows[i + 1]
        escreve(linha.cells[0], [p['identificacao']], centro=False)
        escreve(linha.cells[1], [str(p['horas_extraordinarias']) + ' h'])

    # ---- tabela 2: chefe, compensado por indenização ----
    chefe = next((p for p in dados['peritos'] if p.get('chefe')), None)
    if chefe:
        linha = doc.tables[2].rows[1]
        escreve(linha.cells[0], [chefe['identificacao'] + ' - CHEFE'], centro=False)
        escreve(linha.cells[1], ['Expediente'])

    # ---- tabela 3: observações ----
    obs = list(dados.get('observacoes') or [])
    if obs:
        obs[0] = 'Observações:  ' + obs[0]
        escreve(doc.tables[3].rows[0].cells[0], obs, centro=False)

    # ---- assinaturas ----
    for p in doc.paragraphs:
        t = p.text.strip()
        if t.startswith('Chefe do 1'):
            pass
        elif t == 'Diretor de Perícia Criminal':
            pass
    paras = doc.paragraphs
    for i, p in enumerate(paras):
        t = p.text.strip()
        if t.startswith('Chefe do 1') and i > 0:
            troca_paragrafo(paras[i - 1], dados['chefe_nucleo'].upper())
        if t == 'Diretor de Perícia Criminal' and i > 0:
            troca_paragrafo(paras[i - 1], dados['diretor_pericia'].upper())

    doc.save(caminho_saida)
    print('gerado:', caminho_saida)
    print('mês:', rotulo, '· semanas:', len(semanas), '· plantões:', len(dados['plantoes']))


if __name__ == '__main__':
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
