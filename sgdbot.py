"""
a simple stop loss/start gain bot
adjust STOP_PRICE/START_PRICE and STOP_VOLUME/START_VOLUME to your needs.
to reset orders during runtime, press (s) for a new stop order and (g) for a new start gain
The file can be reloaded after editing without restarting goxtool by simply pressing the (l) key.
"""
# Using the global statement
# pylint: disable=W0603
# No exception type(s) specified
# pylint: disable=W0702
# Missing docstring
# pylint: disable=C0111
# Line too long
# pylint: disable=C0301

import curses
import strategy
import goxapi
import goxtool
STDSCR = curses.initscr()

# USD (EUR or other Fiat) price for the sell stop or buy gain
STOP_PRICE = 5.85
START_PRICE = 1500.85

# STOP_VOLUME for how many BTC to sell at or below the stop price
# START_VOLUME for how many _FIAT_ to use for buying BTC at or above the start price
# Select 0 to trade full wallet amount (BTC wallet for stop and FIAT wallet for gain)
STOP_VOLUME = 0
START_VOLUME = 0

# Do not mess with these
TRADE_TYPE = None
STOP_LOSS = "Stop loss"
START_GAIN = "Start gain"
BTC = "BTC"

class Strategy(strategy.Strategy):
    """stop loss/start gain bot"""
    def __init__(self, gox):
        strategy.Strategy.__init__(self, gox)
        gox.history.signal_changed.connect(self.slot_changed)

        self.init = False
        self.got_wallet = False
        self.already_executed = False

        self.user_currency = gox.currency
        self.total_filled = 0 
        self.btc_wallet = 0
        self.fiat_wallet = 0

    def slot_changed(self, history, _no_data):
        """price history has changed (new trades in history)"""
        global TRADE_TYPE

        if self.already_executed:
            Strategy.end_bot(self)
            return
        
        if not self.init:
            try:
                self.debug("Retrieving wallet data...")
                self.btc_wallet = goxapi.int2float(self.gox.wallet[BTC], BTC)
                self.fiat_wallet = goxapi.int2float(self.gox.wallet[self.user_currency], self.user_currency)        
            except:
                self.debug("Could not retrieve wallet data, retrying...")
                return
            else:
                self.init = True        
                Strategy.begin_bot(self)
        else:
                        
            # main loop
            last_candle = history.last_candle()
          
            if not last_candle:
                self.debug("Could retrieve candle data from goxtool, retrying...")
            else:
                price_last = goxapi.int2float(last_candle.cls, self.user_currency)

                if self.btc_wallet >= 0.01:
                    TRADE_TYPE = STOP_LOSS
                else:
                    TRADE_TYPE = START_GAIN

                vol, _no_data, prc, _no_data, _no_data = Strategy.active_msg(self, TRADE_TYPE)

                if TRADE_TYPE == STOP_LOSS and price_last <= STOP_PRICE:
                    self.gox.sell(0, int(vol * 1e8))
                    self.debug("  *** Market order fired: SELL %.8f at %f" % (vol, prc))
                    self.already_executed = True

                if TRADE_TYPE == START_GAIN and price_last >= START_PRICE:
                    self.gox.buy(0, int((vol / prc) * 1e8))
                    self.debug("  *** Market order fired: BUY %f at %.8f" % (vol, prc))
                    self.already_executed = True
 

    def slot_trade(self, gox, (date, price, volume, typ, own)):
        """a trade message has been received"""
        global TRADE_TYPE

        if not own:
            return

        if own and self.already_executed == False:
            self.already_executed = True
            TRADE_TYPE = None
            return
           
        vol, trade_currency, prc, _no_data, trade_asset = Strategy.set_trade(self, TRADE_TYPE)
       
        vol = goxapi.int2float(volume, BTC) 
        prc = goxapi.int2float(price, self.gox.currency)
        
        if TRADE_TYPE == STOP_LOSS:
            filled = prc * vol
        elif TRADE_TYPE == START_GAIN:
            filled = vol
            vol = prc * filled            

        self.total_filled += filled
        
        self.debug("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        self.debug("                                                                                 ")
        self.debug("  %s filled: VOL %.8f %s at %.5f %s/BTC (filled %.8f %s)"
        % (TRADE_TYPE, vol, trade_currency, prc, self.user_currency, filled, trade_asset))      
        self.debug("                                                                                 ")
        self.debug("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")


    def begin_bot(self):
        global STOP_VOLUME
        global START_VOLUME
        
        if not STOP_VOLUME:
            STOP_VOLUME = self.btc_wallet

        if not START_VOLUME:
            START_VOLUME = self.fiat_wallet

        self.debug("##################################################################################")
        self.debug("                                                                                  ")
        self.debug("  Enabling Stop loss/Start gain bot                                               ")
        self.debug("                                                                                  ")
        self.debug("  Initalizing settings from file...                                               ")
        self.debug("                                                                                  ")
        self.debug("   Stop loss: %.8f BTC @ %.5f %s/BTC (total %.5f %s)"
        % (STOP_VOLUME, STOP_PRICE, self.user_currency, float(STOP_PRICE * STOP_VOLUME), self.user_currency))
        self.debug("  Start gain: %.5f %s @ %.5f %s/BTC (total %.8f BTC)"
        % (START_VOLUME, self.user_currency, START_PRICE, self.user_currency, float(START_VOLUME / START_PRICE)))
        self.debug("                                                                                  ")
        self.debug("##################################################################################")         


    def active_msg(self, set_trade):

        vol, trade_currency, prc, total, trade_asset = Strategy.set_trade(self, set_trade)

        self.debug("**********************************************************************************")
        self.debug("                                                                                  ")
        self.debug("                               %s ACTIVE                                          "
        % (TRADE_TYPE))      
        self.debug("                                                                                  ")
        self.debug("         VOL %.8f %s @ %.5f %s/BTC (total %.8f %s)" 
        % (vol, trade_currency, prc, self.user_currency, total, trade_asset))      
        self.debug("                                                                                  ")
        self.debug("**********************************************************************************")
        
        return vol, trade_currency, prc, total, trade_asset


    def set_trade(self, set_trade):

        if set_trade == STOP_LOSS:
            trade_currency = BTC
            trade_asset = self.user_currency

            vol = STOP_VOLUME
            prc = STOP_PRICE
            total = float(prc * vol)
        elif set_trade == START_GAIN:
            trade_currency = self.user_currency
            trade_asset = BTC
            vol = START_VOLUME
            prc = START_PRICE
            total = float(vol / prc)
        else:
            return

        return vol, trade_currency, prc, total, trade_asset


    def slot_keypress(self, gox, key):
        global TRADE_TYPE
        global STOP_PRICE
        global STOP_VOLUME
        global START_PRICE
        global START_VOLUME

        if not self.init:
            self.debug("Bot not initialized!")
            return
        
        key = chr(key)

        if key == "s":
            TRADE_TYPE = STOP_LOSS
            dialog = NewOrder(STDSCR, self.gox, curses.color_pair(7), TRADE_TYPE)
            dialog.modal()
            prc, vol = dialog.do_submit(dialog.price, dialog.volume)
            
            if prc:
                STOP_PRICE = prc
            if vol:
                STOP_VOLUME = vol
            if vol == 0:
                STOP_VOLUME = self.btc_wallet
                    
        elif key == "g":
            TRADE_TYPE = START_GAIN 
            dialog = NewOrder(STDSCR, self.gox, curses.color_pair(6), TRADE_TYPE)
            dialog.modal()
            prc, vol = dialog.do_submit(dialog.price, dialog.volume)
            
            if prc:
                START_PRICE = prc
            if vol:
                START_VOLUME = vol
            if vol == 0:
                START_VOLUME = self.fiat_wallet
        
        else:
            return
        
        vol, trade_currency, prc, total, trade_asset = Strategy.set_trade(self, TRADE_TYPE)

        self.debug("##################################################################################")
        self.debug("                                                                                  ")
        self.debug("  %s set: VOL %.8f %s @ %.5f %s/BTC (total %.8f %s)"
        % (TRADE_TYPE, vol, trade_currency, prc, self.user_currency, total, trade_asset))
        self.debug("                                                                                  ")
        self.debug("##################################################################################") 


    def end_bot(self):
        if TRADE_TYPE == STOP_LOSS:
            volume_for_fee = goxapi.int2float(self.gox.wallet[self.user_currency], self.user_currency)
        elif TRADE_TYPE == START_GAIN:
            volume_for_fee = goxapi.int2float(self.gox.wallet[BTC], BTC)
        else:
            self.debug(" *** A trade was manually made by user. Bot automatically disabled *** ")
            return

        vol, trade_currency, prc, _no_data, trade_asset = Strategy.set_trade(self, TRADE_TYPE)
        fee = self.total_filled - volume_for_fee

        if fee > 0:

            self.debug("#########################################################@##########################")
            self.debug("                                                                                    ")
            self.debug("  Stop loss/start gain bot is disabled                                              ")
            self.debug("                                                                                    ")
            self.debug("  %s order filled: %.8f %s at %.5f %s/BTC (total filled %.8f %s)"
            % (TRADE_TYPE, vol,  trade_currency, prc, self.user_currency, self.total_filled, trade_asset))
            self.debug("  Mt.Gox fee: %.8f %s"
            % (fee, trade_asset))  
            self.debug("  Press (l) to reload strategy                                                      ")
            self.debug("                                                                                    ")
            self.debug("###############################################################@####################")


class NewOrder(goxtool.DlgNewOrder):
    def __init__(self, stdscr, gox, color, msg):
        goxtool.DlgNewOrder.__init__(self, stdscr, gox, color, msg)
        self.price = 0
        self.volume = 0
    
    def do_submit(self, price, volume):
        self.price =  price
        self.volume = volume
        return self.price, self.volume