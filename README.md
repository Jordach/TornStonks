# TornStonks
Python tool that imports stocks via [Tornsy](https://tornsy.com) - no API keys or private information sent out.

License: AGPL

# Guide:
TornStonks was designed to live within your notification tray and generally be out of sight with minimal visual disruption. With that in mind, the application is very simple with it's interface.

## **TornStonks doesn't verify information entered, and can only be considered as guidance. This means gains and losses are entirely virtual and therefore are not realised.**
___
## Main Window:
![Screenshot](other/screenshot_main.png?raw=true)

By default, the way you're going to be interacting with TornStonks is through Notepad, Excel (via exporting CSV files) or a text editor of your choice. However, you can edit the cells such as `Bought Price`, `Shares`, `Gain Alert %`, and `Loss Alert %`. Cells beyond that are considered "non editable" and will update data at 5 seconds past each minute to update the known stock data from [Tornsy](https://tornsy.com). Changes made to the cells mentioned earlier will be saved to your `user_positions.conf` file.

An example file called `user_positions_template.conf` is included, and shows how the layout of each row works.

For example, a configuration file may look like:
```csv
stock,buy,shares,gain,loss
WLT,420.69,1000,5,1
```

Which when expanded to a spreadsheet it should similar to this:

| stock | buy    | shares | gain | loss |
|-------|--------|--------|------|------|
| WLT   | 420.69 | 1000   | 5    | 1    |

It's very simple to work with once you get used to the syntax.

In short, the file is laid out as follows:
```csv
stock,buy,shares,gain,loss
```
In the screenshot above, you may notice that `Bought Price`, `Shares`, `Gain Alert %`, `Loss Alert %` and the row heading are listed, and not editable. Note: The three letter stock acronym is used as the row number replacement and cannot be edited. This is subject to change.

```csv
WLT,420.69,1000,5,1
```
This is stock information, or to break it down per each comma separated value or CSV:
* **WLT**: This is the three letter acronym for the stock you "own".
* **420.69**: This is the price of the stock at purchase time.
* **1000**: This is the number of shares you "own".
* **5**: This is the percentage that a stock must gain in value before you receive a notification.
* **1**: This is the percentage that a stock must lose in value before you receive a notification.

### **WARNING: TornStonks is not responsible for ignoring stop loss alerts.**
___

## Tray Menu:
### This menu can be accessed by right clicking the TornStonks notification tray icon, which produces the following items:
![Screenshot](other/screenshot_tray.png?raw=true)


* Enable / Disable Stock Notifications

This option will enable TornStonks to emit notification sounds. Note: Currently, PyQT5 does not offer a way for silent notifications.

* Time Between Notifications

This slideout menu will contain options to enable how long TornStonks stays silent after it's already sent a notification for. At a maximum, TornStonks will sent three notifications, one for losses, one for profits, and one for buy ins. By default, TornStonks waits 5 minutes. TornStonks will log any user position that exceeds the set loss or gain percentages to a text file that is formatted as `DD-MM-YYYY.txt`.

* Reload User Stock Positions

This option reloads `user_positions.conf` which is included with this repo or binary version. This will reload all stocks "purchased" stored within it. Note: Stocks are considered "purchased" as in, you can use two instances of this tool to play a paper version of the market with wacky values, alongside the real stocks. **This option exists for people who prefer editing their stock data via an external editor.**

* Enable / Disable Automatic Window Resizing

This option forces the window to match the spreadsheet view. This does not respect screen size. By default TornStocks only resizes to the content once on start up and is then disabled.

* Show / Hide TornStonks

This option is practically self explanatory. Clicking the icon in the notification tray will also hide the window, as well as show it. Closing the window will also achieve the same result as PyQT5 does not allow capturing of window minimising events.

* Quit

This is how you exit TornStonks.
___
## Buy In Pricing:

TornStonks can also be used as a simple way to set a way to alert you when the price of a stock has reached a point to buy low at. This can be achieved by the following configuration example:
```csv
stock,buy,shares,gain,loss
IOU,420.69,0,0,0
```

By setting the "purchase price" to your buy in price, and setting the number of purchased shares to zero, the exact moment when that stock dips below zero will warn you that it's fallen under the specified price, even if it's `420.68`. The program notification system currently cannot tell you if it's at your buy in price, therefore consult the log files which are usually named `DD_MM_YYY.txt`, as these will be timestamped when the buy in, loss or gain alert triggered. Buy in notifications are separated from loss and profit alerts, so you can always be able to tell when a stock has exceeded a buy in.

## Note: Buy in alerts are detected by setting the number of purchased shares to `0`. They will also not trigger profit alerts.
___
## The Log:
Every day, TornStonks makes a log similar to how Torn makes logs and events, these are timestamped.
An example log for any day may look like the following:
```
[04:17:42] [STARTUP] TornStonks started.
[04:17:43] [LOSS] Legal Authorities Group exceeded your loss threshold of -1.0%
[04:36:28] [BUY IN] Torn City Investments exceeded your buy in threshold of $993.74
[04:43:17] [GAIN] Crude Oil Co exceeded your profit threshold of 2.4%
```

Using any text editor to search through the log, you'll notice that things are intentionally given tags similar to the Torn logs.

These are:

* `[STARTUP]` Which is fairly self explanatory.
* `[GAIN]` Which indicates a profit.
* `[LOSS]` Which indicates a loss.
* `[BUY IN]` Which indicates a buy in price deemed acceptable.
___
# What's Next?

* Allow barebones adding and removal of stock rows via the notification tray menu.
* Office Hours, a way to define what time of day it is acceptable to emit notifications.
	* Find a way to add custom duration in minutes for silent notifications?
	* Windows 10 and 11 have a feature known as Focus Assist which mutes notifications, however, other operating systems like macOS and Linux may differ on this.
* Torn API intergration to download your portfolio only? Optional feature, I don't want users to be entering API keys for no reason. Privacy is an actual goal here.
	* API keys are a very private thing that can leak your battle stats or stock positions for mugging purposes.
* Actual buttons to the main window rather than a minimalist interface?
	* This is to facilitate adding and removing rows from TornStonks.