from style import style
from halo import Halo
from time import sleep
import json
import argparse
from txns import TXN
import requests

ascii = """
  _____                _       ______              
 |  __ \              | |     |  ____|             
 | |__) |_ _ _ __   __| | __ _| |____   _____ _ __ 
 |  ___/ _` | '_ \ / _` |/ _` |  __\ \ / / _ \ '__|
 | |  | (_| | | | | (_| | (_| | |___\ V /  __/ |   
 |_|   \__,_|_| |_|\__,_|\__,_|______\_/ \___|_| 

 Telegram: t.me/PESBOTs                                                        
"""

parser = argparse.ArgumentParser(
    description='Set your Token and Amount example: "run.py -t 0xF6616E97D162D5987fF5c2c2CF88569675963F6c -a 0.2"')
parser.add_argument(
    '-t', '--token', help='str, Token for snipe e.g. "-t 0xF6616E97D162D5987fF5c2c2CF88569675963F6c"')
parser.add_argument('-a', '--amount', default=0,
                    help='float, Amount in Bnb to snipe e.g. "-a 0.1"')
parser.add_argument('-tx', '--txamount', default=1, nargs="?", const=1, type=int,
                    help='int, how mutch tx you want to send? It Split your BNB Amount in e.g. "-tx 5"')
parser.add_argument('-sp', '--sellpercent', default=100, nargs="?", const=1, type=int,
                    help='int, how mutch tokens you want to sell? Percentage e.g. "-sp 80"')
parser.add_argument('-nb', '--nobuy', action="store_true",
                    help='No Buy, Skipp buy, if you want to use only TakeProfit/StopLoss/TrailingStopLoss')
parser.add_argument('-tp', '--takeprofit', default=0, nargs="?", const=True,
                    type=int, help='int, Percentage TakeProfit from your input BNB amount "-tp 50" ')
parser.add_argument('-sl', '--stoploss', default=0, nargs="?", const=True, type=int,
                    help='int, Percentage Stop loss from your input BNB amount "-sl 50" ')
parser.add_argument('-tsl', '--trailingstoploss', default=0, nargs="?", const=True,
                    type=int, help='int, Percentage Trailing-Stop-loss from your first Quote "-tsl 50" ')
parser.add_argument('-wb', '--awaitBlocks', default=0, nargs="?", const=True,
                    type=int, help='int, Await Blocks before sending BUY Transaction "-wb 5" ')
parser.add_argument('-cc', '--checkcontract',  action="store_true",
                    help='Check is Contract Verified and Look for some Functions.')
parser.add_argument('-so', '--sellonly',  action="store_true",
                    help='Sell all your Tokens from given address')
parser.add_argument('-bo', '--buyonly',  action="store_true",
                    help='Buy Tokens with from your given amount')
parser.add_argument('-cl', '--checkliquidity',  action="store_true",
                    help='with this arg you use liquidityCheck')
parser.add_argument('-r', '--retry', default=9999999999999999999999999, nargs="?", const=True, type=int,
                    help='with this arg you retry automatically if your tx failed, e.g. "-r 5" or "--retry 5" for max 5 Retrys')
parser.add_argument('-sec', '--SwapEnabledCheck',  action="store_true",
                    help='this argument for automatically swap if owner enable swap/trade')
args = parser.parse_args()


