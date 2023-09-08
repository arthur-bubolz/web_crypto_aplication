from flask import Flask, request, jsonify, render_template

# bibliotecas da APIs
from pycoingecko import CoinGeckoAPI
import pandas as pd

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():

    cg = CoinGeckoAPI()
    print(cg.ping())

    coinList = cg.get_coins_list()
    coinDataFrame = pd.DataFrame.from_dict(coinList).sort_values('id').reset_index(drop=True)
    coins = ['bitcoin','ethereum']

    #VS currencies
    vsCurrencies = ['usd', 'eur', 'brl']

    #requisição de últimas informações das cryptos selecionadas
    complexPriceRequest = cg.get_price(ids = coins,
                            vs_currencies = vsCurrencies,
                            include_market_cap = True,
                            include_24hr_vol = True,
                            include_24hr_change = True,
                            include_last_updated_at = True)
    print(complexPriceRequest)

    api_data = []

    for coin in coins:
        api_data.append({"name": coin, "symbol": coin})


    return render_template('index.html', crypto_data=api_data)

if __name__ == '__main__':

    app.run(debug=True)
