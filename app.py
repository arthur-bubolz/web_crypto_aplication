from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from prophet import Prophet
from markupsafe import Markup

# bibliotecas da APIs
from pycoingecko import CoinGeckoAPI
import pandas as pd

# Inicializa o aplicativo Flask
app = Flask(__name__)

# Inicializa o Socket.IO
socketio = SocketIO(app,async_mode='threading')

# Inicializa a API CoinGecko
cg = CoinGeckoAPI()
print(cg.ping())

# Rota raiz que lida com solicitações GET e POST
@app.route('/', methods=['GET', 'POST'])
def infos():
    if request.method == 'POST':
        form_name = request.form.get('form_type')
        print(form_name)
        if form_name == 'Obter Informações!':
            coin_selected = request.form['coin']
            
            # VS currencies
            vsCurrencies = ['usd', 'eur', 'brl']

            # Requisição de últimas informações da crypto selecionada
            complexPriceRequest = cg.get_price(ids=coin_selected,
                                vs_currencies=vsCurrencies,
                                include_market_cap=True,
                                include_24hr_vol=True,
                                include_24hr_change=True,
                                include_last_updated_at=True)
            
            # Transformando o JSON em um DataFrame
            df = pd.DataFrame.from_dict(complexPriceRequest, orient='index')

            # Transpondo o DataFrame para que as moedas se tornem índices
            df = df.transpose()

            return render_template('index.html', selected_coin=coin_selected, tables = df.to_html(escape=False), titles=df.columns.values)
        
        #tratamento caso o usuário selecionar a opção de obter conversão
        elif form_name == 'Obter Conversão!':
            coin_selected_1_in = request.form['coin_1']
            coin_selected_2_out = request.form['coin_2']
            
            vsCurrencies = ['usd']
            request_base = cg.get_price(ids = coin_selected_1_in, vs_currencies = vsCurrencies)[coin_selected_1_in]['usd']
            request_out = cg.get_price(ids = coin_selected_2_out, vs_currencies = vsCurrencies)[coin_selected_2_out]['usd']
            
            output_value = request_base/request_out
            
            #tag HTML aqui
            tag_html = f"<div><p>1 unidade de {coin_selected_1_in} compra: {output_value} de {coin_selected_2_out}</p></div>"

            # Marcando a tag HTML como segura para renderização
            safe_html = Markup(tag_html)
            
            return render_template('index.html', safe_html=safe_html)            
    # Se for um GET ou a primeira renderização, apenas exibir a página sem informações.
    return render_template('index.html')

@app.route('/historical_data', methods=['GET', 'POST'])
def historical_data():
    if request.method == 'POST':
        coin_selected = request.form['coin']
        
        #currency selecionada
        currency_selc = request.form['currency']
        
        #tempo selecionado
        time_select = request.form['time_back']
        
        # Determinar a data final como a data atual
        data_final = datetime.now()

        # Determinar a data inicial como 30 dias antes da data final
        data_inicial = data_final - timedelta(days=int(time_select))

        # Converter as datas para timestamps UNIX (tempo em milisegundos)
        data_inicial_timestamp = int(data_inicial.timestamp())
        data_final_timestamp = int(data_final.timestamp())


        # Obter os dados históricos de preços
        historico_precos = cg.get_coin_market_chart_range_by_id(
            id=coin_selected,  # Você pode iterar sobre as criptomoedas desejadas
            vs_currency=currency_selc,
            from_timestamp=data_inicial_timestamp,
            to_timestamp=data_final_timestamp,
            localization=False
        )

        # O resultado incluirá dados de preço, volume, etc.
        # processar os dados conforme necessário

        coinDataFrame_2 = pd.DataFrame.from_dict(historico_precos)
        coinDataFrame_2.tail()

        # Funções para extração dos dados diários da cotação da moeda escolhida
        def extrair_segundo_valor(lista):
            return lista[1] if len(lista) > 1 else None

        def extrair_primeiro_valor_e_normalizar(lista):
            return datetime.fromtimestamp((lista[0]/1000)) if len(lista) > 1 else None

        novo_tempo = []
        for i in range(len(coinDataFrame_2)):
            valor = extrair_primeiro_valor_e_normalizar(coinDataFrame_2['prices'][i])
            novo_tempo.append(valor)

        for coluna in coinDataFrame_2:
            coinDataFrame_2[coluna] = coinDataFrame_2[coluna].apply(extrair_segundo_valor)

        coinDataFrame_2['time'] = novo_tempo
        coinDataFrame_2 = coinDataFrame_2[::24]
        
        # Criando um gráfico de linha
        plt.figure(figsize=(10, 6))
        plt.plot(coinDataFrame_2['time'], coinDataFrame_2['prices'], linestyle='-', color='b')
        plt.title('Preço em relação ao tempo')
        plt.xlabel('Tempo')
        plt.ylabel('Preço')
        plt.grid(True)
        
        # Converter o gráfico para uma imagem em bytes
        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        
        # Converter a imagem em base64 para incorporá-la no HTML
        img_base64 = base64.b64encode(img.read()).decode()
        
        prediction_df = coinDataFrame_2[['time','prices']]
        novo_nome_colunas = {'time': 'ds', 'prices': 'y'}
        prediction_df = prediction_df.rename(columns=novo_nome_colunas)
        
        #Inicialização da API do Prophet        
        m = Prophet()
        m.fit(prediction_df)
        future = m.make_future_dataframe(periods=int(time_select))   
        forecast = m.predict(future)  
        fig1 = m.plot(forecast)
        
        # Converter o gráfico para uma imagem em bytes
        img_2 = BytesIO()
        plt.savefig(img_2, format='png')
        img_2.seek(0)

        # Converter a imagem em base64 para incorporá-la no HTML
        img_2_base64 = base64.b64encode(img_2.read()).decode()
           
        return render_template('historical_data.html', selected_coin=coin_selected, img_base64=img_base64, img_2=img_2_base64, n_dias=time_select)
    
    return render_template('historical_data.html')


if __name__ == '__main__':
    socketio.run(app, debug=True)
