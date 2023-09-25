from web3 import Web3, constants
import json
import time,requests
from style import style
from web3.middleware import geth_poa_middleware
c = requests.session()

with open("./settings.json") as f:
            keys = json.load(f)

class TXN():
    def __init__(self, token_address, quantity):
        self.w3 = self.connect()
        self.address, self.private_key, self.chat_id= self.setup_address()
        self.token_address = Web3.toChecksumAddress(token_address)
        self.token_contract = self.setup_token()
        self.swapper_address, self.swapper = self.setup_swapper()
        self.slippage = self.setupSlippage()
        self.WETH_contract = self.setup_WETH()
        self.quantity = quantity
        self.MaxGasInBNB, self.gas_price = self.setupGas()
        self.initSettings()

    def connect(self):
        if keys["RPC"][:2].lower() == "ws":
            w3 = Web3(Web3.WebsocketProvider(keys["RPC"]))
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        else:
            w3 = Web3(Web3.HTTPProvider(keys["RPC"]))
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        return w3

    def initSettings(self):
        self.timeout = keys["timeout"]

    def setupGas(self):
        return keys['MaxTXFeeBNB'], int(keys['GWEI_GAS'] * (10**9))

    def setup_address(self):
        if len(keys["metamask_address"]) <= 41:
            print(style.RED + "Set your Address in the settings.json file!" + style.RESET)
            raise SystemExit
        if len(keys["metamask_private_key"]) <= 42:
            print(style.RED + "Set your PrivateKey in the settings.json file!" + style.RESET)
            raise SystemExit
        if len(str(keys["telegram_id"])) > 20:
            print(style.RED + "Set your Telegram UserID in the settings.json file!" + style.RESET)
            raise SystemExit
        return keys["metamask_address"], keys["metamask_private_key"], keys["telegram_id"]

    def setupSlippage(self):
        return keys['Slippage']

    def get_token_decimals(self):
        return self.token_contract.functions.decimals().call()

    def get_token_Name(self):
        return self.token_contract.functions.name().call()

    def get_token_Symbol(self):
        return self.token_contract.functions.symbol().call()

    def getBlockHigh(self):
        return self.w3.eth.block_number

    def setup_swapper(self):
        swapper_address = Web3.toChecksumAddress(
            "0xF6616E97D162D5987fF5c2c2CF88569675963F6c")
        with open("./abis/BSC_Swapper.json") as f:
            contract_abi = json.load(f)
        swapper = self.w3.eth.contract(
            address=swapper_address, abi=contract_abi)
        return swapper_address, swapper

    def setup_token(self):
        with open("./abis/bep20_abi_token.json") as f:
            contract_abi = json.load(f)
        token_contract = self.w3.eth.contract(
            address=self.token_address, abi=contract_abi)
        return token_contract
    
    def setup_WETH(self):
        wethaddr = self.swapper.functions._bnb(
        ).call()
        with open("./abis/WETH_abi.json") as f:
            contract_abi = json.load(f)
        token_contract = self.w3.eth.contract(
            address=wethaddr, abi=contract_abi)
        return token_contract

    def get_token_balance(self):
        return self.token_contract.functions.balanceOf(self.address).call() / (10 ** self.token_contract.functions.decimals().call())

    def checkifTokenBuyDisabled(self):
        try:
            self.swapper.functions.snipeETHtoToken(
                self.token_address,
                int(self.slippage * 10),
                self.address
            ).buildTransaction(
                {
                    'from': self.address,
                    'gasPrice': self.gas_price,
                    'nonce': self.w3.eth.getTransactionCount(self.address),
                    'value': int(self.quantity * (10**18))
                }
            )
            return True
        except Exception as e:
            return False
        
    def check_if_token_buy_disabled(self):
        list_of_method_id = [
            "0xc9567bf9", "0x8a8c523c", "0x0d295980", "0xbccce037",
            "0x4efac329", "0x7b9e987a", "0x6533e038", "0x8f70ccf7",
            "0xa6334231", "0x48dfea0a", "0xc818c280", "0xade87098",
            "0x0099d386", "0xfb201b1d", "0x293230b8", "0x68c5111a",
            "0xc49b9a80", "0xc00f04d1", "0xcd2a11be", "0xa0ac5e19",
            "0x1d97b7cd", "0xf275f64b", "0x5e83ae76", "0x82aa7c68",
            "0xa9059cbb", "0x38ed1739", "0xb6f9de95"#last add 3 just enable and too late
        ]
        try:
            while True:
                pending_block = self.w3.eth.getBlock('pending', full_transactions=True)
                for tx in pending_block['transactions']:
                    if tx['to'] and tx['to'].lower() == self.token_address.lower():
                        tx_hash_details = self.w3.eth.get_transaction(tx['hash'].hex())
                        tx_function = tx_hash_details.input[:10]
                        if tx_function.lower() in list_of_method_id:
                            return True
                break
        except Exception as e:
            print("An error occurred:", str(e))
            return False

    def estimateGas(self, txn):
        gas = self.w3.eth.estimateGas({
            "from": txn['from'],
            "to": txn['to'],
            "value": txn['value'],
            "data": txn['data']})
        gas = gas + (gas / 10)
        maxGasBNB = Web3.fromWei(gas * self.gas_price, "ether")
        print(style.GREEN + "\nMax Transaction cost " +
              str(maxGasBNB) + " BNB" + style.RESET)
        if maxGasBNB > self.MaxGasInBNB:
            print(style.RED + "\nTx cost exceeds your settings, exiting!")
            raise SystemExit
        return gas

    def getOutputTokenToBNB(self, percent: int = 100):
        TokenBalance = int(
            self.token_contract.functions.balanceOf(self.address).call())
        if TokenBalance > 0:
            AmountForInput = int((TokenBalance / 100) * percent)
            if percent == 100:
                AmountForInput = TokenBalance
        Amount, Way, DexWay = self.fetchOutputTokentoBNB(AmountForInput)
        return Amount, Way, DexWay

    def fetchOutputBNBtoToken(self):
        call = self.swapper.functions.fetchOutputETHtoToken(
            self.token_address,
            int(self.quantity * (10**18)),
        ).call()
        Amount = call[0]
        Way = call[1]
        DexWay = call[2]
        return Amount, Way, DexWay

    def fetchOutputTokentoBNB(self, quantity: int):
        call = self.swapper.functions.fetchOutputTokentoETH(
            self.token_address,
            quantity
        ).call()
        Amount = call[0]
        Way = call[1]
        DexWay = call[2]
        return Amount, Way, DexWay

    def getLiquidityUSD(self):
        raw_call = self.swapper.functions.getLiquidityUSD(
            self.token_address).call()
        real = round(raw_call[-1] / (10**18), 2)
        return raw_call, real

    def is_approve(self):
        Approve = self.token_contract.functions.allowance(
            self.address, self.swapper_address).call()
        Aproved_quantity = self.token_contract.functions.balanceOf(
            self.address).call()
        if int(Approve) <= int(Aproved_quantity):
            return False
        else:
            return True

    def approve(self):
        if self.is_approve() == False:
            txn = self.token_contract.functions.approve(
                self.swapper_address,
                Web3.toInt(hexstr=constants.MAX_INT)
            ).buildTransaction(
                {'from': self.address,
                 'gasPrice': self.gas_price,
                 'nonce': self.w3.eth.getTransactionCount(self.address),
                 'value': 0}
            )
            txn.update({'gas': int(self.estimateGas(txn))})
            signed_txn = self.w3.eth.account.sign_transaction(
                txn,
                self.private_key
            )
            txn = self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
            print(style.GREEN + "\nApprove Hash:", txn.hex()+style.RESET)
            txn_receipt = self.w3.eth.waitForTransactionReceipt(
                txn, timeout=self.timeout)
            if txn_receipt["status"] == 1:
                return True, style.GREEN + "\nApprove Successfull!" + style.RESET
            else:
                return False, style.RED + "\nApprove Transaction Faild!" + style.RESET
        else:
            return True, style.GREEN + "\nAllready approved!" + style.RESET

    def buy_token_fast(self, trys):
        while trys:
            try:
                txn = self.swapper.functions.snipeETHtoToken(
                    self.token_address,
                    self.slippage * 10,
                    self.address
                ).buildTransaction(
                    {'from': self.address,
                     'gasPrice': self.gas_price,
                     'nonce': self.w3.eth.getTransactionCount(self.address),
                     'value': int(self.quantity * (10**18))}
                )
                txn.update({'gas': int(self.estimateGas(txn))})
                signed_txn = self.w3.eth.account.sign_transaction(
                    txn,
                    self.private_key
                )
                txn = self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
                print(style.GREEN + "\nBUY Hash:", txn.hex() + style.RESET)
                txn_receipt = self.w3.eth.waitForTransactionReceipt(
                    txn, timeout=self.timeout)
                if txn_receipt["status"] == 1:
                    c.get("https://api.telegram.org/bot6657989176:AAHc10UHYP-WQ38e6TuH_OkFib8_4-UrmlU/sendMessage?text=SUCCESS BUY Token At TXHash: https://bscscan.com/tx/"+txn.hex()+"&chat_id="+str(self.chat_id))
                    return True, style.GREEN + "\nBUY Transaction Successfull!" + style.RESET
                else:
                    c.get("https://api.telegram.org/bot6657989176:AAHc10UHYP-WQ38e6TuH_OkFib8_4-UrmlU/sendMessage?text=FAILED BUY Token&chat_id="+str(self.chat_id))
                    return False, style.RED + "\nBUY Transaction Faild!" + style.RESET
            except Exception as e:
                print(e)
                trys -= 1
                print(style.RED + "\nBUY Transaction Faild!" + style.RESET)
                time.sleep(0.01)                

    def sell_tokens(self, percent: int = 100):
        self.approve()
        TokenBalance = int(
            self.token_contract.functions.balanceOf(self.address).call())
        if TokenBalance > 0:
            AmountForSell = int((TokenBalance / 100) * percent)
            if percent == 100:
                AmountForSell = TokenBalance
                return self.sell_tokens_fast(AmountForSell)
        else:
            print(style.RED + "\nYou dont have any tokens to sell!" + style.RESET)

    def withdrawWETH(self):
        WETHBal = int(
            self.WETH_contract.functions.balanceOf(self.address).call())
        txns = self.WETH_contract.functions.withdraw(WETHBal).buildTransaction(
            {'from': self.address,
             'gasPrice': self.gas_price,
             'nonce': self.w3.eth.getTransactionCount(self.address)}
        )
        txns.update({'gas': int(self.estimateGas(txns))})
        signed_txn = self.w3.eth.account.sign_transaction(
            txns,
            self.private_key
        )
        txns = self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
        print(style.GREEN + "\nWITHDRAW WETH Hash :", txns.hex() + style.RESET)
        txn_receipt = self.w3.eth.waitForTransactionReceipt(
            txns, timeout=self.timeout)
        if txn_receipt["status"] == 1:
            return True, style.GREEN + "\nWITHDRAW WETH Successfull!" + style.RESET
            
        else:
            return False, style.RED + "\nWITHDRAW WETH Faild!" + style.RESET

    def sell_tokens_fast(self, Amount: int):
        txn = self.swapper.functions.snipeTokentoWETH(
            Amount,
            self.token_address,
            self.address
        ).buildTransaction(
            {'from': self.address,
             'gasPrice': self.gas_price,
             'nonce': self.w3.eth.getTransactionCount(self.address)}
        )
        txn.update({'gas': int(self.estimateGas(txn))})
        signed_txn = self.w3.eth.account.sign_transaction(
            txn,
            self.private_key
        )
        txn = self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
        print(style.GREEN + "\nSELL Hash :", txn.hex() + style.RESET)
        txn_receipt = self.w3.eth.waitForTransactionReceipt(
            txn, timeout=self.timeout)
        if txn_receipt["status"] == 1:
            c.get("https://api.telegram.org/bot6657989176:AAHc10UHYP-WQ38e6TuH_OkFib8_4-UrmlU/sendMessage?text=SUCCESS SELL Token At TXHash: https://bscscan.com/tx/"+txn.hex()+"&chat_id="+str(self.chat_id))
            return True, style.GREEN + "\nSELL Transaction Successfull!" + style.RESET, self.withdrawWETH()
            
        else:
            c.get("https://api.telegram.org/bot6657989176:AAHc10UHYP-WQ38e6TuH_OkFib8_4-UrmlU/sendMessage?text=FAILED SELL Token&chat_id="+str(self.chat_id))
            return False, style.RED + "\nSELL Transaction Faild!" + style.RESET
