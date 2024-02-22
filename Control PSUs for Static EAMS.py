"""
Simple code for controlling RIGOL DP800 series and Keysight B2900 series PSUs. It controls two different PSUs
with two channels each (we use only RIGOL PSUs). It was created for quick setting and fine-tuning of the voltages
for the four static EAMs used for shaping the nine mask designs (0-0, 0-1, 0-X, 1-0, 1-1, 1-X, X-0, X-1, X-X).
{ Used in 2-bit CAM experiment }

Parameters that need to be set:
~ accuracy -> Amount of decimal points for setting voltages
    exp. for accuracy = 3 we get 1V / 10^3 = 1mV, so every step will be in mV
~ set_mask_voltage -> When a mask button is clicked, this is the voltage that will be applied for the closed state
~ close_psu_on_gui_close -> If TRUE all PSUs close their channels when GUI closes
~ psu_current_limit -> Maximum current for all PSUs
~ voltage_increment -> Plus/Minus (+/-) buttons steps in voltage
    exp. if voltage_increment = 2 every press of the buttons will be 2 steps in the scale we use
~ psu_min_voltage -> Minimum voltage for all PSUs
~ psu_max_voltage -> Maximum voltage for all PSUs
~ on_off_button_size -> On/Off state button size (px)
~ font_size -> Font size (px) for label fields
~ psu_ips -> Add the IP of the PSUs
~ button_mapping -> Set the mask state and all the voltages for every PSU channel
"""

import sys
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import pyvisa as visa

accuracy = 2  # voltage decimal points
set_mask_voltage = 4.5  # V
close_psu_on_gui_close = False

psu_current_limit = 0.04  # A
voltage_increment = 1  # step size

psu_min_voltage = 0  # V
psu_max_voltage = 6  # V

on_off_button_size = 16  # pixels
font_size = 16

voltage_factor = pow(10, accuracy)

psu_ips = {
    1: {'ip_address': '192.168.0.115', 'channel': '1', 'model': 'rigol'},
    2: {'ip_address': '192.168.0.115', 'channel': '2', 'model': 'rigol'},
    3: {'ip_address': '192.168.0.109', 'channel': '1', 'model': 'rigol'},
    4: {'ip_address': '192.168.0.109', 'channel': '2', 'model': 'rigol'}
}

# Slider Title, Minimum Value, Maximum Value, Starting Value
sliders_info = [
    (f'<b>EAM 1: +0V</b>', psu_min_voltage, psu_max_voltage, 0),
    (f'<b>EAM 2: +0V</b>', psu_min_voltage, psu_max_voltage, 0),
    (f'<b>EAM 3: +0V</b>', psu_min_voltage, psu_max_voltage, 0),
    (f'<b>EAM 4: +0V</b>', psu_min_voltage, psu_max_voltage, 0),
]

rm = visa.ResourceManager()

PSU_1 = rm.open_resource(f'TCPIP0::{psu_ips[1]["ip_address"]}::inst0::INSTR')
PSU_2 = rm.open_resource(f'TCPIP0::{psu_ips[3]["ip_address"]}::inst0::INSTR')


def get_correct_psu(psu_id):
    PSU = None
    if psu_id == 1 or psu_id == 2:
        PSU = PSU_1
    elif psu_id == 3 or psu_id == 4:
        PSU = PSU_2
    return PSU


