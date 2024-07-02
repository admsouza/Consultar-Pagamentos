from flask import Flask, render_template, request
import requests
import locale
from collections import defaultdict
from datetime import datetime


app = Flask(__name__)

API_URL = 'https://sagrescaptura.tce.pb.gov.br/api/v1/receitas-orcamentarias'
TOKEN = '3938a148-5b81-4ad7-ba2c-dcc68e5106ff'


def format_brl(value):
    # Defina aqui a localidade para formatação
    locale.setlocale(locale.LC_ALL, 'pt_BR.utf8')
    formatted_value = locale.currency(value, grouping=True)
    # Resetar a localidade para evitar problemas
    locale.resetlocale(locale.LC_ALL)
    return formatted_value


def format_brl(value):
    return locale.currency(value, grouping=True)


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

            # Calcular soma total e somas por data
            total_receita = 0
            total_estornos = 0
            receitas_por_data = defaultdict(float)
            estornos_por_data = defaultdict(float)

            for item in data:
                valor = - \
                    item['valor'] if item['tipoLancamento']['nome'] == 'Estorno' else item['valor']
                total_receita += valor
                receitas_por_data[item['competencia']] += valor

                if item['tipoLancamento']['nome'] == 'Estorno':
                    total_estornos += valor
                    estornos_por_data[item['competencia']] += valor

            receitas_por_data = dict(sorted(receitas_por_data.items(),
                                            key=lambda x: datetime.strptime(x[0], '%Y-%m-%d')))
            estornos_por_data = dict(sorted(estornos_por_data.items(),
                                            key=lambda x: datetime.strptime(x[0], '%Y-%m-%d')))

            return render_template('table.html', data=data, total_receita=total_receita,
                                   total_estornos=total_estornos, receitas_por_data=receitas_por_data,
                                   estornos_por_data=estornos_por_data)
        else:
            error = f"Erro ao consultar API: {response_api.status_code}"
            return render_template('index.html', error=error)

    # Caso o método não seja POST, retorna a página inicial normalmente
    return render_template('index.html')


@app.template_filter('brl')
def brl_filter(value):
    return format_brl(value)


if __name__ == '__main__':
    app.run(debug=True)
