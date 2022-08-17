#the following is the cryto trade bot and compatible with the follwing strategy message

#passphrase = input.string(defval='xxxx', title ='Bot Pass',group='═ Bot Setting ═')
#leveragex  = input.int(125,title='leverage',group='═ Bot Setting ═',tooltip='"NOTHING" to do with Position size',minval=1)
#string Alert_OpenLong       = '{"side": "OpenLong", "amount": "@{{strategy.order.contracts}}", "symbol": "{{ticker}}", "passphrase": "'+passphrase+'","leverage":"'+str.tostring(leveragex)+'"}'
#string Alert_OpenShort      = '{"side": "OpenShort", "amount": "@{{strategy.order.contracts}}", "symbol": "{{ticker}}", "passphrase": "'+passphrase+'","leverage":"'+str.tostring(leveragex)+'"}'
#string Alert_LongTP         = '{"side": "CloseLong", "amount": "@{{strategy.order.contracts}}", "symbol": "{{ticker}}", "passphrase": "'+passphrase+'","leverage":"'+str.tostring(leveragex)+'"}'
#string Alert_ShortTP        = '{"side": "CloseShort", "amount": "@{{strategy.order.contracts}}", "symbol": "{{ticker}}", "passphrase": "'+passphrase+'","leverage":"'+str.tostring(leveragex)+'"}'
#var message_closelong       = '{"side": "CloseLong", "amount": "%100", "symbol": "{{ticker}}", "passphrase": "'+passphrase+'","leverage":"'+str.tostring(leveragex)+'"}'
#var message_closeshort      = '{"side": "CloseShort", "amount": "%100", "symbol": "{{ticker}}", "passphrase": "'+passphrase+'","leverage":"'+str.tostring(leveragex)+'"}'
#string Alert_StopLosslong   = '{"side": "CloseLong", "amount": "%100", "symbol": "{{ticker}}", "passphrase": "'+passphrase+'","leverage":"'+str.tostring(leveragex)+'"}'
#string Alert_StopLossshort  = '{"side": "CloseShort", "amount": "%100", "symbol": "{{ticker}}", "passphrase": "'+passphrase+'","leverage":"'+str.tostring(leveragex)+'"}'
#Sample payload = '{"side":"OpenShort","amount":"@0.006","symbol":"BTCUSDTPERP","passphrase":"1945","leverage":"125"}'
#mod and dev by DR.AKN
#Compatible with VXD Cloud Edition Tradingview by Vaz

#feature
import json
import sys
import time
from flask import Flask, request, render_template
from binance.client import Client
from binance.enums import *
import os
import requests

app = Flask(__name__)

API_KEY = str(os.environ['API_KEY'])
API_SECRET = str(os.environ['API_SECRET'])
#TEST_NET = bool(str(os.environ['TEST_NET']))
LINE_TOKEN=str(os.environ['LINE_TOKEN'])
BOT_NAME=str(os.environ['BOT_NAME'])
FREEBALANCE=str(os.environ['FREEBALANCE'])
SECRET_KEY=str(os.environ['SECRET_KEY'])
ORDER_ENABLE=str(os.environ['ORDER_ENABLE'])
#set order enable = FALSE in vars when want to test nonorder api cmd./TRUE for normal operation

#client = Client(API_KEY,API_SECRET,testnet=TEST_NET)
client = Client(API_KEY,API_SECRET)

url = 'https://notify-api.line.me/api/notify'
headers = {'content-type':'application/x-www-form-urlencoded','Authorization':'Bearer '+LINE_TOKEN}

@app.route("/")
def hello_world():
    return render_template('index.html')

