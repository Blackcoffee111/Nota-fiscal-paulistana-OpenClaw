#!/usr/bin/env python3
"""
Emissor NFS-e SP — LAYOUT 2 (Reforma Tributária do Consumo / IBS-CBS).

Implementação COMPLETA do RPS versão 2.0 conforme o XSD oficial da Prefeitura
de SP (`schemas_oficiais_sp/TiposNFe_v02.xsd`, atualizado 29/12/2025) e o
Manual do WebService v3.3 (nov/2025).

Diferenças-chave em relação ao Layout 1 (emitir_nfse.py):
  - Envelope SOAP com VersaoSchema = 2
  - Cabeçalho do lote SEM ValorTotalServicos/ValorTotalDeducoes
  - RPS SEM <ValorServicos> — usa <ValorInicialCobrado>/<ValorFinalCobrado>
  - Campos novos obrigatórios: ValorIPI, ExigibilidadeSuspensa,
    PagamentoParceladoAntecipado, NBS
  - Grupo <IBSCBS> obrigatório (finNFSe, indFinal, cIndOp, indDest, valores)
  - Assinatura do RPS v2: Inscrição Municipal com 12 posições (era 8 na v1),
    usa ValorInicialCobrado no lugar de ValorServicos

VALIDAÇÃO LOCAL: antes de enviar, o XML é validado contra o XSD oficial com
lxml (pega erros de estrutura instantaneamente, sem gastar requisições).

A assinatura do RPS tem um self-test embutido contra os exemplos do manual
(rodar: `python emitir_nfse_v2.py --selftest`).

USO:
  python emitir_nfse_v2.py --selftest                          # valida assinatura
  python emitir_nfse_v2.py --modo teste --dados nota.json --dry-run --json-out
  python emitir_nfse_v2.py --modo teste --dados nota.json --json-out
"""

import os
import sys
import json
import argparse
import tempfile
import base64
from decimal import Decimal, ROUND_HALF_UP
from xml.dom.minidom import parseString

import requests
from dotenv import load_dotenv
from lxml import etree
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import pkcs12

# Reutiliza utilitários e infraestrutura já validada do Layout 1
import emitir_nfse as v1
from emitir_nfse import (
    formata_valor, limpa_documento, carrega_config, carrega_dados_nota,
    processar_resposta, assinar_lote, log,
)

load_dotenv(override=True)

DIR = os.path.dirname(os.path.abspath(__file__))
# Pasta com TODOS os XSDs descompactados (para os imports — xmldsig, tipos — resolverem)
XSD_LOTE = os.path.join(DIR, "schemas_oficiais_sp", "xsd_completo", "PedidoEnvioLoteRPS_v02.xsd")

URL_WEBSERVICE = "https://nfews.prefeitura.sp.gov.br/lotenfe.asmx"


# ───────────────────────────── Assinatura RPS v2 ──────────────────────────────

def centavos(valor):
    """Converte valor monetário em string de centavos (sem ponto)."""
    return str(int((Decimal(str(valor)) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP)))


