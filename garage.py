import wx
import engine

class DictPage(wx.Dialog):
	def __init__(self, dictionary, title = ''):
		self.dictionary = dictionary
		self.title = title

		wx.Dialog.__init__(self, None, -1, self.title.title(), size = (300, 500))

		self.init_layout()

	def init_layout(self):
		# Title and close button
		if self.title:
			title = wx.StaticText(self, -1, self.title.upper())

		# Close button
		close_btn = wx.Button(self, -1, 'Close')
		close_btn.Bind(wx.EVT_BUTTON, self.close)

		# All the dict items
		self.dict_items = {}

		dict_sizer = wx.BoxSizer(wx.VERTICAL)

		for param, value in sorted(self.dictionary.items()):
			t = type(value)
			ignore = False
			# Int or float is a text ctrl
			if t in [int, float]:
				disp_param = wx.TextCtrl(self, -1, str(value), size=(55, 20))
				items = disp_param

			# Tuple returns a sizer with len(tuple) text fields
			elif t == tuple:
				disp_param = wx.BoxSizer(wx.HORIZONTAL)
				items = []
				for v in value: 
					ctrl = wx.TextCtrl(self, -1, str(v), size=(30, 20))
					disp_param.Add(ctrl, 0, wx.RIGHT, 10)
					items.append(ctrl)

			elif t == dict:
				disp_param = wx.Button(self, -1, 'Expand', name = param)
				disp_param.Bind(wx.EVT_BUTTON, self.show_dict)
				items = False

			else:
				ignore = True

			if not ignore:
				if items:
					self.dict_items[param] = items

				# Layout parameter (title & params)
				param_sizer = wx.BoxSizer(wx.HORIZONTAL)
				param_sizer.Add(wx.StaticText(self, -1, param.title()), 0, wx.ALIGN_CENTER_VERTICAL)
				param_sizer.Add(disp_param, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 20)

				# Add to main sizer
				dict_sizer.Add(param_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)	


		# Assemble main sizer
		main_sizer = wx.BoxSizer(wx.VERTICAL)

		if self.title:
			main_sizer.Add(title, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 15)

		main_sizer.Add(dict_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL)
		main_sizer.Add(close_btn, 0, wx.ALIGN_RIGHT, wx.ALL, 20)
		self.SetSizer(main_sizer)
		self.Layout()

		# Reset size to main_sizer size
		self.SetSize(main_sizer.GetSize())
		self.Show(True)

	def update_dict(self):
		for p, v in self.dictionary.items():
			ignore = False
			t = type(v)
			# The tuple can only contain either all ints or all floats
			if t == tuple:
				val = [i.GetLineText(0) for i in self.dict_items[p]]
				if type(v) == int:
					val = [int(va) for va in val]
				# Else assumes float!!
				else:
					val = [float(va) for va in val]
				val = tuple(val)

			elif t == int:
				val = int(self.dict_items[p].GetLineText(0))
			elif t == float:
				val = float(self.dict_items[p].GetLineText(0))

			else:
				ignore = True

			if not ignore:
				self.dictionary[p] = val

	def show_dict(self, evt):
		param = evt.GetEventObject().GetName()
		dlg = DictPage(self.dictionary[param], param)
		if dlg.ShowModal():
			self.dictionary[param] = dlg.dictionary

	def close(self, evt):
		self.update_dict()

		if self.IsModal():
			self.EndModal(True)
		else:
			self.Close()

