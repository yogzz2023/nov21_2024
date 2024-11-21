import sys
import numpy as np
import csv
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QComboBox, QTextEdit,
                             QHBoxLayout, QToolButton, QTabWidget, QTableWidget, QScrollArea, QGroupBox, QRadioButton,
                             QLineEdit, QDialog, QGridLayout, QCheckBox, QTableWidgetItem)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, pyqtSignal, QObject
import pyqtgraph as pg

# Custom stream class to redirect stdout
class OutputStream:
    def __init__(self, text_edit):
        self.text_edit = text_edit

    def write(self, text):
        self.text_edit.append(text)

    def flush(self): 
        pass  # No need to implement flush for QTextEdit

class PlotConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Plot Configuration")
        self.setGeometry(300, 300, 350, 350)

        grid = QGridLayout()

        # Range
        self.range_group = QGroupBox("Range")
        range_layout = QHBoxLayout()
        self.min_range_edit = QLineEdit()
        self.min_range_edit.setPlaceholderText("Min")
        range_layout.addWidget(self.min_range_edit)
        self.max_range_edit = QLineEdit()
        self.max_range_edit.setPlaceholderText("Max")
        range_layout.addWidget(self.max_range_edit)
        self.range_group.setLayout(range_layout)
        grid.addWidget(self.range_group, 0, 0, 1, 2)

        # Azimuth
        self.azimuth_group = QGroupBox("Azimuth")
        azimuth_layout = QHBoxLayout()
        self.min_azimuth_edit = QLineEdit()
        self.min_azimuth_edit.setPlaceholderText("Min")
        azimuth_layout.addWidget(self.min_azimuth_edit)
        self.max_azimuth_edit = QLineEdit()
        self.max_azimuth_edit.setPlaceholderText("Max")
        azimuth_layout.addWidget(self.max_azimuth_edit)
        self.azimuth_group.setLayout(azimuth_layout)
        grid.addWidget(self.azimuth_group, 1, 0, 1, 2)

        # Elevation
        self.elevation_group = QGroupBox("Elevation")
        elevation_layout = QHBoxLayout()
        self.min_elevation_edit = QLineEdit()
        self.min_elevation_edit.setPlaceholderText("Min")
        elevation_layout.addWidget(self.min_elevation_edit)
        self.max_elevation_edit = QLineEdit()
        self.max_elevation_edit.setPlaceholderText("Max")
        elevation_layout.addWidget(self.max_elevation_edit)
        self.elevation_group.setLayout(elevation_layout)
        grid.addWidget(self.elevation_group, 2, 0, 1, 2)

        # Time
        self.time_group = QGroupBox("Time")
        time_layout = QHBoxLayout()
        self.min_time_edit = QLineEdit()
        self.min_time_edit.setPlaceholderText("Min")
        time_layout.addWidget(self.min_time_edit)
        self.max_time_edit = QLineEdit()
        self.max_time_edit.setPlaceholderText("Max")
        time_layout.addWidget(self.max_time_edit)
        self.time_group.setLayout(time_layout)
        grid.addWidget(self.time_group, 3, 0, 1, 2)

        # OK and Cancel buttons
        button_box = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        button_box.addWidget(ok_button)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_box.addWidget(cancel_button)
        grid.addLayout(button_box, 4, 0, 1, 2)

        self.setLayout(grid)

    def get_config_data(self):
        return {
            "range": (float(self.min_range_edit.text()), float(self.max_range_edit.text())),
            "azimuth": (float(self.min_azimuth_edit.text()), float(self.max_azimuth_edit.text())),
            "elevation": (float(self.min_elevation_edit.text()), float(self.max_elevation_edit.text())),
            "time": (float(self.min_time_edit.text()), float(self.max_time_edit.text()))
        }

class Signal(QObject):
    # Signal for collapsing the control panel
    collapseSignal = pyqtSignal(bool)

class KalmanFilterGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.tracks = []
        self.selected_track_ids = set()
        self.marker_size = 10  # Default marker size
        self.plot_color = 'b'  # Default plot color
        self.initUI()
        self.control_panel_collapsed = False  # Start with the panel expanded

    def initUI(self):
        self.setWindowTitle('Kalman Filter GUI')
        self.setGeometry(100, 100, 1200, 600)
        self.setStyleSheet("""
            QWidget {
                background-color: #222222;
                color: #ffffff;
                font-family: "Arial", sans-serif;
            }
            QPushButton {
                background-color: #4CAF50; 
                color: white;
                border: none;
                padding: 8px 16px;
                text-align: center;
                text-decoration: none;
                font-size: 16px;
                margin: 4px 2px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3e8e41;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
            }
            QComboBox {
                background-color: #222222;
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px;
                font-size: 12px;
            }
            QLineEdit {
                background-color: #333333;
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px;
                font-size: 12px;
            }
            QRadioButton {
                background-color: transparent;
                color: white;
            }
            QTextEdit {
                background-color: #333333;
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px;
                font-size: 12px;
            }
            QGroupBox {
                background-color: #333333;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px;
            }
            QTableWidget {
                background-color: #333333;
                color: white;
                border: 1px solid #555555;
                font-size: 12px;
            }
        """)

        # Main layout
        main_layout = QHBoxLayout()

        # Left side: System Configuration and Controls (Collapsible)
        left_layout = QVBoxLayout()
        main_layout.addLayout(left_layout)

        # Collapse/Expand Button
        self.collapse_button = QToolButton()
        self.collapse_button.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.collapse_button.setText("=")  # Set the button text to "="
        self.collapse_button.clicked.connect(self.toggle_control_panel)
        left_layout.addWidget(self.collapse_button)
        # Control Panel
        self.control_panel = QWidget()
        self.control_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        control_layout = QVBoxLayout()
        self.control_panel.setLayout(control_layout)
        left_layout.addWidget(self.control_panel)
        # File Upload Button
        self.file_upload_button = QPushButton("Upload File")
        self.file_upload_button.setIcon(QIcon("upload.png"))
        self.file_upload_button.clicked.connect(self.select_file)
        control_layout.addWidget(self.file_upload_button)
        # System Configuration button
        self.config_button = QPushButton("System Configuration")
        self.config_button.setIcon(QIcon("config.png"))
        self.config_button.clicked.connect(self.show_config_dialog)
        control_layout.addWidget(self.config_button)
        # Initiate Track drop down
        self.track_mode_label = QLabel("Initiate Track")
        self.track_mode_combo = QComboBox()
        self.track_mode_combo.addItems(["3-state", "5-state", "7-state"])
        control_layout.addWidget(self.track_mode_label)
        control_layout.addWidget(self.track_mode_combo)
        # Association Technique radio buttons
        self.association_group = QGroupBox("Association Technique")
        association_layout = QVBoxLayout()
        self.jpda_radio = QRadioButton("JPDA")
        self.jpda_radio.setChecked(True)
        association_layout.addWidget(self.jpda_radio)
        self.munkres_radio = QRadioButton("Munkres")
        association_layout.addWidget(self.munkres_radio)
        self.association_group.setLayout(association_layout)
        control_layout.addWidget(self.association_group)
        # Filter modes buttons
        self.filter_group = QGroupBox("Filter Modes")
        filter_layout = QHBoxLayout()
        self.cv_filter_button = QPushButton("CV Filter")
        filter_layout.addWidget(self.cv_filter_button)
        self.ca_filter_button = QPushButton("CA Filter")
        filter_layout.addWidget(self.ca_filter_button)
        self.ct_filter_button = QPushButton("CT Filter")
        filter_layout.addWidget(self.ct_filter_button)
        self.filter_group.setLayout(filter_layout)
        control_layout.addWidget(self.filter_group)

        # Process button
        self.process_button = QPushButton("Process")
        self.process_button.setIcon(QIcon("process.png"))
        self.process_button.clicked.connect(self.process_data)
        control_layout.addWidget(self.process_button)

        # Right side: Output and Plot (with Tabs)
        right_layout = QVBoxLayout()
        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        # Tab Widget for Output, Plot, and Track Info
        self.tab_widget = QTabWidget()
        self.output_tab = QWidget()
        self.plot_tab = QWidget()
        self.track_info_tab = QWidget()  # New Track Info Tab
        self.tab_widget.addTab(self.output_tab, "Output")
        self.tab_widget.addTab(self.plot_tab, "Plot")
        self.tab_widget.addTab(self.track_info_tab, "Track Info")  # Add Track Info Tab
        self.tab_widget.setStyleSheet(" color: black;")
        right_layout.addWidget(self.tab_widget)

        # Output Display
        self.output_display = QTextEdit()
        self.output_display.setFont(QFont('Courier', 10))
        self.output_display.setStyleSheet("background-color: #333333; color: #ffffff;")
        self.output_display.setReadOnly(True)
        self.output_tab.setLayout(QVBoxLayout())
        self.output_tab.layout().addWidget(self.output_display)

        # Plot Setup
        self.plot_widget = pg.GraphicsLayoutWidget()
        self.plot_tab.setLayout(QVBoxLayout())

        # Horizontal layout for plot controls
        plot_controls_layout = QHBoxLayout()

        # Plot Type dropdown
        self.plot_type_label = QLabel("Plot Type")
        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItems(["Range vs Time", "Azimuth vs Time", "Elevation vs Time", "PPI", "RHI", "All Modes"])
        self.plot_type_combo.currentTextChanged.connect(self.update_plot)
        plot_controls_layout.addWidget(self.plot_type_label)
        plot_controls_layout.addWidget(self.plot_type_combo)

        # Subplot Type dropdown
        self.subplot_type_label = QLabel("Subplot Type")
        self.subplot_type_combo = QComboBox()
        self.subplot_type_combo.addItems(["2 Subplots", "3 Subplots"])
        plot_controls_layout.addWidget(self.subplot_type_label)
        plot_controls_layout.addWidget(self.subplot_type_combo)

        # Plot Color dropdown
        self.plot_color_label = QLabel("Plot Color")
        self.plot_color_combo = QComboBox()
        self.plot_color_combo.addItems(["Blue", "Red", "Green", "Yellow", "Black"])
        self.plot_color_combo.currentTextChanged.connect(self.update_plot_color)
        plot_controls_layout.addWidget(self.plot_color_label)
        plot_controls_layout.addWidget(self.plot_color_combo)

        # Marker size selection
        self.marker_size_label = QLabel("Marker Size")
        self.marker_size_combo = QComboBox()
        self.marker_size_combo.addItems(["Small", "Medium", "Large"])
        self.marker_size_combo.currentTextChanged.connect(self.update_marker_size)
        plot_controls_layout.addWidget(self.marker_size_label)
        plot_controls_layout.addWidget(self.marker_size_combo)

        # Plot Configuration button
        self.plot_config_button = QPushButton("Plot Configuration")
        self.plot_config_button.clicked.connect(self.show_plot_config_dialog)
        plot_controls_layout.addWidget(self.plot_config_button)

        # Plot History button
        self.plot_history_button = QPushButton("Plot History")
        self.plot_history_button.clicked.connect(self.show_plot_history)
        plot_controls_layout.addWidget(self.plot_history_button)

        # Add plot controls to the plot tab
        self.plot_tab.layout().addLayout(plot_controls_layout)
        self.plot_tab.layout().addWidget(self.plot_widget)

        # Add Clear Plot and Clear Output buttons
        self.clear_plot_button = QPushButton("Clear Plot")
        self.clear_plot_button.clicked.connect(self.clear_plot)
        self.plot_tab.layout().addWidget(self.clear_plot_button)

        self.clear_output_button = QPushButton("Clear Output")
        self.clear_output_button.clicked.connect(self.clear_output)
        self.output_tab.layout().addWidget(self.clear_output_button)

        # Track Info Setup
        self.track_info_layout = QVBoxLayout()
        self.track_info_tab.setLayout(self.track_info_layout)

        # Buttons to load CSV files
        self.load_detailed_log_button = QPushButton("Load Detailed Log")
        self.load_detailed_log_button.clicked.connect(lambda: self.load_csv('detailed_log.csv'))
        self.track_info_layout.addWidget(self.load_detailed_log_button)

        self.load_track_summary_button = QPushButton("Load Track Summary")
        self.load_track_summary_button.clicked.connect(lambda: self.load_csv('track_summary.csv'))
        self.track_info_layout.addWidget(self.load_track_summary_button)

        # Table to display CSV data
        self.csv_table = QTableWidget()
        self.csv_table.setStyleSheet("background-color: black; color: red;")  # Set text color to white
        self.track_info_layout.addWidget(self.csv_table)

        # Track ID Selection
        self.track_selection_group = QGroupBox("Select Track IDs to Plot")
        self.track_selection_layout = QVBoxLayout()
        self.track_selection_group.setLayout(self.track_selection_layout)
        self.plot_tab.layout().addWidget(self.track_selection_group)

        # Scroll area for track ID checkboxes
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.track_selection_widget = QWidget()
        self.track_selection_layout_inner = QVBoxLayout()
        self.track_selection_widget.setLayout(self.track_selection_layout_inner)
        self.scroll_area.setWidget(self.track_selection_widget)
        self.track_selection_layout.addWidget(self.scroll_area)

        # Buttons for displaying subplots
        self.show_subplots_button = QPushButton("Show Subplots")
        self.show_subplots_button.clicked.connect(self.show_subplots)
        self.plot_tab.layout().addWidget(self.show_subplots_button)

        main_layout.addWidget(right_widget)

        # Redirect stdout to the output display
        sys.stdout = OutputStream(self.output_display)

        # Set main layout
        self.setLayout(main_layout)

        # Initial settings
        self.config_data = {
            "target_speed": (0, 100),
            "target_altitude": (0, 10000),
            "range_gate": (0, 1000),
            "azimuth_gate": (0, 360),
            "elevation_gate": (0, 90),
            "plant_noise": 20  # Default value
        }

        # Add connections to filter buttons
        self.cv_filter_button.clicked.connect(lambda: self.select_filter("CV"))
        self.ca_filter_button.clicked.connect(lambda: self.select_filter("CA"))
        self.ct_filter_button.clicked.connect(lambda: self.select_filter("CT"))

        # Set initial filter mode
        self.filter_mode = "CV"  # Start with CV Filter
        self.update_filter_selection()

    def toggle_control_panel(self):
        self.control_panel_collapsed = not self.control_panel_collapsed
        self.control_panel.setVisible(not self.control_panel_collapsed)
        self.adjustSize()

    def select_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Input File", "", "CSV Files (*.csv);;All Files (*)", options=options
        )
        if file_name:
            self.input_file = file_name
            print(f"File selected: {self.input_file}")

    def process_data(self):
        input_file = getattr(self, "input_file", None)
        track_mode = self.track_mode_combo.currentText()
        association_type = "JPDA" if self.jpda_radio.isChecked() else "Munkres"
        filter_option = self.filter_mode

        if not input_file:
            print("Please select an input file.")
            return

        print(
            f"Processing with:\nInput File: {input_file}\nTrack Mode: {track_mode}\nFilter Option: {filter_option}\nAssociation Type: {association_type}"
        )

        self.tracks = main(
            input_file, track_mode, filter_option, association_type
        )  # Process data with selected parameters

        if self.tracks is None:
            print("No tracks were generated.")
        else:
            print(f"Number of tracks: {len(self.tracks)}")

            # Update the plot after processing
            self.update_plot()

            # Update track selection checkboxes
            self.update_track_selection()

    def update_plot(self):
        if not self.tracks:
            print("No tracks to plot.")
            return

        plot_type = self.plot_type_combo.currentText()

        self.plot_widget.clear()  # Clear the plot widget before plotting
        plot = self.plot_widget.addPlot()

        if plot_type == "All Modes":
            self.plot_all_modes(self.tracks, plot)
        elif plot_type == "PPI":
            self.plot_ppi(self.tracks, plot)
        elif plot_type == "RHI":
            self.plot_rhi(self.tracks, plot)
        else:
            self.plot_measurements(self.tracks, plot, plot_type, self.selected_track_ids)

        plot.showGrid(x=True, y=True) 
        plot.showGrid(x=True, y=True)  # Add grid lines to the plot

    def plot_measurements(self, tracks, plot, plot_type, selected_track_ids=None):
        for track in tracks:
            if selected_track_ids is not None and track['track_id'] not in selected_track_ids:
                continue

            times = [m[0][3] for m in track['measurements']]
            measurements_x = [(m[0][:3])[0] for m in track['measurements']]
            measurements_y = [(m[0][:3])[1] for m in track['measurements']]
            measurements_z = [(m[0][:3])[2] for m in track['measurements']]

            # Plot Sf values starting from the third measurement
            if len(track['Sf']) > 2:
                Sf_x = [state[0] for state in track['Sf'][2:]]
                Sf_y = [state[1] for state in track['Sf'][2:]]
                Sf_z = [state[2] for state in track['Sf'][2:]]
                Sf_times = times[2:]
            else:
                Sf_x, Sf_y, Sf_z, Sf_times = [], [], [], []

            marker_size = self.marker_size  # Use the selected marker size
            plot_color = self.plot_color  # Use the selected plot color

            if plot_type == "Range vs Time":
                plot.plot(times, measurements_x, pen=None, symbol='o', symbolSize=marker_size, symbolBrush=plot_color, name=f'Track {track["track_id"]} Measurement X')
                plot.plot(Sf_times, Sf_x, pen=plot_color, symbol=None, name=f'Track {track["track_id"]} Sf X')
                plot.setLabel('left', 'X Coordinate')
            elif plot_type == "Azimuth vs Time":
                plot.plot(times, measurements_y, pen=None, symbol='o', symbolSize=marker_size, symbolBrush=plot_color, name=f'Track {track["track_id"]} Measurement Y')
                plot.plot(Sf_times, Sf_y, pen=plot_color, symbol=None, name=f'Track {track["track_id"]} Sf Y')
                plot.setLabel('left', 'Y Coordinate')
            elif plot_type == "Elevation vs Time":
                plot.plot(times, measurements_z, pen=None, symbol='o', symbolSize=marker_size, symbolBrush=plot_color, name=f'Track {track["track_id"]} Measurement Z')
                plot.plot(Sf_times, Sf_z, pen=plot_color, symbol=None, name=f'Track {track["track_id"]} Sf Z')
                plot.setLabel('left', 'Z Coordinate')

        plot.setLabel('bottom', 'Time')
        plot.setTitle(f'Tracks {plot_type}')
        plot.addLegend()

        # Add data tips
        proxy = pg.SignalProxy(plot.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
        self.data_tip = pg.TextItem("", anchor=(0.5, 0))
        plot.addItem(self.data_tip)

    def show_subplots(self):
        if not self.tracks:
            print("No tracks to plot.")
            return

        self.plot_widget.clear()  # Clear the plot widget before plotting
        layout = self.plot_widget.addLayout()

        # Create subplots for measurement_x, measurement_y, measurement_z vs time
        plot_x = layout.addPlot(row=0, col=0)
        plot_y = layout.addPlot(row=0, col=1)
        plot_z = layout.addPlot(row=0, col=2)

        for track in self.tracks:
            times = [m[0][3] for m in track['measurements']]
            measurements_x = [(m[0][:3])[0] for m in track['measurements']]
            measurements_y = [(m[0][:3])[1] for m in track['measurements']]
            measurements_z = [(m[0][:3])[2] for m in track['measurements']]

            marker_size = self.marker_size  # Use the selected marker size
            plot_color = self.plot_color  # Use the selected plot color

            plot_x.plot(times, measurements_x, pen=None, symbol='o', symbolSize=marker_size, symbolBrush=plot_color, name=f'Track {track["track_id"]} Measurement X')
            plot_y.plot(times, measurements_y, pen=None, symbol='o', symbolSize=marker_size, symbolBrush=plot_color, name=f'Track {track["track_id"]} Measurement Y')
            plot_z.plot(times, measurements_z, pen=None, symbol='o', symbolSize=marker_size, symbolBrush=plot_color, name=f'Track {track["track_id"]} Measurement Z')

        plot_x.setLabel('bottom', 'Time')
        plot_x.setLabel('left', 'X Coordinate')
        plot_y.setLabel('bottom', 'Time')
        plot_y.setLabel('left', 'Y Coordinate')
        plot_z.setLabel('bottom', 'Time')
        plot_z.setLabel('left', 'Z Coordinate')

        plot_x.setTitle("Measurement X vs Time")
        plot_y.setTitle("Measurement Y vs Time")
        plot_z.setTitle("Measurement Z vs Time")

        # Synchronize zooming across subplots
        def sync_zoom(plot, other_plots):
            def update_view_range():
                for other_plot in other_plots:
                    other_plot.setXRange(plot.viewRange()[0][0], plot.viewRange()[0][1], padding=0)
                    other_plot.setYRange(plot.viewRange()[1][0], plot.viewRange()[1][1], padding=0)

            plot.sigXRangeChanged.connect(update_view_range)
            plot.sigYRangeChanged.connect(update_view_range)

        sync_zoom(plot_x, [plot_y, plot_z])
        sync_zoom(plot_y, [plot_x, plot_z])
        sync_zoom(plot_z, [plot_x, plot_y])

    def show_plot_history(self):
        if not self.tracks:
            print("No tracks to plot.")
            return

        self.plot_widget.clear()  # Clear the plot widget before plotting
        plot = self.plot_widget.addPlot()

        # Plot the last 100 samples of each track
        for track in self.tracks:
            times = [m[0][3] for m in track['measurements']][-100:]
            measurements_x = [(m[0][:3])[0] for m in track['measurements']][-100:]
            measurements_y = [(m[0][:3])[1] for m in track['measurements']][-100:]
            measurements_z = [(m[0][:3])[2] for m in track['measurements']][-100:]

            marker_size = self.marker_size  # Use the selected marker size
            plot_color = self.plot_color  # Use the selected plot color

            plot.plot(times, measurements_x, pen=None, symbol='o', symbolSize=marker_size, symbolBrush=plot_color, name=f'Track {track["track_id"]} Measurement X')
            plot.plot(times, measurements_y, pen=None, symbol='o', symbolSize=marker_size, symbolBrush=plot_color, name=f'Track {track["track_id"]} Measurement Y')
            plot.plot(times, measurements_z, pen=None, symbol='o', symbolSize=marker_size, symbolBrush=plot_color, name=f'Track {track["track_id"]} Measurement Z')

        plot.setLabel('bottom', 'Time')
        plot.setTitle("Last 100 Samples of Track History")
        plot.addLegend()

    def mouseMoved(self, evt):
        pos = evt[0]  # using signal proxy turns original arguments into a tuple
        if self.plot_widget.sceneBoundingRect().contains(pos):
            mouse_point = self.plot_widget.plotItem.vb.mapSceneToView(pos)
            index = int(mouse_point.x())
            if 0 <= index < len(self.tracks):
                x_value = mouse_point.x()
                y_value = mouse_point.y()
                self.data_tip.setHtml(f"<div style='text-align: center'><b>X:</b> {x_value:.2f}<br><b>Y:</b> {y_value:.2f}</div>")
                self.data_tip.setPos(mouse_point)

    def update_marker_size(self, size):
        if size == "Small":
            self.marker_size = 5
        elif size == "Medium":
            self.marker_size = 10
        elif size == "Large":
            self.marker_size = 15
        self.update_plot()  # Update the plot to reflect the new marker size

    def update_plot_color(self, color):
        color_map = {
            "Blue": 'b',
            "Red": 'r',
            "Green": 'g',
            "Yellow": 'y',
            "Black": 'k'
        }
        self.plot_color = color_map.get(color, 'b')
        self.update_plot()  # Update the plot to reflect the new color

    def plot_all_modes(self, tracks, plot):
        # Create a 2x2 grid for subplots within the existing canvas
        self.plot_widget.clear()
        plots = self.plot_widget.addLayout(row=0, col=0, rowspan=2, colspan=2)

        # Plot Range vs Time
        range_plot = plots.addPlot(row=0, col=0)
        self.plot_measurements(tracks, range_plot, "Range vs Time", self.selected_track_ids)
        range_plot.setTitle("Range vs Time")
        range_plot.showGrid(x=True, y=True)  # Add grid lines

        # Plot Azimuth vs Time
        azimuth_plot = plots.addPlot(row=0, col=1)
        self.plot_measurements(tracks, azimuth_plot, "Azimuth vs Time", self.selected_track_ids)
        azimuth_plot.setTitle("Azimuth vs Time")
        azimuth_plot.showGrid(x=True, y=True)  # Add grid lines

        # Plot PPI
        ppi_plot = plots.addPlot(row=1, col=0)
        self.plot_ppi(tracks, ppi_plot)
        ppi_plot.setTitle("PPI Plot")
        ppi_plot.showGrid(x=True, y=True)  # Add grid lines

        # Plot RHI
        rhi_plot = plots.addPlot(row=1, col=1)
        self.plot_rhi(tracks, rhi_plot)
        rhi_plot.setTitle("RHI Plot")
        rhi_plot.showGrid(x=True, y=True)  # Add grid lines

    def plot_ppi(self, tracks, plot):
        plot.clear()
        for track in tracks:
            if track['track_id'] not in self.selected_track_ids:
                continue

            measurements = track["measurements"]
            x_coords = [sph2cart(*m[0][:3])[0] for m in measurements]
            y_coords = [sph2cart(*m[0][:3])[1] for m in measurements]

            # PPI plot (x vs y)
            plot.plot(x_coords, y_coords, pen=None, symbol='o', symbolSize=self.marker_size, symbolBrush=self.plot_color, name=f"Track {track['track_id']} PPI")

        plot.setLabel('left', 'Y Coordinate')
        plot.setLabel('bottom', 'X Coordinate')
        plot.setTitle("PPI Plot (360°)")
        plot.addLegend()

    def plot_rhi(self, tracks, plot):
        plot.clear()
        for track in tracks:
            if track['track_id'] not in self.selected_track_ids:
                continue

            measurements = track["measurements"]
            x_coords = [sph2cart(*m[0][:3])[0] for m in measurements]
            z_coords = [sph2cart(*m[0][:3])[2] for m in measurements]

            # RHI plot (x vs z)
            plot.plot(x_coords, z_coords, pen='--', symbol=None, name=f"Track {track['track_id']} RHI")

        plot.setLabel('left', 'Z Coordinate')
        plot.setLabel('bottom', 'X Coordinate')
        plot.setTitle("RHI Plot")
        plot.addLegend()

    def show_config_dialog(self):
        dialog = PlotConfigDialog(self)
        if dialog.exec_():
            plot_config_data = dialog.get_config_data()
            print(f"Plot Configuration Updated: {plot_config_data}")

    def select_filter(self, filter_type):
        self.filter_mode = filter_type
        self.update_filter_selection()

    def update_filter_selection(self):
        self.cv_filter_button.setChecked(self.filter_mode == "CV")
        self.ca_filter_button.setChecked(self.filter_mode == "CA")
        self.ct_filter_button.setChecked(self.filter_mode == "CT")

    def clear_plot(self):
        self.plot_widget.clear()

    def clear_output(self):
        self.output_display.clear()

    def load_csv(self, file_path):
        try:
            with open(file_path, 'r') as file:
                reader = csv.reader(file)
                headers = next(reader)
                self.csv_table.setColumnCount(len(headers))
                self.csv_table.setHorizontalHeaderLabels(headers)

                # Clear existing rows
                self.csv_table.setRowCount(0)

                # Add rows from CSV
                for row_data in reader:
                    row = self.csv_table.rowCount()
                    self.csv_table.insertRow(row)
                    for column, data in enumerate(row_data):
                        self.csv_table.setItem(row, column, QTableWidgetItem(data))
        except Exception as e:
            print(f"Error loading CSV file: {e}")

    def update_track_selection(self):
        # Clear existing checkboxes
        for i in reversed(range(self.track_selection_layout_inner.count())):
            widget = self.track_selection_layout_inner.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        # Add "Select All" checkbox
        self.select_all_checkbox = QCheckBox("Select All Tracks")
        self.select_all_checkbox.setChecked(True)
        self.select_all_checkbox.stateChanged.connect(self.toggle_select_all_tracks)
        self.track_selection_layout_inner.addWidget(self.select_all_checkbox)

        # Add checkboxes for each track
        self.track_checkboxes = []
        for track in self.tracks:
            checkbox = QCheckBox(f"Track ID {track['track_id']}")
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.update_selected_tracks)
            self.track_selection_layout_inner.addWidget(checkbox)
            self.track_checkboxes.append(checkbox)

    def toggle_select_all_tracks(self, state):
        # Update all track checkboxes based on the "Select All" checkbox state
        for checkbox in self.track_checkboxes:
            checkbox.setChecked(state == Qt.Checked)

    def update_selected_tracks(self):
        self.selected_track_ids.clear()
        for checkbox in self.track_checkboxes:
            if checkbox.isChecked():
                track_id = int(checkbox.text().split()[-1])
                self.selected_track_ids.add(track_id)

        # Update the plot with selected tracks
        self.update_plot()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = KalmanFilterGUI()
    ex.show()
    sys.exit(app.exec_())
