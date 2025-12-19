from http import HTTPStatus

import requests

from app.security import Settings

settings = Settings()

HEADERS = {"Authorization": f"Basic {settings.INTOUCH_TOKEN}"}


def buscar_funcionario(matricula: str):

    print(f" Buscando o usuário da matrícula: {matricula}")

    if not settings.INTOUCH_TOKEN:
        return {"erro": "Token não configurado"}
    if not settings.INTOUCH_URL:
        return {"erro": "URL não configurada"}

    filtro = f'profile.employeeid eq "{matricula}"'

    try:
        response = requests.get(
            settings.INTOUCH_URL, params={"filter": filtro}, headers=HEADERS
        )

        if response.status_code != HTTPStatus.OK:
            return {
                "erro": f"Erro API Staffbase: {response.status_code}",
                "sucesso": False, "detalhe": response.text
            }

        json_resposta = response.json()

    # tive que tratar o formato, tava vindo errado,
    # entao vai tudo virar o mesmo tipo em lista

        if isinstance(json_resposta, dict) and 'data' in json_resposta:
            lista_usuarios = json_resposta['data']
        elif isinstance(json_resposta, list):
            lista_usuarios = json_resposta
        else:
            lista_usuarios = []

        if not lista_usuarios:
            return {"sucesso": False, "erro": "Usuário não encontrado."}

    # tudo vai pra essa lista, sempre pegando o primeiro (o pesquisado)

        usuario_bruto = lista_usuarios[0]

        primeiro_nome = usuario_bruto.get('firstName', '')
        sobrenome = usuario_bruto.get('lastName', '')
        nome_completo = f"{primeiro_nome} {sobrenome}".strip()

        return {
            "sucesso": True,
            "encontrado": True,
            "id_sistema": usuario_bruto.get('id'),
            "nome": nome_completo,
            "email": usuario_bruto.get('profile', {}).get('workemail'),
            "cargo": usuario_bruto.get('position'),
            "status_atual": usuario_bruto.get('status'),
            "Matricula": matricula
        }

    except Exception as e:
        return {"erro": str(e), "sucesso": False}


def desativar_funcionario(matricula: str):
    print(f" Iniciando processo para matrícula: {matricula}")

    # 1. Busca os dados atuais
    dados = buscar_funcionario(matricula)

    if not dados or not dados.get('sucesso'):
        return {"success": False, "error": "Usuário não encontrado."}

    user_id = dados['id_sistema']
    nome = dados['nome']
    status_atual = dados['status_atual']

    print(f" Status atual: '{status_atual}'")


# 1º - SE O USUÁRIO FOR ATIVADO, NAO PODEMOS DELETAR, SÓ DESATIVAR, LOGO:

    if status_atual == 'activated':
        print(" Usuário ativo. Mudando status para DEACTIVATED.")

        url_update = f"{settings.INTOUCH_URL}/{user_id}"
        payload = {"status": "deactivated"}
        headers_update = {
            "Authorization": f"Basic {settings.INTOUCH_TOKEN}",
            "Content-Type": "application/vnd.staffbase.accessors.user-update.v1+json"
        }

        try:
            resp = requests.put(url_update, json=payload, headers=headers_update)
            if resp.status_code == HTTPStatus.OK or resp.status_code == HTTPStatus.NO_CONTENT:
                return {
                    "success": True,
                    "message": f"Usuário {nome} foi DESATIVADO com sucesso.",
                    "acao": "desativacao"
                }
            else:
                return {
                        "success": False,
                        "error": f"Erro ao desativar: {resp.text}"
                    }
        except Exception as e:
            return {"success": False, "error": str(e)}

# 2º - SE O USUÁRIO NAO FOR ATIVO E FOR PENDENTE
# (recebeu o email e nao ativou a conta), DELETA.
# Pesquisei e esses outros dois são
# só pra garantir a segurança caso tenha algum sinônimo no banco)

    elif status_atual in ['pending', 'created', 'invited']:
        print(" Usuário pendente/criado. Executando EXCLUSÃO definitiva.")

        url_delete = f"{settings.INTOUCH_URL}/{user_id}"

        try:
            resp = requests.delete(url_delete, headers=HEADERS)
            if resp.status_code == HTTPStatus.OK or resp.status_code == HTTPStatus.NO_CONTENT:
                return {
                    "success": True,
                    "message": f"Convite do usuário {nome} foi EXCLUÍDO com sucesso.",
                    "acao": "exclusao"
                }
            else:
                return {"success": False, "error": f"Erro ao deletar: {resp.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# 3º - TA DESATIVADO OU PROTEGIDO, nao faz NADA

    elif status_atual in ['contact', 'deactivated']:
        print(f" Status '{status_atual}' é protegido ou já processado. Nenhuma ação.")
        return {
            "success": True,  # Retorna True pq não foi erro, foi uma decisão lógica
            "message": f"Usuário {nome} está como '{status_atual}' e não precisa ser alterado.",
            "acao": "nenhuma"
        }

    # 4º - se for desconhecido, cancela
    else:
        return {
            "success": False,
            "error": f"""
                Status desconhecido ('{status_atual}').
                Operação cancelada por segurança.
            """
        }
