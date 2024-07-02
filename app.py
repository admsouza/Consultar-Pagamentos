from flask import Flask, render_template, request
import requests
import babel.numbers 
from collections import defaultdict
from datetime import datetime


app = Flask(__name__)

API_URL = 'https://sagrescaptura.tce.pb.gov.br/api/v1/receitas-orcamentarias'
TOKEN = '3938a148-5b81-4ad7-ba2c-dcc68e5106ff'


@app.template_filter('brl')
def brl_filter(value):
    return format_brl(value)


def format_brl(value):
    # Formata o valor como moeda BRL
    formatted_value = babel.numbers.format_currency(value, 'BRL', locale='pt_BR')
    return formatted_value


@app.route('/', methods=['GET', 'POST'])
def consult_recipes():
    if request.method == 'POST':
        cod_unidade = request.form['cod_unidade']
        data_minima = request.form['data_minima']
        data_maxima = request.form['data_maxima']

        params = {
            'codUnidadeGestora': cod_unidade,
            'dataMinima': data_minima,
            'dataMaxima': data_maxima
        }

        headers = {
            'AuthToken': TOKEN
        }

        response_api = requests.get(API_URL, params=params, headers=headers)

        if response_api.status_code == 200:
            data = response_api.json()
            data = sorted(data, key=lambda x: datetime.strptime(
                x['competencia'], '%Y-%m-%d'))  # Ordena os dados pela data

            # Calcular soma total e somas por data, excluindo códigos específicos 3, 4 e 5
            total_receita = 0
            total_estornos = 0
            total_deducao_fundeb = 0  # Soma para dedução de receita para a formação do Fundeb
            receitas_por_data = defaultdict(float)
            estornos_por_data = defaultdict(float)
            deducoes_fundeb_por_data = defaultdict(float)

            for item in data:
                valor = -item['valor'] if item['tipoLancamento']['nome'] == 'Estorno' else item['valor']
                
                # Verifica o tipo de receita pelo código
                tipo_codigo = item['tipoReceitaLancada']['codigo']
                if tipo_codigo in [3, 4, 5]:
                    total_deducao_fundeb += valor
                    deducoes_fundeb_por_data[item['competencia']] += valor
                else:
                    total_receita += valor
                    receitas_por_data[item['competencia']] += valor

                    if item['tipoLancamento']['nome'] == 'Estorno':
                        total_estornos += valor
                        estornos_por_data[item['competencia']] += valor

            # Calcular o total de receitas líquidas após subtrair deduções e estornos
            total_receita_liquida = total_receita - total_deducao_fundeb

            # Ordena os dicionários por data
            receitas_por_data = dict(sorted(receitas_por_data.items(),
                                            key=lambda x: datetime.strptime(x[0], '%Y-%m-%d')))
            estornos_por_data = dict(sorted(estornos_por_data.items(),
                                            key=lambda x: datetime.strptime(x[0], '%Y-%m-%d')))
            deducoes_fundeb_por_data = dict(sorted(deducoes_fundeb_por_data.items(),
                                                   key=lambda x: datetime.strptime(x[0], '%Y-%m-%d')))

            # Passa os totais e dados para o template
            return render_template('table.html', data=data, total_receita=total_receita,
                                   total_estornos=total_estornos, total_deducao_fundeb=total_deducao_fundeb,
                                   total_receita_liquida=total_receita_liquida,
                                   receitas_por_data=receitas_por_data, estornos_por_data=estornos_por_data,
                                   deducoes_fundeb_por_data=deducoes_fundeb_por_data)
        else:
            error = f"Regras de Consulta: Intervalo máximo de 31 dias: {response_api.status_code}"
            return render_template('index.html', error=error)

    # Caso o método não seja POST, retorna a página inicial normalmente
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
