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
    print("Received Signal.......")
    passphrase = data['passphrase']
    if passphrase != SECRET_KEY:
        print("Invalid SECRET KEY/PASSPHRASE")
        return {
        "code" : "fail",
        "message" : "denied : nice try."
        }
    print("Valid SECRET KEY/PASSPHRASE")
    
    currentmode = client.futures_get_position_mode()
    if currentmode['dualSidePosition'] != True :
        print("Position mode: OneWay Mode")
        print("Operation Abort!")
        return {
        "code" : "fail",
        "message" : "abort : please turn on hedge mode."
        }
    print("Position mode: Hedge Mode")
    
    if ORDER_ENABLE=='TRUE':
        action = data['side']

    else:
        action = 'test'
 
    amount = data['amount']
    symbol = data['symbol']
    lev = data['leverage']
    
    #separate amount type
    fiat=0
    usdt=0
    percent=0    

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
   
    bid = 0
    ask = 0
    new_balance=0
    posiAmt = 0
    unpnl = 0
    min_balance=0
    usdt = float(usdt)
    lev = int(lev)
    
    #check USDT Balance
    balance_index=0
    balance_list=client.futures_account_balance()
    for i in range(0,(len(balance_list)-1),1):    
        #print("asset=",balance_list[i]['asset'])
        if balance_list[i]['asset']=='USDT':
            balance_index=i
            break
    balance_key='balance'    
    balance=float(client.futures_account_balance()[balance_index][balance_key])        
    print("Balance = ",balance," USDT")

    #print(FREEBALANCE[0])
    if FREEBALANCE[0]=='$':
        min_balance=float(FREEBALANCE[1:len(FREEBALANCE)])
        print("FREEBALANCE=",min_balance," USDT")
    #Alertline if balance<min_balance
    if balance<min_balance:  
        print("MARGIN-CALL")
        msg ="BINANCE:\n" + "BOT       :" + BOT_NAME + "\n!!!WARNING!!!\nAccount Balance<"+ str(min_balance)+ " USDT"+"\nAccount Balance:"+ str(balance) + " USDT" + "\n!!!!MARGIN-CALL!!!!"
        r = requests.post(url, headers=headers, data = {'message':msg})
        return {
        "code" : "fail",
        "message" : "Margin-CALL"
        }
    
    bid = float(client.futures_orderbook_ticker(symbol =symbol)['bidPrice'])
    ask = float(client.futures_orderbook_ticker(symbol =symbol)['askPrice'])
    
    #List of action OpenLong=BUY, OpenShort=SELL, CloseLong=SELL, CloseShort=BUY
    #CloseShort/BUY
    if action == "CloseShort":
        posiAmt = float(client.futures_position_information(symbol=symbol)[2]['positionAmt'])
        print("Short Position amount:",float(client.futures_position_information(symbol=symbol)[2]['positionAmt']),COIN)
        unpnl = float(client.futures_position_information(symbol=symbol)[2]['unRealizedProfit'])
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
            print("Confirm:", symbol,":",action, ":Qty=",qty_close, " ", COIN,":USDT=", round(usdt,3))
            leverage = float(client.futures_position_information(symbol=symbol)[2]['leverage'])              
            entryP=float(client.futures_position_information(symbol=symbol)[2]['entryPrice'])
            close_SELL = client.futures_create_order(symbol=symbol, positionSide='SHORT', side='BUY', type='MARKET', quantity=qty_close*-1)                        
            time.sleep(1)    
            #success close sell, push line notification                    
            new_balance=float(client.futures_account_balance()[balance_index][balance_key])
            ROI= (entryP-bid)/entryP*100*lev     
            print("Margin %ROE=",ROI)            
            #success close buy, push line notification                    
            msg ="BINANCE:\n" + "BOT         : " + BOT_NAME + "\nCoin        : " + COIN + "/USDT" + "\nStatus      : " + action + "[BUY]" + "\nAmount      : " + str(qty_close*-1) + " "+  COIN +"("+str(round((qty_close*bid*-1),2))+" USDT)" + "\nPrice        :" + str(bid) + " USDT" + "\nLeverage    : " + str(lev) + "\nRealized P/L: " + str(round(unpnl,2)) + " USDT" + "\n%ROE       :"+ str(round(ROI,2)) + "%"+"\nBalance   :" + str(round(new_balance,2)) + " USDT"
            r = requests.post(url, headers=headers, data = {'message':msg})
            print(symbol,": Close Short Position Excuted")
    
    #CloseLong/SELL
    if action == "CloseLong":
        posiAmt = float(client.futures_position_information(symbol=symbol)[1]['positionAmt'])
        print("Long Position amount:",float(client.futures_position_information(symbol=symbol)[1]['positionAmt']),COIN)
        unpnl = float(client.futures_position_information(symbol=symbol)[1]['unRealizedProfit'])
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
                qty_close= round(fiat,qty_precision)
                usdt=round(fiat*ask,qty_precision)
                print("SELL/CloseLong by @ amount=", fiat, " ", COIN, ": USDT=",round(usdt,3))
            print("Confirm:", symbol,":", action, ": Qty=", qty_close, " ", COIN,":USDT=", round(usdt,3))                    
            leverage = float(client.futures_position_information(symbol=symbol)[1]['leverage'])  
            entryP=float(client.futures_position_information(symbol=symbol)[1]['entryPrice'])
            close_BUY = client.futures_create_order(symbol=symbol, positionSide='LONG', side='SELL', type='MARKET', quantity=qty_close)            
            time.sleep(1)
            #success close sell, push line notification                    
            new_balance=float(client.futures_account_balance()[balance_index][balance_key])
            ROI= (ask-entryP)/entryP*100*lev     
            print("Margin %ROE=",ROI)
            msg ="BINANCE:\n" + "BOT        :  " + BOT_NAME + "\nCoin         : " + COIN + "/USDT" + "\nStatus      : " + action + "[SELL]" + "\nAmount      : " + str(qty_close) + " "+  COIN +"("+str(round((qty_close*ask),2))+" USDT)" + "\nPrice       : " + str(ask) + " USDT" + "\nLeverage    : " + str(lev) + "\nRealized P/L: " + str(round(unpnl,2)) + " USDT" + "\n%ROE       :"+ str(round(ROI,2)) + "%"+"\nBalance   :" + str(round(new_balance,2)) + " USDT"
            r = requests.post(url, headers=headers, data = {'message':msg})
            print(symbol,": Close Long Position Excuted")
        
    #OpenLong/BUY
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
        print("Confirm:", symbol,":",action, ":Qty=",Qty_buy, " ", COIN,":USDT=", round(usdt,3))
        Qty_buy = round(Qty_buy,qty_precision)
        print('qty buy : ',Qty_buy)
        client.futures_change_leverage(symbol=symbol,leverage=lev) 
        print('leverage : ',lev)
        order_BUY = client.futures_create_order(symbol=symbol, positionSide='LONG', side='BUY', type='MARKET', quantity=Qty_buy)               
        time.sleep(1)
        #get entry price to find margin value
        entryP=float(client.futures_position_information(symbol=symbol)[1]['entryPrice'])
        print("entryP=",entryP)
        margin=entryP*Qty_buy/lev
        #success openlong, push line notification        
        new_balance=float(client.futures_account_balance()[balance_index][balance_key])
        print("Old Balance=",balance)
        print("New Balance=",new_balance)
        msg ="BINANCE:\n" + "BOT        :" + BOT_NAME + "\nCoin        :" + COIN + "/USDT" + "\nStatus     :" + action + "[BUY]" + "\nAmount  :" + str(Qty_buy) + " "+  COIN +"/"+str(usdt)+" USDT" + "\nPrice       :" + str(bid) + " USDT" + "\nLeverage:" + str(lev) +"\nMargin   :" + str(round(margin,2))+  " USDT"+ "\nBalance   :" + str(round(new_balance,2)) + " USDT"
        r = requests.post(url, headers=headers, data = {'message':msg})
        print(symbol," : Open Long Position Excuted") 
    
    #OpenShort/SELL
    if action == "OpenShort" :                
        qty_precision = 0
        for j in client.futures_exchange_info()['symbols']:
            if j['symbol'] == symbol:
                qty_precision = int(j['quantityPrecision'])
        #check if sell in @ or fiat
        if amount[0]=='@':            
            fiat=float(amount[1:len(amount)])
            Qty_sell= round(fiat,qty_precision)
            usdt=round(fiat*ask,qty_precision)
            print("SELL/SHORT by @ amount=", fiat, " ", COIN, ": USDT=",round(usdt,3))
        if amount[0]=='$':
            usdt=float(amount[1:len(amount)])
            Qty_sell = round(usdt/ask,qty_precision)
            print("SELL/SHORT by USDT amount=", usdt, ": COIN", round(usdt,30))
        print("Confirm:", symbol,":", action, ": Qty=", Qty_sell, " ", COIN,":USDT=", round(usdt,3))
        Qty_sell = round(Qty_sell,qty_precision)
        print('qty sell : ',Qty_sell)
        client.futures_change_leverage(symbol=symbol,leverage=lev)
        print('leverage : ',lev)
        order_SELL = client.futures_create_order(symbol=symbol, positionSide='SHORT', side='SELL', type='MARKET', quantity=Qty_sell)
        time.sleep(1)
        #get entry price to find margin value
        entryP=float(client.futures_position_information(symbol=symbol)[2]['entryPrice'])
        print("entryP=",entryP)
        margin=entryP*Qty_sell/lev
        #success openlong, push line notification        
        new_balance=float(client.futures_account_balance()[balance_index][balance_key])
        print("Old Balance=",balance)
        print("New Balance=",new_balance)
        #success openshort, push line notification        
        msg ="BINANCE:\n" + "BOT        :" + BOT_NAME + "\nCoin        :" + COIN + "/USDT" + "\nStatus     :" + action + "[SHORT]" + "\nAmount  :" + str(Qty_sell) + " "+  COIN +"/"+str(usdt)+" USDT" + "\nPrice       :" + str(bid) + " USDT" + "\nLeverage:" + str(lev) +"\nMargin   :" + str(round(margin,2))+ " USDT"+ "\nBalance   :" + str(round(new_balance,2)) + " USDT"
        r = requests.post(url, headers=headers, data = {'message':msg})
        print(symbol,": Open Short Position Excuted")
    
    #test/Position info
    if action == "test":
        ROIB = 0
        ROIS = 0
        amoutL = float(client.futures_position_information(symbol=symbol)[1]['positionAmt'])
        amoutS = float(client.futures_position_information(symbol=symbol)[2]['positionAmt'])
        print("Position info :")  
        print("---------------------------")
        if amoutL > 0 :
            print("Long amount:",float(client.futures_position_information(symbol=symbol)[1]['positionAmt']),COIN)
            entryPB = float(client.futures_position_information(symbol=symbol)[1]['entryPrice'])
            print("Long Entry :",float(client.futures_position_information(symbol=symbol)[1]['entryPrice']))
            print("Long Unrealized PNL:",float(client.futures_position_information(symbol=symbol)[1]['unRealizedProfit']),"USDT")
            if entryPB > 0 :
                ROIB= (ask-entryPB)/entryPB*100*lev     
                print("Long %ROE=",ROIB)
            print("---------------------------")
        if amoutS < 0 :
            print("Short amount:",float(client.futures_position_information(symbol=symbol)[2]['positionAmt']),COIN)
            entryPS = float(client.futures_position_information(symbol=symbol)[2]['entryPrice'])
            print("Short Entry :",float(client.futures_position_information(symbol=symbol)[2]['entryPrice']))
            print("Short Unrealized PNL:",float(client.futures_position_information(symbol=symbol)[2]['unRealizedProfit']),"USDT")
            if entryPS > 0 :
                ROIS= (entryPS-bid)/entryPS*100*lev     
                print("Short %ROE=",ROIS)   
            print("---------------------------")
        print("If position amount is = your real position in binance you are good to GO!")
        print("If something is off please re-check all Setting.")
        print("---------------------------")
        msg ="BINANCE:\n" + "BOT                 : " + BOT_NAME + "\nPosition info    : " + COIN +"/USDT"+ "\nLong Entry        : "+ str(float(client.futures_position_information(symbol=symbol)[1]['entryPrice'])) +"\nLong amount   : " + str(float(client.futures_position_information(symbol=symbol)[1]['positionAmt'])) + COIN + "(" + str(round((amoutL*ask*),2)) + " USDT)" + "\nUnrealized P/L: " + str(float(client.futures_position_information(symbol=symbol)[1]['unRealizedProfit'])) + " USDT"+ "\n%ROE              : "+ str(round(ROIB,2)) + "%" + "\n         -------------" + "\nShort Entry      : " + str(float(client.futures_position_information(symbol=symbol)[2]['entryPrice']))+ "\nShort amount  : " + str(float(client.futures_position_information(symbol=symbol)[2]['positionAmt']))+ COIN + "(" +str(round((amoutS*bid*-1),2)) + " USDT)"  + "\nUnrealized P/L: "+ str(float(client.futures_position_information(symbol=symbol)[2]['unRealizedProfit'])) +" USDT" + "\n%ROE              : "+ str(round(ROIS,2)) + "%" + "\n         -------------" + "\nBalance   : " + str(round(balance,2)) + " USDT"
        r = requests.post(url, headers=headers, data = {'message':msg})        

    print("----------------------COMPLETED----------------------")
    
    return {
        "code" : "success",
        "message" : "OKi!"
    }

if __name__ == '__main__':
    app.run(debug=True)