def get_parameters(button_id):
    # state(1), state(2), PSU-1 voltage, PSU-2 voltage, PSU-3 voltage, PSU-4 voltage
    button_mapping = {
        1: {'state1': '0', 'state2': '0', 'parameter1': 0, 'parameter2': set_mask_voltage, 'parameter3': 0, 'parameter4': set_mask_voltage},
        2: {'state1': '0', 'state2': '1', 'parameter1': 0, 'parameter2': set_mask_voltage, 'parameter3': set_mask_voltage, 'parameter4': 0},
        3: {'state1': '0', 'state2': 'X', 'parameter1': 0, 'parameter2': set_mask_voltage, 'parameter3': set_mask_voltage, 'parameter4': set_mask_voltage},
        4: {'state1': '1', 'state2': '0', 'parameter1': set_mask_voltage, 'parameter2': 0, 'parameter3': 0, 'parameter4': set_mask_voltage},
        5: {'state1': '1', 'state2': '1', 'parameter1': set_mask_voltage, 'parameter2': 0, 'parameter3': set_mask_voltage, 'parameter4': 0},
        6: {'state1': '1', 'state2': 'X', 'parameter1': set_mask_voltage, 'parameter2': 0, 'parameter3': set_mask_voltage, 'parameter4': set_mask_voltage},
        7: {'state1': 'X', 'state2': '0', 'parameter1': set_mask_voltage, 'parameter2': set_mask_voltage, 'parameter3': 0, 'parameter4': set_mask_voltage},
        8: {'state1': 'X', 'state2': '1', 'parameter1': set_mask_voltage, 'parameter2': set_mask_voltage, 'parameter3': set_mask_voltage, 'parameter4': 0},
        9: {'state1': 'X', 'state2': 'X', 'parameter1': set_mask_voltage, 'parameter2': set_mask_voltage, 'parameter3': set_mask_voltage, 'parameter4': set_mask_voltage}
    }

    if button_id in button_mapping:
        params = button_mapping[button_id]
        parameter1_value = params['parameter1']
        parameter2_value = params['parameter2']
        parameter3_value = params['parameter3']
        parameter4_value = params['parameter4']
        parameter5_value = params['state1']
        parameter6_value = params['state2']
        return parameter1_value, parameter2_value, parameter3_value, parameter4_value, parameter5_value, parameter6_value
    else:
        print('Unknown Button ID')
        exit()


def initialize_psu(psu_id, value):
    PSU = get_correct_psu(psu_id)

    if psu_ips[psu_id]['model'] == 'keysight':
        PSU.write(':SOUR:FUNC:MODE VOLT')
        PSU.write(f':SENS:CURR:PROT {psu_current_limit}')
        PSU.write(':OUTP OFF')
    else:
        PSU.write(f':OUTPut:OVP:VAL CH{psu_ips[psu_id]["channel"]}, 1')
        PSU.write(f':OUTPut:OVP CH{psu_ips[psu_id]["channel"]}, ON')
        PSU.write(f'SOUR{psu_ips[psu_id]["channel"]}:CURR {psu_current_limit}')
        PSU.write(f'SOUR{psu_ips[psu_id]["channel"]}:VOLT {value / voltage_factor}')
        PSU.write(f':OUTP CH{psu_ips[psu_id]["channel"]}, OFF')

    print(f'PSU ID {psu_id} -> Initialized')


def control_psu(psu_id, value, reverse_bias):
    PSU = get_correct_psu(psu_id)

    if psu_ips[psu_id]['model'] == 'keysight':
        if value == 0:
            PSU.write(f':SOUR:VOLT 0')
        else:
            if reverse_bias:
                PSU.write(f':SOUR:VOLT -{value / voltage_factor}')
            else:
                PSU.write(f':SOUR:VOLT {value / voltage_factor}')
    else:
        if value == 0:
            PSU.write(f'SOUR{psu_ips[psu_id]["channel"]}:VOLT 0')
        else:
            PSU.write(f'SOUR{psu_ips[psu_id]["channel"]}:VOLT {value / voltage_factor}')