class SniperBot():

    def __init__(self):
        self.parseArgs()
        self.settings = self.loadSettings()
        self.SayWelcome()

    def loadSettings(self):
        with open("settings.json", "r") as settings:
            settings = json.load(settings)
        return settings

    def SayWelcome(self):
        self.TXN = TXN(self.token, self.amountForSnipe)
        print(style().YELLOW + ascii + style().RESET)
        print(style().GREEN + """Attention, DWYOR !!!""" + style().RESET)
        print(style().GREEN +
              "Start Sniper Tool with following arguments:" + style().RESET)
        print(style().BLUE + "---------------------------------" + style().RESET)
        print(style().YELLOW + "Amount for Buy:", style().GREEN +
              str(self.amount) + " BNB" + style().RESET)
        print(style().YELLOW + "Token to Interact :",
              style().GREEN + str(self.token) + style().RESET)
        print(style().YELLOW + "Token Name:",
              style().GREEN + str(self.TXN.get_token_Name()) + style().RESET)
        print(style().YELLOW + "Token Symbol:",
              style().GREEN + str(self.TXN.get_token_Symbol()) + style().RESET)
        print(style().YELLOW + "Transaction to send:",
              style().GREEN + str(self.tx) + style().RESET)
        print(style().YELLOW + "Amount per transaction :", style().GREEN +
              str("{0:.8f}".format(self.amountForSnipe)) + style().RESET)
        print(style().YELLOW + "Await Blocks before buy :",
              style().GREEN + str(self.wb) + style().RESET)

        if self.tsl != 0:
            print(style().YELLOW + "Trailing Stop loss Percent :",
                  style().GREEN + str(self.tsl) + style().RESET)
        if self.tp != 0:
            print(style().YELLOW + "Take Profit Percent :",
                  style().GREEN + str(self.tp) + style().RESET)
        if self.sl != 0:
            print(style().YELLOW + "Stop loss Percent :",
                  style().GREEN + str(self.sl) + style().RESET)
        print(style().BLUE + "---------------------------------" + style().RESET)

    def parseArgs(self):
        self.token = args.token
        if self.token == None:
            print(
                style.RED+"Please Check your Token argument e.g. -t 0xF6616E97D162D5987fF5c2c2CF88569675963F6c -sec")
            print("exit!")
            raise SystemExit

        self.amount = args.amount
        if args.nobuy != True:
            if not args.sellonly:
                if self.amount == 0:
                    print(style.RED+"Please Check your Amount argument e.g. -a 0.01")
                    print("exit!")
                    raise SystemExit

        self.tx = args.txamount
        self.amountForSnipe = float(self.amount) / float(self.tx)
        self.wb = args.awaitBlocks
        self.tp = args.takeprofit
        self.sl = args.stoploss
        self.tsl = args.trailingstoploss
        self.cl = args.checkliquidity
        self.stoploss = 0
        self.takeProfitOutput = 0

    def calcProfit(self):
        if self.amountForSnipe == 0.0:
            self.amountForSnipe = self.TXN.getOutputTokenToBNB(percent=args.sellpercent)[
                0] / (10**18)
        a = ((self.amountForSnipe * self.tx) * self.tp) / 100
        b = a + (self.amountForSnipe * self.tx)
        return b

    def calcloss(self):
        if self.amountForSnipe == 0.0:
            self.amountForSnipe = self.TXN.getOutputTokenToBNB(percent=args.sellpercent)[
                0] / (10**18)
        a = ((self.amountForSnipe * self.tx) * self.sl) / 100
        b = (self.amountForSnipe * self.tx) - a
        return b

    def calcNewTrailingStop(self, currentPrice):
        a = (currentPrice * self.tsl) / 100
        b = currentPrice - a
        return b

    def awaitBuy(self):
        spinner = Halo(text='await Buy', spinner='dots')
        spinner.start()
        for i in range(self.tx):
            spinner.start()
            self.TXN = TXN(self.token, self.amountForSnipe)
            tx = self.TXN.buy_token_fast(args.retry)
            spinner.stop()
            print(tx[-1])
            if tx[0] != True:
                raise SystemExit

    def awaitSell(self):
        spinner = Halo(text='await Sell', spinner='dots')
        spinner.start()
        self.TXN = TXN(self.token, self.amountForSnipe)
        tx = self.TXN.sell_tokens(args.sellpercent)
        spinner.stop()
        print(tx[1])
        if tx[0] != True:
            raise SystemExit

    def awaitApprove(self):
        spinner = Halo(text='await Approve', spinner='dots')
        spinner.start()
        self.TXN = TXN(self.token, self.amountForSnipe)
        tx = self.TXN.approve()
        spinner.stop()
        print(tx[1])
        if tx[0] != True:
            raise SystemExit

    def awaitBlocks(self):
        spinner = Halo(text='await Blocks', spinner='dots')
        spinner.start()
        waitForBlock = self.TXN.getBlockHigh() + self.wb
        while True:
            sleep(0.01)
            if self.TXN.getBlockHigh() > waitForBlock:
                spinner.stop()
                break
        print(style().GREEN+"[DONE] Wait Blocks finish!")

    def CheckVerifyCode(self):
        while True:
            req = requests.get(
                f"https://api.bscscan.com/api?module=contract&action=getsourcecode&address={self.token}&apikey=3P7Z63P7FVU8FB4SATGGBD6T8SHWEDDREM")
            if req.status_code == 200:
                getsourcecode = req.text.lower()
                jsonSource = json.loads(getsourcecode)
                if not "MAX RATE LIMIT REACHED".lower() in str(jsonSource["result"]).lower():
                    if not "NOT VERIFIED".lower() in str(jsonSource["result"]).lower():
                        print(style().GREEN +"[CheckContract] IS Verfied")
                        for BlackWord in self.settings["cc_BlacklistWords"]:
                            if BlackWord.lower() in getsourcecode:
                                print(
                                    style().RED+f"[CheckContract] BlackWord {BlackWord} FOUND, Exit!")
                                raise SystemExit
                        print(style().GREEN +
                              "[CheckContract] No known abnormalities found.")
                        break
                    else:
                        print(
                            style().RED+"[CheckContract] Code Not Verfied, Can't check, Exit!")
                        raise SystemExit
                else:
                    print("Max Request Rate Reached, Sleep 5sec.")
                    sleep(5)
                    continue
            else:
                print("BSCScan.org Request Faild, Exiting.")
                raise SystemExit

    def awaitLiquidity(self):
        spinner = Halo(text='await Liquidity and now is Block: '+str(self.TXN.w3.eth.get_block('latest').number), spinner='dots')
        spinner.start()
        while True:
            sleep(0.05)
            try:
                self.TXN.fetchOutputBNBtoToken()[0]
                spinner.text = 'await Liquidity and now is Block: ' + str(self.TXN.w3.eth.get_block('latest').number)
                break
            except Exception as e:
                spinner.text = 'await Liquidity and now is Block: ' + str(self.TXN.w3.eth.get_block('latest').number)
                if "UPDATE" in str(e):
                    print(e)
                    raise SystemExit
                continue
        spinner.stop()
        print(style().GREEN+"[DONE] Liquidity is Added!" + style().RESET)

    def fetchLiquidity(self):
        liq = self.TXN.getLiquidityUSD()[1]
        print(style().GREEN+"[LIQUIDTY] Current Token Liquidity:",
              round(liq, 3), "USD" + style().RESET)
        if float(liq) < float(self.settings["MinLiquidityUSD"]):
            print(style.RED+"[LIQUIDTY] <- TO SMALL, EXIT!")
            raise SystemExit
        return True

    def awaitEnabledBuy(self):
        spinner = Halo(text='Awaiting Dev Enables Swapping and now is Block: '+str(self.TXN.w3.eth.get_block('latest').number), spinner='dots')
        spinner.start()
        while True:
            sleep(0.02)
            spinner.text='Awaiting Dev Enables Swapping and now is Block: '+str(self.TXN.w3.eth.get_block('latest').number)
            try:
                spinner.text='Awaiting Dev Enables Swapping and now is Block: '+str(self.TXN.w3.eth.get_block('latest').number)
                if self.TXN.check_if_token_buy_disabled():
                    break
            except Exception as e:
                spinner.text='Awaiting Dev Enables Swapping and now is Block: '+str(self.TXN.w3.eth.get_block('latest').number)
                if "UPDATE" in str(e):
                    print(e)
                    raise SystemExit
                continue
        spinner.stop()
        print(style().GREEN+"[DONE] Swapping is Enabled!")

    def awaitMangePosition(self):
        highestLastPrice = 0
        if self.tp != 0:
            self.takeProfitOutput = self.calcProfit()
        if self.sl != 0:
            self.stoploss = self.calcloss()
        TokenBalance = round(self.TXN.get_token_balance(), 5)
        while True:
            try:
                sleep(0.9)
                LastPrice = float(
                    self.TXN.getOutputTokenToBNB(args.sellpercent)[0] / (10**18))
                if self.tsl != 0:
                    if LastPrice > highestLastPrice:
                        highestLastPrice = LastPrice
                        self.TrailingStopLoss = self.calcNewTrailingStop(
                            LastPrice)
                    if LastPrice < self.TrailingStopLoss:
                        print(style().GREEN +
                              "[TRAILING STOP LOSS] Triggert!" + style().RESET)
                        self.awaitSell()
                        break

                if self.takeProfitOutput != 0:
                    if LastPrice >= self.takeProfitOutput:
                        print()
                        print(style().GREEN +
                              "[TAKE PROFIT] Triggert!" + style().RESET)
                        self.awaitSell()
                        break

                if self.stoploss != 0:
                    if LastPrice <= self.stoploss:
                        print()
                        print(style().GREEN +
                              "[STOP LOSS] Triggert!" + style().RESET)
                        self.awaitSell()
                        break

                msg = str("Token Balance: " + str("{0:.5f}".format(
                    TokenBalance)) + " | CurrentOutput: "+str("{0:.7f}".format(LastPrice))+"BNB")
                if self.stoploss != 0:
                    msg = msg + " | Stop loss below: " + \
                        str("{0:.7f}".format(self.stoploss)) + "BNB"
                if self.takeProfitOutput != 0:
                    msg = msg + "| Take Profit Over: " + \
                        str("{0:.7f}".format(self.takeProfitOutput)) + "BNB"
                if self.tsl != 0:
                    msg = msg + " | Trailing Stop loss below: " + \
                        str("{0:.7f}".format(self.TrailingStopLoss)) + "BNB"
                print(msg, end="\r")

            except Exception as e:
                if KeyboardInterrupt:
                    raise SystemExit
                print(
                    style().RED + f"[ERROR] {str(e)},\n\nSleeping now 30sec and Reinit RPC!" + style().RESET)
                sleep(30)
                self.TXN = TXN(self.token, self.amountForSnipe)
                continue

        print(style().GREEN +
              "[DONE] Position Manager Finished!" + style().RESET)

    def StartUP(self):
        self.TXN = TXN(self.token, self.amountForSnipe)

        if args.sellonly:
            print("Start SellOnly, for selling tokens!")
            self.awaitApprove()
            if args.SwapEnabledCheck == True:
                self.awaitEnabledBuy()
            if args.sellpercent > 0 and args.sellpercent < 100:
                print(self.TXN.sell_tokens(args.sellpercent)[1])
            else:
                percent = int(input("Enter Percent you want to sell: "))
                print(self.TXN.sell_tokens(percent)[1])
            raise SystemExit

        if args.buyonly:
            print(
                f"Start BuyOnly, buy now with {self.amountForSnipe}BNB tokens!")
            print(self.TXN.buy_token_fast(args.retry)[1])
            raise SystemExit

        if args.nobuy != True:
            self.awaitLiquidity()
            if args.SwapEnabledCheck == True:
                self.awaitEnabledBuy()

        if args.checkcontract:
            self.CheckVerifyCode()

        if self.wb != 0:
            self.awaitBlocks()

        if self.cl == True:
            if self.fetchLiquidity() != False:
                pass

        if args.nobuy != True:
            self.awaitBuy()

        if self.tsl != 0 or self.tp != 0 or self.sl != 0:
            sleep(0.01)
            self.awaitApprove()
            self.awaitMangePosition()

        print(style().GREEN +
              "[DONE] PandaEver Sniper Bot finish!" + style().RESET)


SniperBot().StartUP()