def montar_string_assinatura_v2(config, nota):
    """Monta a cadeia de caracteres da assinatura do RPS v2.0.

    Ordem oficial (Manual WebService v3.3, "Campos para assinatura do RPS – v2.0"):
      1  Inscrição Municipal do Prestador .. 12 dígitos, zeros à esquerda
      2  Série do RPS ..................... 5 chars, espaços à DIREITA
      3  Número do RPS .................... 12 dígitos, zeros à esquerda
      4  Data de Emissão .................. AAAAMMDD
      5  Tipo de Tributação ............... 1 char
      6  Status do RPS .................... 1 char (N/C)
      7  ISS Retido ....................... S/N
      8  Valor Inicial Cobrado ............ 15 dígitos (centavos), zeros à esquerda
      9  Valor das Deduções ............... 15 dígitos (centavos), zeros à esquerda
      10 Código do Serviço ................ 5 dígitos, zeros à esquerda
      11 Indicador CPF/CNPJ Tomador ....... 1 dígito (1=CPF,2=CNPJ,3=não,4=NIF)
      12 CPF/CNPJ Tomador ................. 14 dígitos (zeros se 3/4)
      13 Indicador CPF/CNPJ Intermediário . 1 dígito (só se houver intermediário)
      14 CPF/CNPJ Intermediário ........... 14 dígitos (só se houver)
      15 ISS Retido Intermediário ......... S/N (só se houver)
      16 NIF ou NãoNIF .................... valor do NIF, ou 1 dígito NaoNIF
    """
    insc = str(config['inscricao_municipal']).zfill(12)               # 1 (12 posições!)
    serie = str(config['serie_rps']).ljust(5)                         # 2
    numero = str(nota['numero_rps']).zfill(12)                        # 3
    data = str(nota['data_emissao']).replace('-', '')[:8]             # 4
    tributacao = str(config['tributacao_rps'])[:1]                    # 5
    status = str(nota['status_rps'])                                  # 6
    iss_retido = str(nota['iss_retido'])                              # 7
    # Campo 8: Valor Inicial OU Final Cobrado (mesma posição na assinatura).
    # O webservice exige ValorFinalCobrado (erro 640 se usar Inicial).
    v_campo8 = (nota.get('valor_final_cobrado') or nota.get('valor_inicial_cobrado')
                or nota.get('valor_servicos', 0))
    vr_inicial = centavos(v_campo8).zfill(15)                         # 8
    vr_deducao = centavos(nota.get('valor_deducoes', 0)).zfill(15)    # 9
    cod_servico = str(config['codigo_servico']).zfill(5)             # 10

    ind_tomador = str(nota['indicador_tomador'])                     # 11
    doc_tomador = nota.get('documento_tomador', '')
    if nota['indicador_tomador'] in (3, 4):
        cpfcnpj_tomador = '0' * 14                                    # 12 (zeros)
    else:
        cpfcnpj_tomador = limpa_documento(doc_tomador).zfill(14)      # 12

    s = insc + serie + numero + data + tributacao + status + iss_retido + \
        vr_inicial + vr_deducao + cod_servico + ind_tomador + cpfcnpj_tomador

    # 13-15 Intermediário (só se houver)
    inter = nota.get('intermediario', {})
    cnpj_inter = limpa_documento(inter.get('cnpj', ''))
    if cnpj_inter:
        ind_inter = '2' if len(cnpj_inter) == 14 else '1'
        iss_inter = 'S' if inter.get('iss_retido', False) else 'N'
        s += ind_inter + cnpj_inter.zfill(14) + iss_inter

    # 16 NIF ou NãoNIF (indicador 4 = tomador estrangeiro; após o intermediário).
    # Tanto <NIF> quanto <NaoNIF> usam indicador 4. O campo 16 recebe o NIF
    # literal (se houver) ou o código NaoNIF (0/1/2) quando não há NIF.
    if nota['indicador_tomador'] == 4:
        s += str(nota.get('nif') or nota.get('nao_nif', ''))

    return s


def gerar_assinatura_rps_v2(config, nota):
    """Gera o hash RSA-SHA1 (base64) da string de assinatura do RPS v2."""
    string_rps = montar_string_assinatura_v2(config, nota)
    log(f"    (debug) RPS v2 String: '{string_rps}' (len: {len(string_rps)})")

    with open(config['certificado'], "rb") as f:
        p12 = f.read()
    senha = os.environ.get("NFSE_CERT_PASSWORD") or config.get('senha_certificado', '')
    chave, _, _ = pkcs12.load_key_and_certificates(p12, senha.encode('utf-8'))
    assinatura = chave.sign(string_rps.encode('ascii'), padding.PKCS1v15(), hashes.SHA1())
    return base64.b64encode(assinatura).decode('ascii')


# ──────────────────────────── Construção do XML v02 ───────────────────────────