class AppInterface(QWidget):
    def __init__(self):
        super().__init__()

        # Initialize parameters
        self.label = None
        self.mask_buttons = None
        self.on_off_buttons = None
        self.psu_on_off_state = None
        self.slider_labels = None
        self.reverse_checkboxes = None
        self.sliders = None
        self.plus_buttons = None
        self.minus_buttons = None
        self.max_input_field = None
        self.confirm_button = None

        self.init_ui()

    def init_ui(self):
        self.mask_buttons = []
        self.on_off_buttons = []
        self.psu_on_off_state = []
        self.slider_labels = []
        self.reverse_checkboxes = []
        self.sliders = []
        self.plus_buttons = []
        self.minus_buttons = []

        self.setWindowTitle('Static EAMs')
        self.setGeometry(100, 100, 1000, 400)

        main_layout = QHBoxLayout()
        main_layout.setSpacing(10)  # Set spacing between layouts
        self.setLayout(main_layout)

        # Left side layout (buttons)
        left_layout = QGridLayout()

        self.label = QLabel('<b>Set a State</b>', self)
        self.label.setStyleSheet(f'font-size: {font_size}px;')
        self.label.setAlignment(Qt.AlignCenter)  # Align text in the center
        left_layout.addWidget(self.label, 0, 0, 1, 3)  # Span label across all 3 columns

        self.label.setEnabled(False)

        states = [
            '0-0',
            '0-1',
            '0-X',
            '1-0',
            '1-1',
            '1-X',
            'X-0',
            'X-1',
            'X-X',
        ]

        row = 1
        col = 0
        for i in range(9):
            button = QPushButton(f'{states[i]}', self)
            button.setFixedSize(100, 100)  # Square buttons
            button.clicked.connect(lambda _, button_id=i + 1: self.on_button_click(button_id))
            left_layout.addWidget(button, row, col)

            button.setEnabled(False)
            self.mask_buttons.append(button)

            col += 1
            if col == 3:
                col = 0
                row += 1

        # Right side layout (additional component - sliders)
        right_layout = QVBoxLayout()

        i = 1
        for title, min_val, max_val, init_val in sliders_info:
            slider_title_layout = QHBoxLayout()

            on_off_button = QPushButton('', self)
            on_off_button.setStyleSheet(f'background-color: gray; border-radius: {on_off_button_size // 2}px; padding: 0px;')
            on_off_button.setFixedSize(on_off_button_size, on_off_button_size)
            on_off_button.clicked.connect(lambda value, b_id=i: self.on_off_button_clicked(b_id))
            slider_title_layout.addWidget(on_off_button)

            on_off_button.setEnabled(False)
            self.psu_on_off_state.append(0)
            self.on_off_buttons.append(on_off_button)

            slider_label = QLabel(title, self)
            slider_label.setStyleSheet(f'font-size: {font_size}px;')
            slider_label.setAlignment(Qt.AlignCenter)  # Align text in the center
            slider_title_layout.addWidget(slider_label)
            right_layout.addLayout(slider_title_layout)

            slider_label.setEnabled(False)
            self.slider_labels.append(slider_label)

            checkbox = QCheckBox('+/-')
            checkbox.stateChanged.connect(lambda value, s_label=slider_label, s_id=i: self.toggle_reverse_bias(s_label, s_id))
            slider_title_layout.addWidget(checkbox)

            checkbox.setEnabled(False)
            if psu_ips[i]['model'] != 'keysight':
                checkbox.setVisible(False)
            self.reverse_checkboxes.append(checkbox)

            slider_buttons_layout = QHBoxLayout()
            slider = QSlider(Qt.Horizontal, self)  # Set orientation to horizontal

            slider.setMinimum(min_val * voltage_factor)
            slider.setMaximum(max_val * voltage_factor)
            slider.setValue(int(init_val) * voltage_factor)
            initialize_psu(i, int(init_val))
            slider.setTickPosition(QSlider.TicksBelow)
            slider.setTickInterval(voltage_factor)
            slider.valueChanged.connect(
                lambda value, s_label=slider_label, s_id=i: self.update_slider_value(s_label, s_id, value, 'slider'))
            slider_buttons_layout.addWidget(slider)

            slider.setEnabled(False)
            self.sliders.append(slider)

            plus_button = QPushButton('+', self)
            plus_button.setFixedSize(40, 40)  # Square buttons
            plus_button.clicked.connect(lambda value, s_label=slider_label, s_id=i, s=slider: self.update_slider_value(s_label, s_id, s.value() + voltage_increment, 'button'))
            slider_buttons_layout.addWidget(plus_button)

            plus_button.setEnabled(False)
            self.plus_buttons.append(plus_button)

            minus_button = QPushButton('-', self)
            minus_button.setFixedSize(40, 40)  # Square buttons
            minus_button.clicked.connect(lambda value, s_label=slider_label, s_id=i, s=slider: self.update_slider_value(s_label, s_id, s.value() - voltage_increment, 'button'))
            slider_buttons_layout.addWidget(minus_button)

            minus_button.setEnabled(False)
            self.minus_buttons.append(minus_button)

            right_layout.addLayout(slider_buttons_layout)
            i += 1

        # Text input field and confirm button
        limits_layout = QHBoxLayout()

        # Add label and text input field
        label = QLabel(f'<b>Maximum value (Limit: {psu_max_voltage}V)</b>', self)
        label.setStyleSheet(f'font-size: {font_size}px;')
        label.setAlignment(Qt.AlignCenter)  # Align text in the center
        limits_layout.addWidget(label)

        self.max_input_field = QLineEdit(self)
        limits_layout.addWidget(self.max_input_field)

        self.confirm_button = QPushButton('Confirm', self)
        self.confirm_button.clicked.connect(self.confirm_button_clicked)

        limits_layout.addWidget(self.confirm_button)

        right_layout.addLayout(limits_layout)

        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)

        # Connect returnPressed signal of text input to click signal of button
        self.max_input_field.returnPressed.connect(self.confirm_button.click)

        self.show()

    def on_button_click(self, button_id):
        parameters = get_parameters(button_id)
        self.label.setText(f"<b>State {parameters[4]} - {parameters[5]}</b>")
        i = 0
        for slider in self.sliders:
            slider.setValue(int(parameters[i] * voltage_factor))
            i += 1

    def on_off_button_clicked(self, button_id):
        PSU = get_correct_psu(button_id)
        if self.psu_on_off_state[button_id - 1] == 0:
            if psu_ips[button_id]['model'] == 'keysight':
                PSU.write(':OUTP ON')
            else:
                PSU.write(f':OUTP CH{psu_ips[button_id]["channel"]}, ON')
            self.on_off_buttons[button_id - 1].setStyleSheet(f'background-color: green; border-radius: {on_off_button_size // 2}px; padding: 0px;')
            self.psu_on_off_state[button_id - 1] = 1
        else:
            if psu_ips[button_id]['model'] == 'keysight':
                PSU.write(':OUTP OFF')
            else:
                PSU.write(f':OUTP CH{psu_ips[button_id]["channel"]}, OFF')
            self.on_off_buttons[button_id - 1].setStyleSheet(f'background-color: red; border-radius: {on_off_button_size // 2}px; padding: 0px;')
            self.psu_on_off_state[button_id - 1] = 0

    def update_slider_value(self, label, slider_id, value, mode):
        if mode == 'button':
            self.sliders[slider_id - 1].setValue(value)
            self.sliders[slider_id - 1].setValue(value)
        reverse_bias = self.reverse_checkboxes[slider_id - 1].isChecked()
        if reverse_bias:
            label.setText(f'<b>{label.text().split(":")[0]}: -{value / voltage_factor}V</b>')
        else:
            label.setText(f'<b>{label.text().split(":")[0]}: +{value / voltage_factor}V</b>')
        control_psu(slider_id, value, reverse_bias)

    def toggle_reverse_bias(self, label, slider_id):
        psu_id = slider_id
        PSU = get_correct_psu(psu_id)
        reverse_bias = self.reverse_checkboxes[slider_id - 1].isChecked()
        if psu_ips[psu_id]['model'] == 'keysight':
            PSU.write(f':SOUR:VOLT 0')
            PSU.write(':OUTP OFF')
        else:
            PSU.write(f'SOUR{psu_ips[psu_id]["channel"]}:VOLT 0')
            PSU.write(f':OUTP CH{psu_ips[psu_id]["channel"]}, OFF')
        self.sliders[slider_id - 1].setValue(0)
        if reverse_bias:
            label.setText(f'<b>{label.text().split(":")[0]}: -0V</b>')
        else:
            label.setText(f'<b>{label.text().split(":")[0]}: +0V</b>')

    def confirm_button_clicked(self):
        timer = QTimer(self)
        max_value = self.max_input_field.text()
        psu_id = 1
        accept = False
        for slider in self.sliders:
            if max_value and float(max_value) <= psu_max_voltage:
                slider.setMaximum(int(float(max_value) * voltage_factor))
                if psu_ips[psu_id]['model'] != 'keysight':
                    PSU = get_correct_psu(psu_id)
                    PSU.write(f':OUTPut:OVP:VAL CH{psu_ips[psu_id]["channel"]}, {float(max_value) + 0.1}')
                # Change button background color to green
                self.confirm_button.setStyleSheet('background-color: #90EE90')
                timer.singleShot(500, self.reset_button_color)
                accept = True
            psu_id += 1
        if accept:
            self.label.setEnabled(True)
            for button in self.mask_buttons:
                button.setEnabled(True)
            for on_off_button in self.on_off_buttons:
                on_off_button.setStyleSheet(f'background-color: red; border-radius: {on_off_button_size // 2}px; padding: 0px;')
                on_off_button.setEnabled(True)
            for slider_label in self.slider_labels:
                slider_label.setEnabled(True)
            for slider in self.sliders:
                slider.setEnabled(True)
            for plus_button in self.plus_buttons:
                plus_button.setEnabled(True)
            for minus_button in self.minus_buttons:
                minus_button.setEnabled(True)

    def reset_button_color(self):
        # Revert button background color to default
        self.confirm_button.setStyleSheet('')

    def closeEvent(self, event, **kwargs):
        # Perform cleanup or other actions when the window is closed
        if close_psu_on_gui_close:
            PSU_1.write(':OUTP OFF')
            PSU_2.write(f':OUTP CH1, OFF')
            PSU_2.write(f':OUTP CH2, OFF')
            PSU_3.write(':OUTP OFF')
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = AppInterface()
    sys.exit(app.exec_())
