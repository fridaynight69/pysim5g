'''
A GUI (Graphical User Interface) for running simulation and visualizing all results

'''
import tkinter as tk
import configparser
import os, os.path
from tkinter import messagebox
from tkinter import ttk
from PIL import Image, ImageTk

from vis import load_in_all_main_lut, load_in_all_main_lut_specific
from vis import plotting_function1_isd, plotting_function2_isd
from run import run_simulator, generate_site_radii
from run import ANT_TYPE, CONFIDENCE_INTERVALS, MODULATION_AND_CODING_LUT, PARAMETERS, SITE_RADII, SPECTRUM_PORTFOLIO

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__),'..','scripts', 'script_config.ini'))

# Default path for all objects
BASE_PATH = CONFIG['file_locations']['base_path']

# The paths comprise the simulation graphs
LINE_GRAPH = os.path.join(BASE_PATH, '..', 'vis', 'outputs', 'frequency_capacity_lineplot_isd.png')
BAR_GRAPH = os.path.join(BASE_PATH, '..', 'vis', 'outputs', 'frequency_capacity_barplot_isd_specific.png')

# The path comprises the run.py file - for configuring inputs
INPUT_CONF = os.path.join(BASE_PATH, '..', 'scripts', 'run.py')

# The path comprises the vis.py file - for configuring visualization
VIS_CONF = os.path.join(BASE_PATH, '..', 'scripts', 'vis.py')

class SampleApp(tk.Tk):
	def __init__(self):
		tk.Tk.__init__(self)
		self._frame = None
		self.switch_frame(StartPage)

	def switch_frame(self, frame_class):
		new_frame = frame_class(self)
		if self._frame is not None:
			self._frame.destroy()
		self._frame = new_frame
		self._frame.grid()

class StartPage(tk.Frame):
	def __init__(self, master):
		tk.Frame.__init__(self, master, bg='khaki')
		tk.Label(self, text="Start page",
                font=('MathJax_SansSerif-Bold', 18, "bold")).pack(side="top", fill="x", pady=5)
		tk.Button(self, text="README", font=('MathJax_SansSerif-Bold', 18, "bold"),
                command=lambda: master.switch_frame(READMEPage)).pack(fill='x', pady = 10)
		tk.Button(self, text="5G RAN SIMULATOR", font=('MathJax_SansSerif-Bold', 18, "bold"),
                command=lambda: master.switch_frame(simulation_runner)).pack(fill='x', pady = 10)
		tk.Button(self, text="RESULT VISUALIZATION", font=('MathJax_SansSerif-Bold', 18, "bold"),
                command=lambda: master.switch_frame(visualize)).pack(fill='x', pady = 10)
		tk.Button(self, text="Quit", font=('MathJax_SansSerif-Bold', 18, "bold"),
                command=master.quit).pack(fill='x', pady = 10)

class READMEPage(tk.Frame):
	def __init__(self, master):
		tk.Frame.__init__(self, master)
		tk.Frame.configure(self,bg='brown')
		tk.Label(self, text="README", font=('MathJax_SansSerif-Bold', 18, "bold")).pack(side="top", fill="x", pady=5)

		tk.Button(self, text="Go back", font=('MathJax_SansSerif-Bold', 14, "bold"),
				  command=lambda: master.switch_frame(StartPage)).pack()
		
		self.textDescription = '''
A Graphic User Interface is built on Tkinter (Python library)
1. Firstly click button "5G RAN SIMULATOR" to run simulator file (run.py) in scripts
2. Secondly click button "RESULT VISUALIZATION" to visualize all simulation results in graphs
After click "RESULT VISUALIZATION", a window "Running visualization" will appear:
	2.1. Click "Start Visualization" to start visualizing simulation results
	2.2. Click "Show line graphs" to display the line graphs of simulation results
	2.3. Click "Show bar graphs" to display the bar graphs of simulation results
		'''
		
		tk.Label(self, text=self.textDescription, font=('MathJax_SansSerif-Bold',
				12, "bold")).pack(side="top", fill="both")