def _esc(texto):
    """Escapa caracteres XML."""
    return (str(texto).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def construir_grupo_ibscbs(config, nota):
    """Monta o grupo <IBSCBS> obrigatório do RPS v2."""
    cfg = config.get('ibscbs', {})
    fin = cfg.get('fin_nfse', 0)
    ind_final = nota.get('ind_final', cfg.get('ind_final', 0))
    c_ind_op = str(cfg.get('c_ind_op', '000000')).zfill(6)
    ind_dest = nota.get('ind_dest', cfg.get('ind_dest', 0))
    cclass = str(cfg.get('cclasstrib', '000001')).zfill(6)

    # Destinatário (só quando indDest=1 e há dados)
    dest_xml = ''
    if ind_dest == 1 and nota.get('destinatario'):
        d = nota['destinatario']
        end = d.get('endereco', {})
        end_xml = ''
        if end:
            end_xml = (
                '<end><endNac>'
                f"<cMun>{end.get('cidade','')}</cMun>"
                f"<CEP>{limpa_documento(end.get('cep',''))}</CEP>"
                '</endNac>'
                f"<xLgr>{_esc(end.get('logradouro','')[:255])}</xLgr>"
                f"<nro>{_esc(end.get('numero','')[:60])}</nro>"
                f"<xBairro>{_esc(end.get('bairro','')[:60])}</xBairro>"
                '</end>'
            )
        dest_xml = (
            '<dest>'
            f"<xNome>{_esc(d.get('razao_social','')[:300])}</xNome>"
            f"{end_xml}"
            + (f"<email>{_esc(d['email'][:80])}</email>" if d.get('email') else '')
            + '</dest>'
        )

    return (
        '<IBSCBS>'
        f'<finNFSe>{fin}</finNFSe>'
        f'<indFinal>{ind_final}</indFinal>'
        f'<cIndOp>{c_ind_op}</cIndOp>'
        f'<indDest>{ind_dest}</indDest>'
        f'{dest_xml}'
        '<valores><trib><gIBSCBS>'
        f'<cClassTrib>{cclass}</cClassTrib>'
        '</gIBSCBS></trib></valores>'
        '</IBSCBS>'
    )


def construir_xml_lote_v2(config, nota, assinatura_rps):
    """Monta o <PedidoEnvioLoteRPS> versão 2 completo."""
    cfg_ibs = config.get('ibscbs', {})
    # ValorFinalCobrado = valor total da nota incluindo tributos (exigido pelo WS)
    v_final = (nota.get('valor_final_cobrado') or nota.get('valor_inicial_cobrado')
               or nota.get('valor_servicos', 0))

    # REGRA FISCAL (proteção defensiva): retenção na fonte (IRRF, INSS, e a
    # soma PCC no ValorCSLL) só vale quando o TOMADOR é PJ (indicador 2).
    # PF (1), sem identificação (3) e exterior (4) NÃO retêm. O débito próprio
    # (ValorPIS/ValorCOFINS) é SEMPRE mantido, independe do tomador.
    # Override: "tomador_retem": false no JSON (ex.: PJ do Simples Nacional).
    tomador_eh_pj = nota.get('indicador_tomador') == 2
    tomador_retem = nota.get('tomador_retem', tomador_eh_pj)
    v_pis = nota.get('valor_pis', 0)        # débito próprio — sempre
    v_cofins = nota.get('valor_cofins', 0)  # débito próprio — sempre
    v_inss = nota.get('valor_inss', 0) if tomador_retem else 0
    v_ir = nota.get('valor_ir', 0) if tomador_retem else 0
    v_csll = nota.get('valor_csll', 0) if tomador_retem else 0
    if not tomador_retem and (nota.get('valor_ir') or nota.get('valor_csll') or nota.get('valor_inss')):
        log("⚠️  Tomador não-PJ: retenções (IRRF/INSS/CSLL) zeradas — PF não retém na fonte. Débito próprio PIS/COFINS mantido.")

    # Discriminação (sem acentos/quebras — regra anti-erro 1057)
    texto_disc = str(nota.get('discriminacao', '')).strip()
    msg = config.get('mensagem_padrao', '').strip()
    if msg and msg not in texto_disc:
        texto_disc = (texto_disc + ' | ' + msg).strip(' |')

    # Bloco do tomador
    tomador_doc = ''
    if nota['indicador_tomador'] in (1, 2):
        tag = 'CNPJ' if nota['indicador_tomador'] == 2 else 'CPF'
        tomador_doc = (f'<CPFCNPJTomador><{tag}>'
                       f'{limpa_documento(nota.get("documento_tomador",""))}'
                       f'</{tag}></CPFCNPJTomador>')

    razao = nota.get('razao_social_tomador', '')
    razao_xml = f'<RazaoSocialTomador>{_esc(razao[:300])}</RazaoSocialTomador>' if razao else ''

    end = nota.get('endereco_tomador', {})
    end_xml = ''
    if end:
        end_xml = (
            '<EnderecoTomador>'
            f"<Logradouro>{_esc(end.get('logradouro','')[:50])}</Logradouro>"
            f"<NumeroEndereco>{_esc(end.get('numero','')[:10])}</NumeroEndereco>"
            f"<ComplementoEndereco>{_esc(end.get('complemento','')[:30])}</ComplementoEndereco>"
            f"<Bairro>{_esc(end.get('bairro','')[:30])}</Bairro>"
            f"<Cidade>{end.get('cidade','')}</Cidade>"
            f"<UF>{end.get('uf','')}</UF>"
            f"<CEP>{limpa_documento(end.get('cep',''))}</CEP>"
            '</EnderecoTomador>'
        )

    email_xml = f"<EmailTomador>{_esc(nota['email_tomador'][:75])}</EmailTomador>" if nota.get('email_tomador') else ''

    grupo_ibscbs = construir_grupo_ibscbs(config, nota)

    iss_retido_bool = 'true' if nota['iss_retido'] == 'S' else 'false'

    xml = (
        '<PedidoEnvioLoteRPS xmlns="http://www.prefeitura.sp.gov.br/nfe" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xmlns:xsd="http://www.w3.org/2001/XMLSchema">'
        '<Cabecalho xmlns="" Versao="2">'
        f'<CPFCNPJRemetente><CNPJ>{config["cnpj_prestador"]}</CNPJ></CPFCNPJRemetente>'
        '<transacao>false</transacao>'
        f'<dtInicio>{nota["data_emissao"]}</dtInicio>'
        f'<dtFim>{nota["data_emissao"]}</dtFim>'
        '<QtdRPS>1</QtdRPS>'
        '</Cabecalho>'
        '<RPS xmlns="">'
        f'<Assinatura>{assinatura_rps}</Assinatura>'
        '<ChaveRPS>'
        f'<InscricaoPrestador>{config["inscricao_municipal"]}</InscricaoPrestador>'
        f'<SerieRPS>{config["serie_rps"]}</SerieRPS>'
        f'<NumeroRPS>{nota["numero_rps"]}</NumeroRPS>'
        '</ChaveRPS>'
        '<TipoRPS>RPS</TipoRPS>'
        f'<DataEmissao>{nota["data_emissao"]}</DataEmissao>'
        f'<StatusRPS>{nota["status_rps"]}</StatusRPS>'
        f'<TributacaoRPS>{config["tributacao_rps"]}</TributacaoRPS>'
        f'<ValorDeducoes>{formata_valor(nota.get("valor_deducoes",0))}</ValorDeducoes>'
        f'<ValorPIS>{formata_valor(v_pis)}</ValorPIS>'
        f'<ValorCOFINS>{formata_valor(v_cofins)}</ValorCOFINS>'
        f'<ValorINSS>{formata_valor(v_inss)}</ValorINSS>'
        f'<ValorIR>{formata_valor(v_ir)}</ValorIR>'
        f'<ValorCSLL>{formata_valor(v_csll)}</ValorCSLL>'
        f'<CodigoServico>{config["codigo_servico"]}</CodigoServico>'
        f'<AliquotaServicos>{config["aliquota_servicos"]}</AliquotaServicos>'
        f'<ISSRetido>{iss_retido_bool}</ISSRetido>'
        f'{tomador_doc}'
        f'{razao_xml}'
        f'{end_xml}'
        f'{email_xml}'
        f'<Discriminacao>{_esc(texto_disc[:2000])}</Discriminacao>'
        # ValorInicialCobrado/ValorFinalCobrado são <xs:choice> — só UM.
        # O WS exige ValorFinalCobrado (valor total da nota, com tributos) — erro 640 se usar Inicial.
        f'<ValorFinalCobrado>{formata_valor(v_final)}</ValorFinalCobrado>'
        f'<ValorIPI>{formata_valor(nota.get("valor_ipi",0))}</ValorIPI>'
        f'<ExigibilidadeSuspensa>{nota.get("exigibilidade_suspensa",0)}</ExigibilidadeSuspensa>'
        f'<PagamentoParceladoAntecipado>{nota.get("pagamento_parcelado_antecipado",0)}</PagamentoParceladoAntecipado>'
        f'<NBS>{cfg_ibs.get("nbs","000000000")}</NBS>'
        # gpPrestacao: choice obrigatório (cLocPrestacao=cidade IBGE OU cPaisPrestacao)
        f'<cLocPrestacao>{nota.get("municipio_prestacao", cfg_ibs.get("municipio_prestacao","3550308"))}</cLocPrestacao>'
        f'{grupo_ibscbs}'
        '</RPS>'
        '</PedidoEnvioLoteRPS>'
    )
    return xml


# ──────────────────────────── Validação local (XSD) ───────────────────────────

def validar_contra_xsd(xml_str):
    """Valida o XML do lote contra o XSD oficial. Retorna (ok, erros)."""
    if not os.path.exists(XSD_LOTE):
        return None, ["XSD não encontrado em schemas_oficiais_sp/"]
    try:
        schema = etree.XMLSchema(etree.parse(XSD_LOTE))
        doc = etree.fromstring(xml_str.encode('utf-8'))
        if schema.validate(doc):
            return True, []
        return False, [str(e) for e in schema.error_log]
    except Exception as e:
        return False, [f"Erro ao validar: {e}"]


# ────────────────────────────────── Emissão ───────────────────────────────────

def emitir_nota_v2(config_file, dados_file, modo, dry_run=False, validar=True):
    log("=" * 60)
    log(f"  NFS-e SP — LAYOUT 2 (RTC/IBS-CBS) | Modo: {modo.upper()}"
        + (" | DRY RUN" if dry_run else ""))
    log("=" * 60)

    config = carrega_config(config_file)
    nota = carrega_dados_nota(dados_file)

    senha = os.environ.get("NFSE_CERT_PASSWORD") or config.get('senha_certificado', '')
    if not senha:
        return {"sucesso": False, "erros": [{"codigo": "SEC", "descricao": "Senha do certificado ausente"}]}

    with open(config['certificado'], "rb") as f:
        p12 = f.read()
    chave, cert, _ = pkcs12.load_key_and_certificates(p12, senha.encode('utf-8'))
    chave_pem = chave.private_bytes(serialization.Encoding.PEM,
                                    serialization.PrivateFormat.PKCS8,
                                    serialization.NoEncryption())
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)

    log("[1/6] Gerando assinatura RPS v2...")
    assinatura = gerar_assinatura_rps_v2(config, nota)

    log("[2/6] Montando XML do lote (layout v2)...")
    xml_nao_assinado = construir_xml_lote_v2(config, nota, assinatura)

    log("[3/6] Assinando digitalmente (XMLDSig)...")
    xml_assinado = assinar_lote(xml_nao_assinado, chave_pem, cert_pem)

    if validar:
        log("[4/6] Validando contra XSD oficial...")
        # Valida o XML final (já com a <Signature>, que é obrigatória no schema)
        ok, erros = validar_contra_xsd(xml_assinado)
        if ok is True:
            log("      ✅ XML válido contra o XSD oficial")
        elif ok is False:
            log("      ❌ XML inválido:")
            for e in erros[:8]:
                log(f"         - {e}")
            return {"sucesso": False, "erros": [{"codigo": "XSD", "descricao": e} for e in erros]}
        else:
            log(f"      ⚠️  {erros[0]}")

    if dry_run:
        log("\n" + "=" * 60 + "\n  DRY RUN — XML montado (não enviado):\n" + "=" * 60)
        try:
            pretty = parseString(xml_assinado).toprettyxml(indent='  ')
            print('\n'.join(l for l in pretty.splitlines() if l.strip() and not l.strip().startswith('<?xml')))
        except Exception:
            print(xml_assinado)
        return {"sucesso": True, "dry_run": True, "mensagem": "XML v2 gerado localmente."}

    xml_escapado = (xml_assinado.replace('&', '&amp;').replace('<', '&lt;')
                    .replace('>', '&gt;').replace('"', '&quot;'))

    if modo == 'teste':
        wrapper, action = 'TesteEnvioLoteRPSRequest', '"http://www.prefeitura.sp.gov.br/nfe/ws/testeenvio"'
    else:
        wrapper, action = 'EnvioLoteRPSRequest', '"http://www.prefeitura.sp.gov.br/nfe/ws/envioLoteRPS"'

    envelope = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
        'xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
        '<soap:Body>'
        f'<{wrapper} xmlns="http://www.prefeitura.sp.gov.br/nfe">'
        '<VersaoSchema>2</VersaoSchema>'
        f'<MensagemXML>{xml_escapado}</MensagemXML>'
        f'</{wrapper}>'
        '</soap:Body></soap:Envelope>'
    )

    log("[5/6] Enviando para a Prefeitura (VersaoSchema=2)...")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pem") as tc:
        tc.write(chave_pem + b'\n' + cert_pem)
        cert_path = tc.name
    try:
        resp = requests.post(URL_WEBSERVICE, data=envelope.encode('utf-8'),
                             headers={'Content-Type': 'text/xml; charset=utf-8', 'SOAPAction': action},
                             cert=cert_path, timeout=60, allow_redirects=False)
        with open('debug_resposta_v2.xml', 'w', encoding='utf-8') as f:
            f.write(resp.text)
        log("[6/6] Processando resposta...")
        if resp.status_code == 200:
            return processar_resposta(resp.text)
        log(f"❌ HTTP {resp.status_code}")
        return {"sucesso": False, "erros": [{"codigo": str(resp.status_code), "descricao": "Erro HTTP"}]}
    finally:
        if os.path.exists(cert_path):
            os.remove(cert_path)


