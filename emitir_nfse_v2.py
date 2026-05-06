#!/usr/bin/env python3
"""
Emissor NFS-e SP — Layout v2 (RTC / IBS-CBS).

Estende emitir_nfse.py adicionando o grupo IBSCBS conforme:
  - NT 04 SE/CGNFS-e v1.1 (19/08/2025) — caminho NFSe/infNFSe/DPS/infDPS/IBSCBS/
  - LC 214/2025 (Reforma Tributária do Consumo)
  - Informe Técnico RT 2025.002 v1.10 (tabelas CST / cClassTrib / cCredPres)

⚠️ ESCOPO DESTE SCAFFOLD
------------------------
A NT 04 define o grupo IBSCBS na DPS do **padrão nacional** da NFS-e
(NFSe/infNFSe/DPS/infDPS/IBSCBS/). A Prefeitura de SP, em 2026, mantém
seu webservice legado (lotenfe.asmx, envelope <PedidoEnvioLoteRPS>) e
incorpora o IBSCBS dentro do bloco <RPS>. A posição EXATA do grupo
dentro do RPS depende do XSD oficial do "Layout 2" publicado pela
Sec. Fazenda SP, que pode evoluir nas próximas semanas.

Este arquivo:
  ✓ Implementa o grupo IBSCBS com os campos da NT 04 v1.1
  ✓ Calcula alíquotas-teste (CBS 0,9% / IBS 0,1%) em 2026
  ✓ Mantém compatibilidade com o pipeline de assinatura existente
  ⚠ A posição do bloco <IBSCBS> dentro de <RPS> está marcada com
    TODO_SP_LAYOUT_V2 — confirmar contra o XSD da Prefeitura.
  ⚠ Recomendado SEMPRE rodar com --dry-run antes de --modo teste.

USO
---
  python emitir_nfse_v2.py --modo teste --dados nota.json --dry-run --json-out
  python emitir_nfse_v2.py --modo teste --dados nota.json --json-out
"""

import argparse
import json
import re
import sys
from decimal import Decimal, ROUND_HALF_UP

import emitir_nfse as v1

# Referência fixa ao construtor original (evita recursão durante o monkey-patch)
_CONSTRUIR_XML_V1_ORIGINAL = v1.construir_xml_lote


def calcular_ibscbs(config_ibs, valor_servicos):
    """Calcula valores informativos de IBS e CBS conforme alíquotas configuradas.

    Em 2026 (fase de teste), CBS=0,9% e IBS=0,1%. Os valores são destacados
    na NF-e mas NÃO são recolhidos (LC 214/2025 dispensa o recolhimento de
    sujeitos passivos que cumprirem as obrigações acessórias).
    """
    vs = Decimal(str(valor_servicos))
    a_cbs = Decimal(str(config_ibs.get('aliquota_cbs', 0.009)))
    a_uf = Decimal(str(config_ibs.get('aliquota_ibs_uf', 0.001)))
    a_mun = Decimal(str(config_ibs.get('aliquota_ibs_mun', 0.0)))

    v_cbs = (vs * a_cbs).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    v_ibs_uf = (vs * a_uf).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    v_ibs_mun = (vs * a_mun).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    v_ibs_total = v_ibs_uf + v_ibs_mun

    return {
        'v_cbs': v_cbs,
        'v_ibs_uf': v_ibs_uf,
        'v_ibs_mun': v_ibs_mun,
        'v_ibs_total': v_ibs_total,
        'p_cbs': a_cbs,
        'p_ibs_uf': a_uf,
        'p_ibs_mun': a_mun,
    }


