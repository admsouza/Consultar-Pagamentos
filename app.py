from flask import Flask, render_template, request
import requests
from collections import defaultdict
import locale
from datetime import datetime

app = Flask(__name__)

API_URL = 'https://sagresonline.tce.pb.gov.br/api/v2/municipal/execucao-orcamentaria/pagamentos'

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')  # Define o local para formato de moeda brasileira

@app.route('/', methods=['GET', 'POST'])
def consult_payments():
    data = []
    grouped_data = defaultdict(lambda: {'pago': 0, 'retido': 0, 'liquido': 0})

    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        unidade_gestora = request.form.get('unidade_gestora')
        
        params = {
            'startDate': start_date,
            'endDate': end_date,
            'unidadesGestoras[]': unidade_gestora
        }
        
        try:
            response = requests.get(API_URL, params=params)
            response.raise_for_status()
            api_data = response.json()

            # Filtra apenas os dados desejados e agrupa por data de pagamento
            if isinstance(api_data, list):
                for item in api_data:
                    dados_pagamento = item.get('dadosPagamento', {})
                    data_pagamento = dados_pagamento.get('dataPagamento', '')

                    if data_pagamento:
                        # Extrai apenas a parte da data, ignorando o tempo
                        data_pagamento = data_pagamento.split(' ')[0]
                        grouped_data[data_pagamento]['pago'] += dados_pagamento.get('pago', 0)
                        grouped_data[data_pagamento]['retido'] += dados_pagamento.get('retido', 0)
                        grouped_data[data_pagamento]['liquido'] += dados_pagamento.get('liquido', 0)
            else:
                return "Erro na resposta da API: Estrutura de dados inesperada.", 500

        except requests.RequestException as e:
            return f"Erro na consulta: {e}", 500

    # Ordena os dados por data de pagamento
    sorted_data = sorted(grouped_data.items(), key=lambda x: datetime.strptime(x[0], '%Y-%m-%d'))

    # Formata os valores para moeda brasileira
    formatted_data = [
        {
            'dataPagamento': data_pagamento,
            'pago': locale.currency(valores['pago'], grouping=True),
            'retido': locale.currency(valores['retido'], grouping=True),
            'liquido': locale.currency(valores['liquido'], grouping=True)
        }
        for data_pagamento, valores in sorted_data
    ]

    return render_template('index.html', data=formatted_data)

if __name__ == '__main__':
    app.run(debug=True)
