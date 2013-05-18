sgdbot.py
=========

Stop loss/Start gain dialog interactive bot for goxtool Mt.Gox trading bot framework
Features:

- Ability to set or change stop loss/start gain orders during runtime. No need to edit files or reload strategy (very useful)! (press s to open stop loss dialog or press g to open start gain dialog)
- Added autofilling full wallet amount for stop loss (BTC wallet) and start gain (FIAT wallet). Select 0 for volumes to use full wallet amount
- For easier start gain, its volume setting is in FIAT, not BTC (_this is for start gain only_)
- Automatically selects to stop loss when there is at least 0.01 BTC in wallet (minimum Mt. Gox amount for trading) and only selects start gain when BTC wallet is empty and FIAT is filled with any amount
- Actively informs in goxtools's debug dialog, stop loss or start gain enablement and order filling status. Great to remind you when the bot is enabled and how was the order filled.
- Informs Mt.Gox charged fee for Stop loss/Start gain filled order

Note: This fork removed trailing stop from the original code

To run this bot get goxtool at https://github.com/prof7bit/goxtool
