from argparse import ArgumentError
import json
import os
import traceback
import boto3
import pccc

import logger as lambda_logger

# jira library
from jira import JIRA

env = os.environ

xray = env.get("ENABLE_XRAY", "")
if xray == "":
    xray = False
else:
    xray = True

logger = lambda_logger.Logger(__name__, env.get('LOGGING_LEVEL', "OFF"), enable_xray=xray)

AWS_REGION = env.get('AWS_REGION', 'us-east-1')
ATLASSIAN_URL = env.get('ATLASSIAN_URL')
CREDS_ARN = env.get('SECRETS_MANAGER_ARN', None)

def add_comment_to_issue(issue: str, comment: str) -> str:
    '''
    Adiciona um comentário em uma issue no JIRA. As credenciais de acesso ao JIRA podem ser obtidas tanto por variáveis de ambiente
    (não seguro) quanto por secret manager (seguro e recomendado)
    '''

    if CREDS_ARN is None: 

        logger.warn("Nome do secrets manager para obter as credenciais do JIRA não foi encontrado. Utilizar variáveis de ambiente (NÃO UTILIZAR ESTE MÉTODO EM AMBIENTE PRODUTIVO")

        jira_username = env.get('USER_NAME', None)
        jira_api_token = env.get('API_TOKEN', None)

        if jira_username is None or jira_api_token is None:
            raise ArgumentError("Um dos parâmetros de credenciais do JIRA não foi informado")

        jira_auth = (jira_username, jira_api_token)
    
    else:

        try:
            secretsmanager = boto3.client('secretsmanager', region_name=AWS_REGION)
            result = secretsmanager.get_secret_value(SecretId=CREDS_ARN)
        except:
            raise ArgumentError("Um dos parâmetros de credenciais do JIRA não foi informado")

        jira_secret = json.loads(result.get("SecretString"))
        jira_auth = (jira_secret.get('username'), jira_secret.get('jira_api_token'))


    jira_client = JIRA(ATLASSIAN_URL, basic_auth=jira_auth)
    logger.debug(f'Escrevendo comentário {comment}, na atividade {issue}')

    try:

        comment_id = jira_client.add_comment(issue, comment)

    except Exception as e:

        traceback_msg = traceback.format_exc()
        logger.critical(f'Erro ao tentar escrever comentário na issue {issue} - {traceback_msg}')
        raise e

    return f'{comment_id} - Comentario adicionado com sucesso'

def get_commit_message(repository: str, branch_name: str, commit_hash: str) -> dict:
    '''
        Responsável por coletar o commit_info
        
        inputs:
            repository:
                description: Nome do repositorio
                type: string
            commit_hash: 
                description: Id do commit
                type: string
        response:
            - type: dict
                    payload = {
                    'branch': "string",
                    'message': "string"
                }
    '''

    codecommit = boto3.client('codecommit', region_name=AWS_REGION)
    logger.info('Client CodeCommit inicializado com sucesso')

    
    commit_info = codecommit.get_commit(repositoryName=repository, commitId=commit_hash)
    logger.debug(f'Commit info - {commit_info}')

    # coletando a mensagem de commit
    commit_message = commit_info['commit']['message']

    ccr = pccc.ConventionalCommitRunner()

    ccr.options.update(
        types = [
            "build",
            "ci",
            "docs",
            "feat",
            "fix",
            "perf",
            "refactor",
            "release",
            "style",
            "test"
        ], 
        scopes = [branch_name]
    )
    ccr.raw = commit_message
    ccr.clean()
    ccr.parse()
    if ccr.exc != None:
        raise BaseException('Invalid commit message')

    payload = {
        'branch': ccr.header.get("scope"),
        'message': f'* {commit_hash[0:7]} {commit_message}',
        'body': ccr.body
    }

    return payload

def lambda_handler(event, context):

    logger.debug(f'Evento recebido antes do tratamento - {event}')

    records_from_sns = event['Records']
    for record_from_sns in records_from_sns:
        
        body = record_from_sns['body']

        json_body = json.loads(body)

        records = json.loads(json_body['Message'])['Records']

        for record in records:

            logger.info(f'Evento recebido - {record}')

            references = record['codecommit']['references'][0]
            commit_hash = references['commit']
            repository = record['eventSourceARN'].split(':')[5]

            branch_name = references['ref'].split('/')[-1] # o último item é o nome do branch

            payload = get_commit_message(repository, branch_name, commit_hash)
            logger.debug(payload)

            issue = payload.get('branch')
            comment = payload.get('message')

            logger.debug(f"branch a se conectar: {issue}")

            if issue is not None and issue != "":
                result = add_comment_to_issue(issue, comment)
            else:
                result = "Mensagem de commit não possui branch associado. Nada a ser feito."

            logger.info(result)