import wx

class ConfigurationEditor(wx.Dialog):
	def __init__(self):
		wx.Dialog.__init__(self, None, title = 'SlalomBoard Configuration Editor', size=(640, 480))

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
				'backwards_cars': {'probability': 0.005, 'size': (50, 75), 'moving': (3, 8), 'forward': False}
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

		main_sizer.Add(lb_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.TOP, 10)
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
			print obj

		self.update()


if __name__ == '__main__':
	app = wx.App(
		redirect=True,filename="editor_log.txt"
	)

	ConfigurationEditor()

	app.MainLoop()