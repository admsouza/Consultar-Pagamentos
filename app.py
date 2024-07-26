from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

API_URL = 'https://sagresonline.tce.pb.gov.br/api/v2/municipal/execucao-orcamentaria/pagamentos'

@app.route('/', methods=['GET', 'POST'])
def consult_payments():
    data = []
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

            # Filtra apenas os dados desejados
            if isinstance(api_data, list):
                data = [
                    {
                        'dadosPrincipais': item.get('dadosPrincipais', {}),
                        'dadosPagamento': item.get('dadosPagamento', {})
                    }
                    for item in api_data
                ]
            else:
                return "Erro na resposta da API: Estrutura de dados inesperada.", 500

        except requests.RequestException as e:
            return f"Erro na consulta: {e}", 500

    return render_template('index.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)