@app.route("/webhook", methods=['POST'])
def webhook():
    data = json.loads(request.data)
    print("decoding data...")
    if passphrase != SECRET_KEY:
        print("Invalid SECRET KEY/PASSPHRASE")
        return {
        "code" : "fail",
        "message" : str(data)
        }
    print("Valid SECRET KEY/PASSPHRASE")
    
    if ORDER_ENABLE=='TRUE':
        action = data['side']
        amount = data['amount']
        symbol = data['symbol']
        passphrase = data['passphrase']
        lev = data['leverage']

    else:
        action = 'maintenance mode'
 
    
    
    #separate amount type
    fiat=0
    usdt=0
    percent=0    

    #check if secretkey is valid
    CHmod = client.futures_get_position_mode()
    print("Position mode: Hedge Mode" if CHmod['dualSidePosition'] == True else "Position mode: OneWay Mode")


    #trim PERT from symbol
    if (symbol[len(symbol)-4:len(symbol)]) == "PERP":
        symbol=symbol[0:len(symbol)-4]

    COIN = symbol[0:len(symbol)-4] 

    if amount[0]=='@':
        fiat=float(amount[1:len(amount)])
        print("COIN:",symbol, " : ",action," : amount=",fiat," : leverage=" , lev)
    if amount[0]=='$':
        usdt=float(amount[1:len(amount)])
        print("USDT:",symbol, " : ",action," : amount=",usdt," : leverage=" , lev)
    if amount[0]=='%':
        percent= float(amount[1:len(amount)])
        print("Percent:",symbol, " : ",action," : amount=",percent," : leverage=" , lev)

    print('amount=',amount)
    print('fiat=',fiat)
    print('USDT=',usdt)
    print('Percent=',percent)      


    bid = 0
    ask = 0
    usdt = float(usdt)
    lev = int(lev)

    min_balance=0
    print('show balance list')
    #check USDT Balance
    balance_index=0
    balance_list=client.futures_account_balance()
    print(len(balance_list))
    for i in range(0,(len(balance_list)-1),1):    
        #print("asset=",balance_list[i]['asset'])
        if balance_list[i]['asset']=='USDT':
            balance_index=i
            break
    print("Balance list=",balance_list[balance_index])
    balance_key='withdrawAvailable'    
    balance=float(client.futures_account_balance()[balance_index][balance_key])        

    print("USDT Balance=",balance)
    balance_key='withdrawAvailable'    
    balance=float(client.futures_account_balance()[balance_index][balance_key])

    #print(FREEBALANCE[0])
    if FREEBALANCE[0]=='$':
        min_balance=float(FREEBALANCE[1:len(FREEBALANCE)])
        print("FREEBALANCE=",min_balance)
    #Alertline if balance<min_balance
    if balance<min_balance:            
        msg ="BINANCE:\n" + "BOT       :" + BOT_NAME + "\n!!!WARNING!!!\nAccount Balance<"+ str(min_balance)+ " USDT"+"\nAccount Balance:"+ str(balance) + " USDT"
        r = requests.post(url, headers=headers, data = {'message':msg})

    bid = float(client.futures_orderbook_ticker(symbol =symbol)['bidPrice'])
    ask = float(client.futures_orderbook_ticker(symbol =symbol)['askPrice'])

    #posiAmtL = float(client.futures_position_information(symbol=symbol)[1]['positionAmt'])
    #posiAmtS = float(client.futures_position_information(symbol=symbol)[2]['positionAmt'])
    print("Long Position amount:",float(client.futures_position_information(symbol=symbol)[1]['positionAmt']))
    print("Short Position amount:",float(client.futures_position_information(symbol=symbol)[2]['positionAmt']))

    #List of action OpenLong=BUY, OpenShort=SELL, StopLossLong, StopLossShort, CloseLong=LongTP, CloseShort=ShortTP, CloseLong, CloseShort, 
    #OpenLong/BUY    
    new_balance=0
    #if action == "OpenLong" and usdt>0:
    if action == "OpenLong" :
        qty_precision = 0
        for j in client.futures_exchange_info()['symbols']:
            if j['symbol'] == symbol:
                qty_precision = int(j['quantityPrecision'])
        #check if buy in @ or fiat
        if amount[0]=='@':            
            fiat=float(amount[1:len(amount)])
            Qty_buy=round(fiat,qty_precision)
            usdt=round(fiat*bid,qty_precision)
            print("BUY/LONG by @ amount=", fiat, " ", COIN, ": USDT=",round(usdt,3))
        if amount[0]=='$':
            usdt=float(amount[1:len(amount)])
            Qty_buy = round(usdt/bid,qty_precision)
            print("BUY/LONG by USDT amount=", usdt, ": COIN", round(usdt,30))
        print("CF:", symbol,":",action, ":Qty=",Qty_buy, " ", COIN,":USDT=", round(usdt,3))
        Qty_buy = round(Qty_buy,qty_precision)
        print('qty buy : ',Qty_buy)
        client.futures_change_leverage(symbol=symbol,leverage=lev) 
        print('leverage : ',lev)
        order_BUY = client.futures_create_order(symbol=symbol, positionSide='LONG', side='BUY', type='MARKET', quantity=Qty_buy)        
        print(symbol," : BUY")        
        time.sleep(1)
        #get entry price to find margin value
        entryP=float(client.futures_position_information(symbol=symbol)[1]['entryPrice'])
        print("entryP=",entryP)
        margin=entryP*Qty_buy/lev
        #success openlong, push line notification        
        new_balance=float(client.futures_account_balance()[balance_index][balance_key])
        print("Old Balance=",balance)
        print("New Balance=",new_balance)
        paid=balance-new_balance
        #paid=usdt/lev
        msg ="BINANCE:\n" + "BOT        :" + BOT_NAME + "\nCoin        :" + COIN + "/USDT" + "\nStatus     :" + action + "[BUY]" + "\nAmount  :" + str(Qty_buy) + " "+  COIN +"/"+str(usdt)+" USDT" + "\nPrice       :" + str(bid) + " USDT" + "\nLeverage:" + str(lev) +"\nMargin   :" + str(round(margin,2))+  " USDT"+ "\nPaid        :" + str(round(paid,2)) + " USDT"+ "\nBalance   :" + str(round(new_balance,2)) + " USDT"
        r = requests.post(url, headers=headers, data = {'message':msg})

    #OpenShort/SELL
    #if action == "OpenShort" and usdt > 0:        
    if action == "OpenShort" :                
        qty_precision = 0
        for j in client.futures_exchange_info()['symbols']:
            if j['symbol'] == symbol:
                qty_precision = int(j['quantityPrecision'])
        #check if sell in @ or fiat
        if amount[0]=='@':            
            fiat=float(amount[1:len(amount)])
            Qty_sell= -1*round(fiat,qty_precision)
            usdt=round(fiat*ask,qty_precision)
            print("SELL/SHORT by @ amount=", fiat, " ", COIN, ": USDT=",round(usdt,3))
        if amount[0]=='$':
            usdt=float(amount[1:len(amount)])
            Qty_sell = round(usdt/ask,qty_precision)
            print("SELL/SHORT by USDT amount=", usdt, ": COIN", round(usdt,30))
        print("CF:", symbol,":", action, ": Qty=", Qty_sell, " ", COIN,":USDT=", round(usdt,3))
        Qty_sell = round(Qty_sell,qty_precision)
        print('qty sell : ',Qty_sell)
        client.futures_change_leverage(symbol=symbol,leverage=lev)
        print('leverage : ',lev)

        order_SELL = client.futures_create_order(symbol=symbol, positionSide='SHORT', side='SELL', type='MARKET', quantity=Qty_sell)
        print(symbol,": SELL")
        time.sleep(1)
        #get entry price to find margin value
        entryP=float(client.futures_position_information(symbol=symbol)[2]['entryPrice'])
        print("entryP=",entryP)
        margin=entryP*Qty_sell/lev
        #success openlong, push line notification        
        new_balance=float(client.futures_account_balance()[balance_index][balance_key])
        print("Old Balance=",balance)
        print("New Balance=",new_balance)
        paid=balance-new_balance        #paid=usdt/lev
        #success openshort, push line notification        
        msg ="BINANCE:\n" + "BOT        :" + BOT_NAME + "\nCoin        :" + COIN + "/USDT" + "\nStatus     :" + action + "[SHORT]" + "\nAmount  :" + str(Qty_sell) + " "+  COIN +"/"+str(usdt)+" USDT" + "\nPrice       :" + str(bid) + " USDT" + "\nLeverage:" + str(lev) +"\nMargin   :" + str(round(margin,2))+  " USDT"+ "\nPaid        :" + str(round(paid,2)) + " USDT"+ "\nBalance   :" + str(round(new_balance,2)) + " USDT"
        r = requests.post(url, headers=headers, data = {'message':msg})


    if action == "CloseLong":
        posiAmt = float(client.futures_position_information(symbol=symbol)[1]['positionAmt'])
        if posiAmt > 0.0 :
            qty_precision = 0
            for j in client.futures_exchange_info()['symbols']:
                if j['symbol'] == symbol:
                    qty_precision = int(j['quantityPrecision'])
            print("qty_precision",qty_precision)
            #check if sell in % or $
            if amount[0]=='%':            
                qty_close=round(percent*posiAmt/100,qty_precision)                
                usdt=round(qty_close*ask,qty_precision)                
                print("SELL/CloseLong by % amount=", qty_close, " ", COIN, ": USDT=",round(usdt,3))
            if amount[0]=='$':
                usdt=float(amount[1:len(amount)])                
                qty_close = round(usdt/ask,qty_precision)                
                print("SELL/CloseLong by USDT amount=", usdt, ": COIN", round(qty_close,3))
            if amount[0]=='@':            
                fiat=float(amount[1:len(amount)])
                qty_close= -1*round(fiat,qty_precision)
                usdt=round(fiat*ask,qty_precision)
                print("SELL/CloseLong by @ amount=", fiat, " ", COIN, ": USDT=",round(usdt,3))
            print("CF:", symbol,":", action, ": Qty=", qty_close, " ", COIN,":USDT=", round(usdt,3))                    
            leverage = float(client.futures_position_information(symbol=symbol)[1]['leverage'])  
            entryP=float(client.futures_position_information(symbol=symbol)[1]['entryPrice'])*qty_close
            close_BUY = client.futures_create_order(symbol=symbol, positionSide='LONG', side='SELL', type='MARKET', quantity=qty_close)            
            time.sleep(1)
            #success close sell, push line notification                    
            new_balance=float(client.futures_account_balance()[balance_index][balance_key])
            profit = new_balance-balance
            margin=entryP/leverage
            ROI_val=100*profit/margin 
            ROI=0
            if ROI>=100:
                ROI=round(100-ROI_val,2)
            elif ROI<100:
                ROI=round(ROI_val-100,2)            
            print("Margin ROI%=",ROI)
            msg ="BINANCE:\n" + "BOT       :" + BOT_NAME + "\nCoin       :" + COIN + "/USDT" + "\nStatus    :" + action + "[SELL]" + "\nAmount  :" + str(qty_close) + " "+  COIN +"/"+str(round((qty_close*ask),2))+" USDT" + "\nPrice       :" + str(ask) + " USDT" + "\nLeverage:" + str(lev) + "\nReceive    :" + str(round(profit,2)) + " USDT" + "\nROI           :"+ str(round(ROI,2)) + "%"+"\nBalance   :" + str(round(new_balance,2)) + " USDT"
            r = requests.post(url, headers=headers, data = {'message':msg})
            print(symbol,": CloseLong")

    if action == "CloseShort":
        posiAmt = float(client.futures_position_information(symbol=symbol)[2]['positionAmt'])
        if posiAmt < 0.0 :
            qty_precision = 0
            for j in client.futures_exchange_info()['symbols']:
                if j['symbol'] == symbol:
                    qty_precision = int(j['quantityPrecision'])
            print("qty_precision",qty_precision)
            #check if buy in % or $
            if amount[0]=='%':            
                qty_close=round(percent*posiAmt/100,qty_precision)
                usdt=round(qty_close*bid,qty_precision)
                print("BUY/CloseShort by % amount=", qty_close, " ", COIN, ": USDT=",round(usdt,3))
            if amount[0]=='$':
                usdt=float(amount[1:len(amount)])
                qty_close = -1*round(usdt/bid,qty_precision)
                print("BUY/CloseShort by USDT amount=", usdt, ": COIN", round(qty_close,3))
            if amount[0]=='@':            
                fiat=float(amount[1:len(amount)])
                qty_close = -1*round(fiat,qty_precision)
                usdt=round(fiat*ask,qty_precision)
                print("SELL/CloseShort by @ amount=", fiat, " ", COIN, ": USDT=",round(usdt,3))
            print("CF:", symbol,":",action, ":Qty=",qty_close, " ", COIN,":USDT=", round(usdt,3))
            leverage = float(client.futures_position_information(symbol=symbol)[2]['leverage'])              
            entryP=float(client.futures_position_information(symbol=symbol)[2]['entryPrice'])*qty_close
            close_SELL = client.futures_create_order(symbol=symbol, positionSide='SHORT', side='BUY', type='MARKET', quantity=qty_close*-1)                        
            time.sleep(1)    
            #success close sell, push line notification                    
            new_balance=float(client.futures_account_balance()[balance_index][balance_key])
            profit = new_balance-balance
            margin=-1*entryP/leverage
            ROI_val=100*profit/margin 
            ROI=0
            if ROI>=100:
                ROI=round(100-ROI_val,2)
            elif ROI<100:
                ROI=round(ROI_val-100,2)            
            print("Margin ROI%=",ROI)            
            #success close buy, push line notification                    
            msg ="BINANCE:\n" + "BOT       :" + BOT_NAME + "\nCoin       :" + COIN + "/USDT" + "\nStatus    :" + action + "[BUY]" + "\nAmount  :" + str(qty_close*-1) + " "+  COIN +"/"+str(round((qty_close*bid*-1),2))+" USDT" + "\nPrice       :" + str(bid) + " USDT" + "\nLeverage:" + str(lev) + "\nReceive    :" + str(round(profit,2)) + " USDT" + "\nROI           :"+ str(round(ROI,2)) + "%"+"\nBalance   :" + str(round(new_balance,2)) + " USDT"
            r = requests.post(url, headers=headers, data = {'message':msg})
            print(symbol,": CloseShort")

    if action == "test":
        print("TEST! >> Pull position amount")
        print("Long Position amount:",float(client.futures_position_information(symbol=symbol)[1]['positionAmt']),"and should be Matched")
        print("Short Position amount:",float(client.futures_position_information(symbol=symbol)[2]['positionAmt']),"and should be Matched")
        print("If position amount is = your real position in binance you are good to GO!")
        print("If something is off please re-check all Setting.")
        msg ="BINANCE:\n" + "BOT       :" + BOT_NAME + "\nTest! \nPull position amount\nLong Position amount:" + str(posiAmtL) + "\nShort Position amount:" + str(posiAmtS) + "\nBalance   :" + str(round(balance,2)) + " USDT"
        r = requests.post(url, headers=headers, data = {'message':msg})        

    print("---------------------------------")

    return {
        "code" : "success",
        "message" : str(data)
    }

if __name__ == '__main__':
    app.run(debug=True)