class simulation_runner(tk.Frame):
	def __init__(self, master):
		'''
		Running simulation
		'''

		self.Message = "5G RAN SIMULATOR"
		tk.Frame.__init__(self, master)      
		tk.Frame.configure(self,bg='black')
		self.LabelMessage = tk.Label(self, text=self.Message, font=('MathJax_SansSerif-Bold', 18, "bold"))

		self.inputButton = tk.Button(self, text = 'Configure input',
						command = self.configure_input,
						font = ('MathJax_SansSerif-Bold', 14, "bold")
						)

		self.StartButton = tk.Button(self, text = 'Start simulation',
						command = self.start_simulation,
						font = ('MathJax_SansSerif-Bold', 14, "bold")
						)

		self.goBackButton = tk.Button(self, text = "Go back", font = ('MathJax_SansSerif-Bold', 14, "bold"),
				  command = lambda: master.switch_frame(StartPage))

		self.show_widgets()

	def configure_input(self):
		os.system("start "+INPUT_CONF)
	
	def start_simulation(self):
		run_simulator(PARAMETERS,
				SPECTRUM_PORTFOLIO,
				ANT_TYPE,
				SITE_RADII,
				MODULATION_AND_CODING_LUT,
				CONFIDENCE_INTERVALS
				)
	
	def show_widgets(self):
		self.LabelMessage.pack(side="top", fill="x", pady=5)

		self.inputButton.pack(fill='x', pady = 10)
		self.StartButton.pack(fill='x', pady = 10)
		self.goBackButton.pack(fill='x', pady = 10)

class visualize(tk.Frame):
	'''
	Class for visualization of all results from simulation_runner as graphs
	'''
	def __init__(self, master):
		tk.Frame.__init__(self, master)      
		tk.Frame.configure(self,bg='blue')
		
		self.Message = "RESULT VISUALIZATION"

		self.LabelMessage = tk.Label(self, text=self.Message, font=('MathJax_SansSerif-Bold', 18, "bold"))

		self.visConfButton = tk.Button(self, text = 'Configuration',
						command = self.vis_conf,
						font = ('MathJax_SansSerif-Bold', 14, "bold")
								)

		self.StartButton = tk.Button(self, text = 'Start Visualization', command = self.start_vis,
							font = ('MathJax_SansSerif-Bold', 14, "bold"))

		self.showGraphButton1 = tk.Button(self, text = 'Show line graphs',
						font = ('MathJax_SansSerif-Bold', 14, "bold"),
						command = lambda: master.switch_frame(Zoom(tk.Toplevel(self.master), LINE_GRAPH))
							)
		self.showGraphButton2 = tk.Button(self, text = 'Show bar graphs',
						font = ('MathJax_SansSerif-Bold', 14, "bold"),
						command = lambda: master.switch_frame(Zoom(tk.Toplevel(self.master), BAR_GRAPH))
							)

		self.goBackButton = tk.Button(self, text = "Go back",
							font = ('MathJax_SansSerif-Bold', 14, "bold"),
							command = lambda: master.switch_frame(StartPage))
		self.show_widgets()

	def start_vis(self):
		max_isd_distance = 5
		data = load_in_all_main_lut(max_isd_distance)
		plotting_function1_isd(data)
		specific_data = load_in_all_main_lut_specific(max_isd_distance)
		plotting_function2_isd(specific_data)

		DATA_OUTPUT = os.path.join(BASE_PATH, '..', 'vis', 'outputs', 'frequency_capacity_barplot_isd_specific.png')
		if (os.path.isfile(DATA_OUTPUT)):
			messagebox.showinfo(title= 'Response', message= "Completely visualize all results\nThe graphs were saved in ../vis/outputs/")
		
	def vis_conf(self):
		os.system("start"+ VIS_CONF)

	def show_widgets(self):
		self.LabelMessage.pack(side="top", fill="x", pady=5)
		self.visConfButton.pack(fill='x', pady = 10)
		self.StartButton.pack(fill='x', pady = 10)
		self.showGraphButton1.pack(fill='x', pady = 10)
		self.showGraphButton2.pack(fill='x', pady = 10)
		self.goBackButton.pack(fill='x', pady = 10)

