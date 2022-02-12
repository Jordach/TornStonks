import requests
import json
import sys
import schedule
import time
import threading
import pprint
import csv

from datetime import datetime, date
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QAction, QTableWidget, QTableWidgetItem, QVBoxLayout, QSystemTrayIcon, QMenu, QStatusBar
from PyQt5.QtGui import QIcon, QPainter
from PyQt5.QtCore import pyqtSlot, QTimer

user_positions_file = "user_positions.conf"
#user_config_file_b = "user_options_b.conf"
csv_data = csv.DictReader(open(user_positions_file, mode="rt"))
user_data  = {"stock":[], "buy":[], "shares":[], "gain":[], "loss":[]}
num_stonks = 0
for row in csv_data:
	user_data["stock"].append(row["stock"])
	user_data["buy"].append(row["buy"])
	user_data["shares"].append(row["shares"])
	user_data["gain"].append(row["gain"])
	user_data["loss"].append(row["loss"])
	num_stonks += 1

pp = pprint.PrettyPrinter(indent=4)
#torn_token = "" # Not implemented, but later on probably for better intergration.
pyqt_init = False
tornsy_api_address = "https://tornsy.com/api/stocks?interval=m30"
tornsy_data = requests.get(tornsy_api_address)
json_data = ""
current_day = ""
app_name = "TornStonks"
ver_info = "0.1"

def update_date():
	today = date.today()

	global current_day
	current_day = today.strftime("%d_%m_%Y")
update_date()

def write_notification_to_log(log_text):
	ctime = datetime.now()
	time_string = ctime.strftime("[%H:%M:%S] ")
	with open(current_day+".txt", "a+") as file:
		file.seek(0)
		contents = file.read(100)
		if len(contents) > 0:
			file.write("\n")
		file.write(time_string+log_text)
write_notification_to_log("[STARTUP] " + app_name + " started.")

def save_user_data_csv():
	global user_positions_file
	global user_data
	with open(user_positions_file, mode="w", newline="") as csv_file:
		fieldnames = ["stock", "buy", "shares", "gain", "loss"]
		writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

		global num_stonks
		writer.writeheader()
		for i in range(0, num_stonks):
			writer.writerow({"stock" : user_data["stock"][i], "buy" : user_data["buy"][i],  "shares" : user_data["shares"][i], "gain" : user_data["gain"][i], "loss" : user_data["loss"][i]})

# Nicked from https://schedule.readthedocs.io/en/stable/background-execution.html
# But I don't think many will actually care.
def run_continuously(interval=1):
	"""Continuously run, while executing pending jobs at each
	elapsed time interval.
	@return cease_continuous_run: threading. Event which can
	be set to cease continuous run. Please note that it is
	*intended behavior that run_continuously() does not run
	missed jobs*. For example, if you've registered a job that
	should run every minute and you set a continuous run
	interval of one hour then your job won't be run 60 times
	at each interval but only once.
	"""
	cease_continuous_run = threading.Event()

	class ScheduleThread(threading.Thread):
		@classmethod
		def run(cls):
			while not cease_continuous_run.is_set():
				schedule.run_pending()
				time.sleep(interval)

	continuous_thread = ScheduleThread()
	continuous_thread.start()
	return cease_continuous_run

def get_latest_stocks():
	update_date()
	global tornsy_data
	tornsy_data = requests.get(tornsy_api_address)

	if tornsy_data.status_code == 200:
		global json_data
		json_data = json.loads(tornsy_data.text)
		global pyqt_init
		if pyqt_init:
			App.update_table(ex, False)
		#print("Successfully updated stocks from Tornsy")
	else:
		raise ValueError("Server returned error code that was not OK 200.")

# Get initial data
get_latest_stocks()

# Initiate background thread
schedule.every().minute.at(":10").do(get_latest_stocks)
stop_run_continuously = run_continuously()