class ConfigurationEditor(wx.Dialog):
	def __init__(self):
		wx.Dialog.__init__(self, None, title = 'SlalomBoard Garage', size=(640, 480))

		# The complete current configuration is saved here
		# This is an empty base level configuration 
		self.configuration = {'boards': {}, 'endless': {}}

		# This Represents Model DataStructures for each configuration item
		self.model_conf = {
			'boards': {
				'max_lean': 0.026, 'lean_vel': 0.0015, 'max_speed': 24,
				'jitter': 0.025, 'break_speed': 1, 'slowed': 0.05,
				'break_effect': 1.5, 'max_pump': 4.5, 'optimal_velocity': 10,
				'sigma': 13
				},

			'endless': {
				'obstacle_prob': 0.015,
				'obstacle_size': (15, 22),
				'step_size': 20,
				'forward_cars': {'probability': 0.007, 'size': (50, 75), 'moving': (8, 14)},
				'backwards_cars': {'probability': 0.005, 'size': (50, 75), 'moving': (3, 8)}
				}
			}

		# Current Selection
		self.selection = {n: False for n in self.configuration.keys()}

		self.init_layout()


	def init_layout(self):
		'''
			This creates all the wx Elements and layouts them.
		'''

		# Define lb elements titles
		titles = {'boards': 'Boards', 'endless': 'Endless Maps'}

		# Set up listbox displayed elements
		# board (selection etc.)
		self.lb_elements = {}

		main_sizer = wx.BoxSizer(wx.VERTICAL)

		# Add Main Title
		main_sizer.Add(wx.StaticText(self, -1, 'SLALOM BOARD GARAGE'), 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 10)

		# Layout list boxes and their titles
		lb_sizer = wx.BoxSizer(wx.HORIZONTAL)
		for param, title in titles.items():

			# Add the title
			title_sizer = wx.BoxSizer(wx.VERTICAL)
			title_sizer.Add(wx.StaticText(self, -1, title), 0, wx.LEFT | wx.RIGHT, 10)

			# Add & Remove buttons
			add_btn = wx.Button(self, -1, '+', name = param)
			rem_btn = wx.Button(self, -1, '-', name = param)
			edit_btn = wx.Button(self, -1, 'Edit', name = param)

			add_btn.Bind(wx.EVT_BUTTON, self.add_btn_click)
			rem_btn.Bind(wx.EVT_BUTTON, self.remove_btn_click)
			edit_btn.Bind(wx.EVT_BUTTON, self.edit_btn_click)

			title_sizer.Add(add_btn, 0, wx.TOP, 5)
			title_sizer.Add(rem_btn, 0, wx.TOP, 5)
			title_sizer.Add(edit_btn, 0, wx.TOP, 5)

			# Add the title sizer
			lb_sizer.Add(title_sizer, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 10)

			# Create and add the listbox
			self.lb_elements[param] = wx.ListBox(self, -1, (0, 0), (90, 120), [], wx.LB_SINGLE, name = param)

			# Bind the change event
			self.Bind(wx.EVT_LISTBOX, self.update_selection, self.lb_elements[param])

			lb_sizer.Add(self.lb_elements[param], 0, wx.RIGHT, 10)

		# All the Buttons
		button_sizer = wx.BoxSizer(wx.HORIZONTAL)
		endless_btn = wx.Button(self, -1, 'Start Endless Game')
		endless_btn.Bind(wx.EVT_BUTTON, self.start_endless)
		button_sizer.Add(endless_btn)

		# Set up the main sizer
		main_sizer.Add(lb_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.TOP, 10)
		main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.TOP, 10)
		self.SetSizer(main_sizer)
		self.Show()

	def update(self):
		'''
			This updates all the dynamic values in the UI.
		'''

		for p in ['boards', 'endless']:
			names = self.configuration[p].keys()
			self.lb_elements[p].Clear()
			[self.lb_elements[p].Append(n) for n in names]

	def update_selection(self, *args):
		'''
			Updates the currently selected items.
		'''
		for param, lb in self.lb_elements.items():
			current_id = lb.GetSelection()
			if current_id != -1:
				current = lb.GetString(current_id)
			else:
				current = False

			self.selection[param] = current

	def add_btn_click(self, evt):
		param = evt.GetEventObject().GetName()
		dlg = wx.TextEntryDialog(self, 'Enter a Name','Enter Name')

		if dlg.ShowModal() == wx.ID_OK:
			name = dlg.GetValue()

			# Add the model configuration if the name doesn't exist yet
			if name not in self.configuration[param].keys():
				self.configuration[param][name] = self.model_conf[param]

		self.update()


	def remove_btn_click(self, evt):
		param = evt.GetEventObject().GetName()
		sel = self.selection[param]
		if sel:
			del self.configuration[param][sel]
		self.update()


	def edit_btn_click(self, evt):
		param = evt.GetEventObject().GetName()
		sel = self.selection[param]
		if sel:
			obj = self.configuration[param][sel]
			if param in ('boards', 'endless'):
				if param == 'boards':
					title = 'Editing Board: ' + sel
				else:
					title = 'Editing Endless Map: ' + sel

				dlg = DictPage(obj, title)

				if dlg.ShowModal():
					self.configuration[param][sel] = dlg.dictionary

		self.update()

	def start_endless(self, evt):
		if self.selection['boards'] and self.selection['endless']:
			board_params = self.configuration['boards'][self.selection['boards']]
			map_params = self.configuration['endless'][self.selection['endless']]
			params = {'size': (800, 650),'start_pos': 8.0,}

			# Verschachtelung
			map_params['board'] = board_params
			params.update(map_params)

			# Start the game
			engine.start_game(params)


if __name__ == '__main__':
	app = wx.App(
		redirect=True,filename="editor_log.txt"
	)

	ConfigurationEditor()

	app.MainLoop()