def construir_grupo_ibscbs(config, nota):
    """Monta o bloco XML <IBSCBS> conforme NT 04 v1.1 — caminho DPS/infDPS/IBSCBS/.

    Retorna string XML pronta para ser inserida no envelope. Se o config tiver
    `ibscbs.habilitado=false`, retorna string vazia (compatibilidade com v1).
    """
    cfg = config.get('ibscbs', {})
    if not cfg.get('habilitado'):
        return ''

    val = calcular_ibscbs(cfg, nota['valor_servicos'])

    # Destinatário (quando diferente do tomador). Por padrão indDest=0 → tomador é destinatário.
    ind_dest = nota.get('ind_dest', cfg.get('ind_dest', 0))

    cst = str(cfg.get('cst', '000')).zfill(3)
    cclass = str(cfg.get('cclasstrib', '000001')).zfill(6)
    ccred = cfg.get('ccredpres')
    fin = cfg.get('fin_nfse', 0)
    ind_final = cfg.get('ind_final', 0)
    c_ind_op = str(cfg.get('c_ind_op', '111111'))

    # Bloco gIBSCBS interno
    gibscbs = (
        f'<gIBSCBS>'
        f'<CST>{cst}</CST>'
        f'<cClassTrib>{cclass}</cClassTrib>'
        + (f'<cCredPres>{str(ccred).zfill(2)}</cCredPres>' if ccred else '')
        + f'</gIBSCBS>'
    )

    valores = (
        f'<valores>'
        f'<trib>{gibscbs}</trib>'
        f'</valores>'
    )

    # Grupo destinatário (opcional). Só preenche se nota tiver dados de destinatário distintos.
    dest_xml = ''
    if ind_dest and nota.get('destinatario'):
        d = nota['destinatario']
        doc = v1.limpa_documento(d.get('documento', ''))
        tag_doc = 'CNPJ' if len(doc) == 14 else 'CPF'
        end = d.get('endereco', {})
        dest_xml = (
            f'<dest>'
            f'<{tag_doc}>{doc}</{tag_doc}>'
            f'<xNome>{d.get("razao_social", "")[:150]}</xNome>'
            + (
                f'<end>'
                f'<endNac>'
                f'<cMun>{end.get("cidade", "")}</cMun>'
                f'<CEP>{v1.limpa_documento(end.get("cep", ""))}</CEP>'
                f'</endNac>'
                f'<xLgr>{end.get("logradouro", "")[:255]}</xLgr>'
                f'<nro>{end.get("numero", "")[:60]}</nro>'
                f'<xBairro>{end.get("bairro", "")[:60]}</xBairro>'
                f'</end>' if end else ''
            )
            + (f'<email>{d["email"][:80]}</email>' if d.get('email') else '')
            + f'</dest>'
        )

    return (
        f'<IBSCBS>'
        f'<finNFSe>{fin}</finNFSe>'
        f'<indFinal>{ind_final}</indFinal>'
        f'<cIndOp>{c_ind_op}</cIndOp>'
        f'<indDest>{ind_dest}</indDest>'
        f'{dest_xml}'
        f'{valores}'
        f'</IBSCBS>'
    )


def construir_xml_lote_v2(config, nota, assinatura_rps):
    """Monta o XML do lote chamando o construtor v1 e injetando o grupo IBSCBS."""
    xml_v1 = _CONSTRUIR_XML_V1_ORIGINAL(config, nota, assinatura_rps)
    grupo = construir_grupo_ibscbs(config, nota)
    if not grupo:
        return xml_v1

    # TODO_SP_LAYOUT_V2: confirmar posição exata do <IBSCBS> dentro de <RPS>
    # contra o XSD oficial do Layout 2 da Prefeitura SP. Posição provisória:
    # imediatamente após </Discriminacao> e antes de </RPS>.
    if '</Discriminacao>' not in xml_v1:
        v1.log("⚠️  Não encontrou </Discriminacao> para injetar IBSCBS. XML v1 inalterado.")
        return xml_v1

    xml_v2 = xml_v1.replace('</Discriminacao>', '</Discriminacao>' + grupo, 1)
    return xml_v2


def emitir_nota_v2(config_file, dados_file, modo, dry_run=False):
    """Wrapper de v1.emitir_nota que substitui o construtor de XML por v2."""
    # Monkey-patch temporário do construtor — preserva todo o resto do pipeline.
    v1.construir_xml_lote = construir_xml_lote_v2
    try:
        v1.log("🆕 LAYOUT v2 (RTC / IBS-CBS) — NT 04 v1.1")
        return v1.emitir_nota(config_file, dados_file, modo, dry_run=dry_run)
    finally:
        v1.construir_xml_lote = _CONSTRUIR_XML_V1_ORIGINAL


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Emissor NFS-e SP — Layout v2 (RTC)')
    parser.add_argument('--modo', choices=['teste', 'producao'], default='teste')
    parser.add_argument('--config', default='config.json')
    parser.add_argument('--dados', default='dados_nota.json')
    parser.add_argument('--json-out', action='store_true')
    parser.add_argument('--dry-run', action='store_true',
                        help='Monta e assina o XML mas NÃO envia (para inspeção)')
    args = parser.parse_args()

    if args.json_out:
        v1.IS_JSON_OUT = True
        import warnings
        warnings.filterwarnings('ignore')

    resultado = emitir_nota_v2(args.config, args.dados, args.modo, dry_run=args.dry_run)
    if args.json_out and resultado:
        print(json.dumps(resultado, indent=2, ensure_ascii=False, default=str))