# ─────────────────────────────────── Self-test ────────────────────────────────

def selftest_assinatura():
    """Valida montar_string_assinatura_v2 contra os exemplos oficiais do manual."""
    # Valores e strings copiados LITERALMENTE do Manual WebService v3.3
    # (R$ 20.500,00 inicial / R$ 5.000,00 deduções).
    cfg = {'inscricao_municipal': '123456789012', 'serie_rps': 'RTNT',
           'tributacao_rps': 'T', 'codigo_servico': '2658'}
    base = dict(numero_rps=1, data_emissao='2026-01-01', status_rps='N',
                iss_retido='N', valor_inicial_cobrado=20500.00, valor_deducoes=5000.00)
    casos = [
        # CPF tomador, COM intermediário
        (cfg, dict(base, indicador_tomador=1, documento_tomador='13167474254',
                   intermediario={'cnpj': '09999999000106', 'iss_retido': True}),
         "123456789012RTNT 00000000000120260101TNN00000000205000000000000050000002658100013167474254209999999000106S"),
        # CPF tomador, SEM intermediário
        (cfg, dict(base, indicador_tomador=1, documento_tomador='13167474254'),
         "123456789012RTNT 00000000000120260101TNN00000000205000000000000050000002658100013167474254"),
        # NIF (tomador estrangeiro), SEM intermediário
        (cfg, dict(base, indicador_tomador=4, nif='W123456789'),
         "123456789012RTNT 00000000000120260101TNN00000000205000000000000050000002658400000000000000W123456789"),
        # NIF, COM intermediário (intermediário vem ANTES do NIF)
        (cfg, dict(base, indicador_tomador=4, nif='W123456789',
                   intermediario={'cnpj': '09999999000106', 'iss_retido': True}),
         "123456789012RTNT 00000000000120260101TNN00000000205000000000000050000002658400000000000000209999999000106SW123456789"),
        # NaoNIF (estrangeiro sem NIF — usa indicador 4), SEM intermediário
        (cfg, dict(base, indicador_tomador=4, nao_nif='2'),
         "123456789012RTNT 00000000000120260101TNN000000002050000000000000500000026584000000000000002"),
        # NaoNIF, COM intermediário
        (cfg, dict(base, indicador_tomador=4, nao_nif='2',
                   intermediario={'cnpj': '09999999000106', 'iss_retido': True}),
         "123456789012RTNT 00000000000120260101TNN00000000205000000000000050000002658400000000000000209999999000106S2"),
    ]
    ok = True
    for i, (cfg, nota, esperado) in enumerate(casos, 1):
        got = montar_string_assinatura_v2(cfg, nota)
        status = "✅" if got == esperado else "❌"
        if got != esperado:
            ok = False
            print(f"{status} Caso {i}: DIVERGÊNCIA")
            print(f"   esperado: {esperado}")
            print(f"   obtido  : {got}")
        else:
            print(f"{status} Caso {i}: OK ({len(got)} chars)")
    return ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Emissor NFS-e SP — Layout 2 (RTC)")
    parser.add_argument("--modo", choices=['teste', 'producao'], default='teste')
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--dados", default="dados_nota.json")
    parser.add_argument("--json-out", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-validate", action="store_true", help="Pula validação XSD local")
    parser.add_argument("--selftest", action="store_true", help="Testa a assinatura contra exemplos do manual")
    args = parser.parse_args()

    if args.selftest:
        sys.exit(0 if selftest_assinatura() else 1)

    if args.json_out:
        v1.IS_JSON_OUT = True
        import warnings
        warnings.filterwarnings('ignore')

    resultado = emitir_nota_v2(args.config, args.dados, args.modo,
                               dry_run=args.dry_run, validar=not args.no_validate)
    if args.json_out and resultado:
        print(json.dumps(resultado, indent=2, ensure_ascii=False, default=str))