# Classes for adding scrollbar and mouse wheel in order to zoom image
# Reference: https://stackoverflow.com/questions/25787523/move-and-zoom-a-tkinter-canvas-with-mouse/48069295#48069295
class AutoScrollbar(ttk.Scrollbar):
    ''' A scrollbar that hides itself if it's not needed.
        Works only if you use the grid geometry manager '''

    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
        ttk.Scrollbar.set(self, lo, hi)

    def pack(self, **kw):
        raise tk.TclError('Cannot use pack with this widget')

    def place(self, **kw):
        raise tk.TclError('Cannot use place with this widget')

class Zoom(ttk.Frame):
	''' Simple zoom with mouse wheel '''

	def __init__(self, master, path):
		''' Initialize the main Frame '''

		ttk.Frame.__init__(self, master)
		self.master.title('Simulation graph for performance metrics')
		
        # Vertical and horizontal scrollbars for canvas
		vbar = AutoScrollbar(self.master, orient='vertical')
		hbar = AutoScrollbar(self.master, orient='horizontal')
		vbar.grid(row=0, column=1, sticky='ns')
		hbar.grid(row=1, column=0, sticky='we')
        # Open image
		self.image = Image.open(path)
        # Create canvas and put image on it
		self.canvas = tk.Canvas(self.master, highlightthickness=0,
                                xscrollcommand=hbar.set, yscrollcommand=vbar.set)
		self.canvas.grid(row=0, column=0, sticky='nswe')
		vbar.configure(command=self.canvas.yview)  # bind scrollbars to the canvas
		hbar.configure(command=self.canvas.xview)
        # Make the canvas expandable
		self.master.rowconfigure(0, weight=1)
		self.master.columnconfigure(0, weight=1)
        # Bind events to the Canvas
		self.canvas.bind('<ButtonPress-1>', self.move_from)
		self.canvas.bind('<B1-Motion>',     self.move_to)
		self.canvas.bind('<MouseWheel>', self.wheel)  # with Windows and MacOS, but not Linux
		self.canvas.bind('<Button-5>',   self.wheel)  # only with Linux, wheel scroll down
		self.canvas.bind('<Button-4>',   self.wheel)  # only with Linux, wheel scroll up
        # Show image
		self.imscale = 1.0
		self.imageid = None
		self.delta = 0.75
        # Text is used to set proper coordinates to the image
		self.text = self.canvas.create_text(0, 0, anchor='nw', text='Scroll to zoom')
		self.show_image()

	def move_from(self, event):
		''' Remember previous coordinates for scrolling with the mouse '''
		self.canvas.scan_mark(event.x, event.y)

	def move_to(self, event):
		''' Drag (move) canvas to the new position '''
		self.canvas.scan_dragto(event.x, event.y, gain=1)

	def wheel(self, event):
		''' Zoom with mouse wheel '''
		scale = 1.0
        # Respond to Linux (event.num) or Windows (event.delta) wheel event
		if event.num == 5 or event.delta == -120:
			scale        *= self.delta
			self.imscale *= self.delta
		if event.num == 4 or event.delta == 120:
			scale        /= self.delta
			self.imscale /= self.delta
        # Rescale all canvas objects
		x = self.canvas.canvasx(event.x)
		y = self.canvas.canvasy(event.y)
		self.canvas.scale('all', x, y, scale, scale)
		self.show_image()

	def show_image(self):
		''' Show image on the Canvas '''
		if self.imageid:
			self.canvas.delete(self.imageid)
			self.imageid = None
			self.canvas.imagetk = None  # delete previous image from the canvas
		width, height = self.image.size
		new_size = int(self.imscale * width), int(self.imscale * height)
		imagetk = ImageTk.PhotoImage(self.image.resize(new_size))
        # Use self.text object to set proper coordinates
		self.imageid = self.canvas.create_image(self.canvas.coords(self.text),
                                                anchor='nw', image=imagetk)
		self.canvas.lower(self.imageid)  # set it into background
		self.canvas.imagetk = imagetk  # keep an extra reference to prevent garbage-collection


# Running the App as the main module
if __name__ == '__main__':
    app = SampleApp()
    app.title("Simulation runner")
    app.mainloop()