# PyQt things
class App(QWidget):
	def __init__(self):
		super().__init__()
		global app_name
		global ver_info
		self.title = app_name + " " + ver_info
		self.left = 0
		self.top = 0
		self.width = 800
		self.height = 1020
		self.setWindowIcon(QIcon("tornstonks.ico"))
		self.update_timer = QTimer(self)
		self.update_timer.timeout.connect(self.table_update)
		self.update_timer.start(1000)
		self.save_timer = QTimer(self)
		self.save_timer.timeout.connect(self.save_data)
		self.save_timer.start(60000)
		self.tray_icon = QSystemTrayIcon(self)
		self.statusBar = QStatusBar()
		self.tray_icon.setIcon(QIcon("tornstonks.ico"))
		self.tray_icon.setToolTip("TornStonks")
		self.tray_icon.activated.connect(self.show_hide_window)
		self.tray_icon.show()
		self.window_visible = True
		self.auto_window_resizing = False
		self.no_notification = False
		self.not_recently_notified = True
		self.enable_notify_in_mins = 5
		self.create_tray_menu()
		self.init_ui()

	def init_ui(self):
		self.setWindowTitle(self.title)
		self.setGeometry(self.left, self.top, self.width, self.height)

		self.create_table()

		self.layout = QVBoxLayout()
		self.layout.addWidget(self.table_widget)
		self.layout.addWidget(self.statusBar)
		self.setLayout(self.layout)

		self.show()

	def create_tray_menu(self):
		self.tray_menu = QMenu()

		# Notification settings
		if self.no_notification:
			self.tray_notify = QAction("Enable Stock Notifications")
		else:
			self.tray_notify = QAction("Disable Stock Notifications")
		self.tray_notify.triggered.connect(self.set_notify)
		self.tray_menu.addAction(self.tray_notify)

		self.notify_duration_menu = QMenu("Time Between Notifications")
		if self.enable_notify_in_mins == 1:
			self.notify_duration_1m = QAction("Always Display Alerts [Current Setting]")
		else:
			self.notify_duration_1m = QAction("Always Display Alerts")

		if self.enable_notify_in_mins == 5:
			self.notify_duration_5m = QAction("5 Minutes [Current Setting]")
		else:
			self.notify_duration_5m = QAction("5 Minutes")

		if self.enable_notify_in_mins == 15:
			self.notify_duration_15m = QAction("15 Minutes [Current Setting]")
		else:
			self.notify_duration_15m = QAction("15 Minutes")

		if self.enable_notify_in_mins == 30:
			self.notify_duration_30m = QAction("30 Minutes [Current Setting]")
		else:
			self.notify_duration_30m = QAction("30 Minutes")

		if self.enable_notify_in_mins == 60:
			self.notify_duration_1h = QAction("1 Hour [Current Setting]")
		else:
			self.notify_duration_1h = QAction("1 Hour")

		if self.enable_notify_in_mins == 60*3:
			self.notify_duration_3h = QAction("3 Hours [Current Setting]")
		else:
			self.notify_duration_3h = QAction("3 Hours")

		if self.enable_notify_in_mins == 60*6:
			self.notify_duration_6h = QAction("6 Hours [Current Setting]")
		else:
			self.notify_duration_6h = QAction("6 Hours")
		
		if self.enable_notify_in_mins == 60*12:
			self.notify_duration_12h = QAction("12 Hours [Current Setting]")
		else:
			self.notify_duration_12h = QAction("12 Hours")

			
		#self.notify_duration_custom = QAction("Custom Duration [Currently: " + str(self.enable_notify_in_mins) + "]")
		self.notify_duration_1m.triggered.connect(self.set_notify_duration_1m)
		self.notify_duration_5m.triggered.connect(self.set_notify_duration_5m)
		self.notify_duration_15m.triggered.connect(self.set_notify_duration_15m)
		self.notify_duration_30m.triggered.connect(self.set_notify_duration_30m)
		self.notify_duration_1h.triggered.connect(self.set_notify_duration_1h)
		self.notify_duration_3h.triggered.connect(self.set_notify_duration_3h)
		self.notify_duration_6h.triggered.connect(self.set_notify_duration_6h)
		self.notify_duration_12h.triggered.connect(self.set_notify_duration_12h)
		#self.notify_duration_custom.triggered.connect(self.set_notify_duration_custom)
		self.notify_duration_menu.addAction(self.notify_duration_1m)
		self.notify_duration_menu.addAction(self.notify_duration_5m)
		self.notify_duration_menu.addAction(self.notify_duration_15m)
		self.notify_duration_menu.addAction(self.notify_duration_30m)
		self.notify_duration_menu.addAction(self.notify_duration_1h)
		self.notify_duration_menu.addAction(self.notify_duration_3h)
		self.notify_duration_menu.addAction(self.notify_duration_6h)
		self.notify_duration_menu.addAction(self.notify_duration_12h)
		#self.notify_duration_menu.addAction(self.notify_duration_custom)
		self.tray_menu.addMenu(self.notify_duration_menu)
		self.tray_menu.addSeparator()

		# User settings
		self.reload_user_stocks = QAction("Reload User Stock Positions")
		self.reload_user_stocks.triggered.connect(self.reload_user_data)
		self.tray_menu.addAction(self.reload_user_stocks)
		self.tray_menu.addSeparator()

		# Window Configuration
		if self.auto_window_resizing:
			self.tray_resizer = QAction("Disable Automatic Window Resizing")
		else:
			self.tray_resizer = QAction("Enable Automatic Window Resizing")
		self.tray_resizer.triggered.connect(self.resizer_setting)		
		self.tray_menu.addAction(self.tray_resizer)

		self.tray_show_hide = None
		if self.window_visible:
			self.tray_show_hide = QAction("Hide TornStonks")
		else:
			self.tray_show_hide = QAction("Show TornStonks")
		self.tray_show_hide.triggered.connect(self.show_hide_window_context)
		self.tray_menu.addAction(self.tray_show_hide)
		self.tray_menu.addSeparator()
		self.tray_quit = QAction("Quit")
		self.tray_quit.triggered.connect(QApplication.quit)
		self.tray_menu.addAction(self.tray_quit)
		self.tray_icon.setContextMenu(self.tray_menu)

	def set_notify_duration_1m(self):
		self.enable_notify_in_mins = 0.5
		# Update the Tray Menu
		self.create_tray_menu()
	def set_notify_duration_5m(self):
		self.enable_notify_in_mins = 5
		# Update the Tray Menu
		self.create_tray_menu()
	def set_notify_duration_15m(self):
		self.enable_notify_in_mins = 15
		# Update the Tray Menu
		self.create_tray_menu()
	def set_notify_duration_30m(self):
		self.enable_notify_in_mins = 30
		# Update the Tray Menu
		self.create_tray_menu()
	def set_notify_duration_1h(self):
		self.enable_notify_in_mins = 60
		# Update the Tray Menu
		self.create_tray_menu()
	def set_notify_duration_3h(self):
		self.enable_notify_in_mins = 60*3
		# Update the Tray Menu
		self.create_tray_menu()
	def set_notify_duration_6h(self):
		self.enable_notify_in_mins = 60*6
		# Update the Tray Menu
		self.create_tray_menu()
	def set_notify_duration_12h(self):
		self.enable_notify_in_mins = 60*12
		# Update the Tray Menu
		self.create_tray_menu()
	def set_notify_duration_custom(self):
		# This is a todo
		self.enable_notify_in_mins = self.enable_notify_in_mins + 0
		# Update the Tray Menu
		self.create_tray_menu()

	def reload_user_data(self):
		global user_positions_file
		global user_data
		global num_stonks
		csv_data = csv.DictReader(open(user_positions_file, mode="rt"))
		user_data  = {"stock":[], "buy":[], "shares":[], "gain":[], "loss":[]}
		num_stonks = 0
		for row in csv_data:
			user_data["stock"].append(row["stock"])
			user_data["buy"].append(row["buy"])
			user_data["shares"].append(row["shares"])
			user_data["gain"].append(row["gain"])
			user_data["loss"].append(row["loss"])
			num_stonks += 1
		self.update_table(True)

	def set_notify(self):
		if self.no_notification:
			self.no_notification = False
		else:
			self.no_notification = True
		self.create_tray_menu()

	def show_hide_window(self, reason):
		if reason == 3:
			if self.window_visible:
				self.window_visible = False
				self.hide()
			else:
				self.window_visible = True
				self.show()
			self.create_tray_menu()

	def show_hide_window_context(self):
		if self.window_visible:
			self.window_visible = False
			self.hide()
		else:
			self.window_visible = True
			self.show()
		self.create_tray_menu()

	def closeEvent(self, event):
		event.ignore()
		self.window_visible = False
		self.create_tray_menu()
		self.hide()

	def unmute_notifier(self):
		self.not_recently_notified = True
		# write_notification_to_log("Unmuted Notifications")
		return schedule.CancelJob

	@pyqtSlot()
	def resizer_setting(self):
		if self.auto_window_resizing:
			self.auto_window_resizing = False
		else:
			self.auto_window_resizing = True

		# Update the Tray Menu
		self.create_tray_menu()

	def create_table(self):
		self.table_widget = QTableWidget()
		global num_stonks
		self.table_widget.setRowCount(num_stonks)
		self.table_widget.setColumnCount(11)
		self.table_widget.setHorizontalHeaderLabels(
			["Bought Price",            #0
			"Shares",                   #1
			"Gain Alert %",             #2
			"Loss Alert %",             #3
			"Price",                    #4
			"30m Ago",                  #5
			"Gain/Loss %",              #6
			"Purchase Total",           #7
			"Pre Tax Gain/Loss",        #8
			"Taxed Gain/Loss",          #9
			"Final Sale Value w/ Tax"]  #10
		)
		self.table_widget.move(0,0)
		self.table_widget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
		self.table_widget.setUpdatesEnabled(True)
		self.update_table(True)

	def update_table(self, update_user_data):
		global json_data
		global user_data
		global num_stonks
		global pyqt_init

		row_headers = []
		self.table_widget.setRowCount(num_stonks)
		gains = 0
		ygain = 0
		losses = 0
		yloss = 0
		buyins = 0
		ybuy = 0
		for y in range(0, num_stonks):
			row_headers.append(user_data["stock"][y])
			item = None
			for data in json_data["data"]:
				if user_data["stock"][y] == data["stock"]:
					item = data
			if item["stock"] != "TCSE":
				if y <= num_stonks:
					if user_data["stock"][y] == item["stock"]:
						if update_user_data:
							self.table_widget.setItem(y, 0, QTableWidgetItem(str(user_data["buy"][y])))
							self.table_widget.setItem(y, 1, QTableWidgetItem(str(user_data["shares"][y])))
							self.table_widget.setItem(y, 2, QTableWidgetItem(str(user_data["gain"][y])))
							self.table_widget.setItem(y, 3, QTableWidgetItem(str(user_data["loss"][y])))
							self.table_widget.setItem(y, 7, QTableWidgetItem("$"+str("{:,.2f}".format(float(user_data["shares"][y]) * float(user_data["buy"][y])))))
						if float(user_data["buy"][y]) > 0:
							bought_for = float(user_data["buy"][y])
							curr_price = float(item["price"])
							perc = (float(curr_price - bought_for) / bought_for) * 100
							self.table_widget.setItem(y, 6, QTableWidgetItem(str("{:.2f}".format(perc)) + "%"))
							gain_test = float(user_data["gain"][y])
							loss_test = 0 - float(user_data["loss"][y])
							if perc > gain_test:
								if user_data["shares"][y] != "0": # Only alert when you actually own shares in the stock for making profit on
									write_notification_to_log("[GAIN] "+item["name"] + " exceeded your profit threshold of " + str(gain_test) + "%")
									gains+=1
									if gains == 1:
										ygain = item
							elif perc <= loss_test:
								if user_data["shares"][y] == "0":
									write_notification_to_log("[BUY IN] "+item["name"] + " exceeded your buy in threshold of $" + str(user_data["buy"][y]))
									buyins+=1
									if buyins == 1:
										ybuy = item
								else:
									write_notification_to_log("[LOSS] "+item["name"] + " exceeded your loss threshold of " + str(loss_test) + "%")
									losses+=1
									if losses == 1:
										yloss = item
							
						else:
							self.table_widget.setItem(y, 6, QTableWidgetItem("N/A"))
						self.table_widget.setItem(y, 4, QTableWidgetItem("$"+str(item["price"])))
						self.table_widget.setItem(y, 5, QTableWidgetItem("$"+str(item["interval"]["m30"]["price"])))
						tax_res = float(user_data["shares"][y]) * float(item["price"])
						self.table_widget.setItem(y, 8, QTableWidgetItem("$"+str("{:,.2f}".format((tax_res)-float(user_data["buy"][y])*float(user_data["shares"][y])))))
						self.table_widget.setItem(y, 9, QTableWidgetItem("$"+str("{:,.2f}".format((tax_res * 0.999)-float(user_data["buy"][y])*float(user_data["shares"][y])))))
						self.table_widget.setItem(y, 10, QTableWidgetItem("$"+str("{:,.2f}".format(tax_res * 0.999))))
			if not self.no_notification and y == (num_stonks - 1):
				if self.not_recently_notified:
					# This silences notifications when starting TornStonks
					if pyqt_init:
						self.not_recently_notified = False
						# This is a dirty hack, shave a few seconds off so it hopefully runs just before the incoming stock refresh
						schedule.every((60 * self.enable_notify_in_mins) - 10).seconds.do(self.unmute_notifier)
						if gains == 1:
							self.tray_icon.showMessage("TENDIES!", ygain["name"] + " has exceeded your profit threshold.", QIcon("tornstonks.ico"))
						elif gains > 1:
							self.tray_icon.showMessage("BULLRUN!", "Multiple stocks have exceeded your profit thresholds.", QIcon("tornstonks.ico"))

						if buyins == 1:
							self.tray_icon.showMessage("SOLD SHORT!", ybuy["name"] + " has exceeded your buy in threshold.", QIcon("tornstonks.ico"))
						elif buyins > 1:
							self.tray_icon.showMessage("FIRESALE!", "Multiple stocks have exceeded your buy in threshold.", QIcon("tornstonks.ico"))

						if losses == 1:
							self.tray_icon.showMessage("BEARISH!", yloss["name"] + " has exceeded your loss threshold.", QIcon("tornnotstonks.ico"))
						elif losses > 1:
							self.tray_icon.showMessage("DAMMIT BOBO!", "Multiple stocks have exceeded your loss thresholds.", QIcon("tornnotstonks.ico"))
		self.table_widget.setVerticalHeaderLabels(row_headers)
		# Resize window on first launch
		if not pyqt_init:
			pyqt_init = True
			self.table_init_resize = QTimer(self)
			self.table_init_resize.timeout.connect(self.init_resize)
			self.table_init_resize.start(int(1000/60))
		else:
			# Resize window on stock updates
			if self.window_visible:	
				self.table_widget.resizeColumnsToContents()
				if self.auto_window_resizing:
					self.resize(self.sizeHint())
				self.table_widget.viewport().update()
		# Show last time when TornStocks imported data
		today = date.today()
		today_string = today.strftime("%d/%m/%Y")
		ctime = datetime.now()
		time_string = ctime.strftime("%H:%M:%S")
		self.tray_icon.setToolTip("Updated at: " + time_string + " " + today_string)
		self.statusBar.showMessage("Last Updated Stock Data at " + time_string + " " + today_string)

	@pyqtSlot()
	def init_resize(self):
		self.table_widget.resizeColumnsToContents()
		self.resize(self.sizeHint())
		self.table_widget.update()
		self.table_init_resize.stop()

	@pyqtSlot()
	def table_update(self):
		# Save user data as things are edited in real time;
		global num_stonks
		for row in range(0, num_stonks):
			for col in range(0, 2):
				self.cell = self.table_widget.item(row, col)

				if col == 0:
					user_data["buy"][row] = self.cell.text()
					if float(user_data["buy"][row]) > 0:
						bought_for = float(user_data["buy"][row])
						price = self.table_widget.item(row, 4).text()
						curr_price = float(price.replace("$", ""))
						perc = ((curr_price - bought_for) / bought_for) * 100
						self.table_widget.setItem(row, 6, QTableWidgetItem(str("{:.2f}".format(perc)) + "%"))
						self.table_widget.setItem(row, 7, QTableWidgetItem("$"+str("{:,.2f}".format(float(user_data["shares"][row]) * float(user_data["buy"][row])))))
						tax_res = float(user_data["shares"][row]) * curr_price
						self.table_widget.setItem(row, 8, QTableWidgetItem("$"+str("{:,.2f}".format((tax_res)-float(user_data["buy"][row])*float(user_data["shares"][row])))))
						self.table_widget.setItem(row, 9, QTableWidgetItem("$"+str("{:,.2f}".format((tax_res * 0.99)-float(user_data["buy"][row])*float(user_data["shares"][row])))))
						self.table_widget.setItem(row, 10, QTableWidgetItem("$"+str("{:,.2f}".format(tax_res * 0.99))))
					else:
						self.table_widget.setItem(row, 6, QTableWidgetItem("N/A"))
				elif col == 1:
					user_data["shares"][row] = self.cell.text()
				elif col == 2:
					user_data["gain"][row] = self.cell.text()
				elif col == 3:
					user_data["loss"][row] = self.cell.text()
					
		if self.window_visible:
			if self.auto_window_resizing:
				self.resize(self.sizeHint())
			self.table_widget.viewport().update()

	@pyqtSlot()
	def save_data(self):
		save_user_data_csv()

def stop_app():
	stop_run_continuously.set()
	save_user_data_csv()

if __name__ == '__main__':
	app = QApplication(sys.argv)
	app.aboutToQuit.connect(stop_app)
	ex = App()
	sys.exit(app.exec_())