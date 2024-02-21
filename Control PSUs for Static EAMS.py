"""
Simple code for controlling RIGOL DP800 series and Keysight B2900 series PSUs. It controls two different PSUs with
two channels each. It was created for quick setting and fine-tuning of the voltages for the four static EAMs used
for shaping the nine mask designs (0-0, 0-1, 0-X, 1-0, 1-1, 1-X, X-0, X-1, X-X). { Used in 2-bit CAM experiment }

Parameters that need to be set:
~ psu_min_voltage -> Minimum voltage for all PSUs
~ psu_max_voltage -> Maximum voltage for all PSUs
~ voltage_increment -> Plus/Minus (+/-) buttons increments
    exp. if voltage_increment = 2 every press of the buttons will be 2 steps in the scale we use
~ accuracy -> Amount of decimal points for setting voltages
    exp. for accuracy = 3 we get 1V / 10^3 = 1mV, so every increment will be voltage_increment-mV
~ psu_ips -> Add the IP of the PSUs
~ button_mapping -> Set the mask state and all the voltages for every PSU channel
"""

import sys
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import pyvisa as visa

psu_min_voltage = 0  # V
psu_max_voltage = 5  # V
psu_current_limit = 0.04  # A
voltage_increment = 1
accuracy = 2

close_psu_on_gui_close = False

voltage_factor = pow(10, accuracy)

psu_ips = {
    1: {'ip_address': '192.168.0.115', 'channel': '1', 'model': 'rigol'},
    2: {'ip_address': '192.168.0.115', 'channel': '2', 'model': 'rigol'},
    3: {'ip_address': '192.168.0.109', 'channel': '1', 'model': 'rigol'},
    4: {'ip_address': '192.168.0.109', 'channel': '2', 'model': 'rigol'}
}

# Slider Title, Minimum Value, Maximum Value, Starting Value
sliders_info = [
    (f'<b>EAM 1: 0V</b>', psu_min_voltage, psu_max_voltage, 0),
    (f'<b>EAM 2: 0V</b>', psu_min_voltage, psu_max_voltage, 0),
    (f'<b>EAM 3: 0V</b>', psu_min_voltage, psu_max_voltage, 0),
    (f'<b>EAM 4: 0V</b>', psu_min_voltage, psu_max_voltage, 0),
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
        1: {'state1': '0', 'state2': '0', 'parameter1': 0, 'parameter2': 4, 'parameter3': 0, 'parameter4': 4},
        2: {'state1': '0', 'state2': '1', 'parameter1': 0, 'parameter2': 4, 'parameter3': 4, 'parameter4': 0},
        3: {'state1': '0', 'state2': 'X', 'parameter1': 0, 'parameter2': 4, 'parameter3': 4, 'parameter4': 4},
        4: {'state1': '1', 'state2': '0', 'parameter1': 4, 'parameter2': 0, 'parameter3': 0, 'parameter4': 4},
        5: {'state1': '1', 'state2': '1', 'parameter1': 4, 'parameter2': 0, 'parameter3': 4, 'parameter4': 0},
        6: {'state1': '1', 'state2': 'X', 'parameter1': 4, 'parameter2': 0, 'parameter3': 4, 'parameter4': 4},
        7: {'state1': 'X', 'state2': '0', 'parameter1': 4, 'parameter2': 4, 'parameter3': 0, 'parameter4': 4},
        8: {'state1': 'X', 'state2': '1', 'parameter1': 4, 'parameter2': 4, 'parameter3': 4, 'parameter4': 0},
        9: {'state1': 'X', 'state2': 'X', 'parameter1': 4, 'parameter2': 4, 'parameter3': 4, 'parameter4': 4}
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
            PSU.write(':OUTP OFF')
        else:
            if reverse_bias:
                PSU.write(f':SOUR:VOLT -{value / voltage_factor}')
                PSU.write(':OUTP ON')
            else:
                PSU.write(f':SOUR:VOLT {value / voltage_factor}')
                PSU.write(':OUTP ON')
    else:
        if value == 0:
            PSU.write(f'SOUR{psu_ips[psu_id]["channel"]}:VOLT 0')
            PSU.write(f':OUTP CH{psu_ips[psu_id]["channel"]}, OFF')
        else:
            PSU.write(f'SOUR{psu_ips[psu_id]["channel"]}:VOLT {value / voltage_factor}')
            PSU.write(f':OUTP CH{psu_ips[psu_id]["channel"]}, ON')


class AppInterface(QWidget):
    def __init__(self):
        super().__init__()

        # Initialize parameters
        self.label = None
        self.mask_buttons = None
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

            slider_label = QLabel(title, self)
            slider_label.setAlignment(Qt.AlignCenter)  # Align text in the center
            slider_title_layout.addWidget(slider_label)
            right_layout.addLayout(slider_title_layout)

            slider_label.setEnabled(False)
            self.slider_labels.append(slider_label)

            checkbox = QCheckBox('Reverse Bias')
            checkbox.stateChanged.connect(
                lambda value, s_label=slider_label, s_id=i: self.toggle_reverse_bias(s_label, s_id))
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
            minus_button.clicked.connect(
                lambda value, s_label=slider_label, s_id=i, s=slider: self.update_slider_value(s_label, s_id, s.value() - voltage_increment, 'button'))
            slider_buttons_layout.addWidget(minus_button)

            minus_button.setEnabled(False)
            self.minus_buttons.append(minus_button)

            i += 1
            right_layout.addLayout(slider_buttons_layout)

        # Text input field and confirm button
        limits_layout = QHBoxLayout()

        # Add label and text input field
        label = QLabel(f'<b>Maximum value (Limit: {psu_max_voltage}V)</b>', self)
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

    def update_slider_value(self, label, slider_id, value, mode):
        if mode == 'button':
            self.sliders[slider_id - 1].setValue(value)
            self.sliders[slider_id - 1].setValue(value)
        reverse_bias = self.reverse_checkboxes[slider_id - 1].isChecked()
        if reverse_bias:
            label.setText(f'<b>{label.text().split(":")[0]}: -{value / voltage_factor}V</b>')
        else:
            label.setText(f'<b>{label.text().split(":")[0]}: {value / voltage_factor}V</b>')
        control_psu(slider_id, value, reverse_bias)

    def toggle_reverse_bias(self, label, slider_id):
        psu_id = slider_id
        PSU = get_correct_psu(psu_id)
        if psu_ips[psu_id]['model'] == 'keysight':
            PSU.write(f':SOUR:VOLT 0')
            PSU.write(':OUTP OFF')
        else:
            PSU.write(f'SOUR{psu_ips[psu_id]["channel"]}:VOLT 0')
            PSU.write(f':OUTP CH{psu_ips[psu_id]["channel"]}, OFF')
        self.sliders[slider_id - 1].setValue(0)
        label.setText(f'<b>{label.text().split(":")[0]}: 0V</b>')

    def on_button_click(self, button_id):
        parameters = get_parameters(button_id)
        self.label.setText(f"<b>State {parameters[4]} - {parameters[5]}</b>")
        i = 0
        for slider in self.sliders:
            slider.setValue(int(parameters[i] * voltage_factor))
            i += 1

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
