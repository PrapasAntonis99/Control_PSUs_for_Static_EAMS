"""
Simple code for controlling RIGOL DP800 series PSUs. It controls two different PSUs with two channels each. It was
created for quick setting and fine-tuning of the voltages for the four static EAMs used for shaping the nine mask
designs (0-0, 0-1, 0-X, 1-0, 1-1, 1-X, X-0, X-1, X-X). { Used in 2-bit CAM experiment }

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
import time
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import pyvisa as visa

psu_min_voltage = 0  # V
psu_max_voltage = 8  # V
voltage_increment = 1
accuracy = 2

voltage_factor = pow(10, accuracy)

psu_ips = {
    1: {'ip_address': '192.16.3.8', 'channel': '1'},
    2: {'ip_address': '192.16.3.8', 'channel': '2'},
    3: {'ip_address': '192.16.3.8', 'channel': '1'},
    4: {'ip_address': '192.16.3.8', 'channel': '2'}
}

rm = visa.ResourceManager()

PSU_1 = rm.open_resource(f'TCPIP0::{psu_ips[1]["ip_address"]}::INSTR')
PSU_2 = rm.open_resource(f'TCPIP0::{psu_ips[3]["ip_address"]}::INSTR')


def get_parameters(button_id):
    # state(1), state(2), PSU-1 voltage, PSU-2 voltage, PSU-3 voltage, PSU-4 voltage
    button_mapping = {
        1: {'state1': '0', 'state2': '0', 'parameter1': 5.0, 'parameter2': 5.0, 'parameter3': 1.0, 'parameter4': 9.0},
        2: {'state1': '0', 'state2': '1', 'parameter1': 5.0, 'parameter2': 10.0, 'parameter3': 2.0, 'parameter4': 8.0},
        3: {'state1': '0', 'state2': 'X', 'parameter1': 5.0, 'parameter2': 0.0, 'parameter3': 3.0, 'parameter4': 7.0},
        4: {'state1': '1', 'state2': '0', 'parameter1': 10.0, 'parameter2': 5.0, 'parameter3': 4.0, 'parameter4': 6.0},
        5: {'state1': '1', 'state2': '1', 'parameter1': 10.0, 'parameter2': 10.0, 'parameter3': 5.0, 'parameter4': 5.0},
        6: {'state1': '1', 'state2': 'X', 'parameter1': 10.0, 'parameter2': 0., 'parameter3': 6.0, 'parameter4': 4.0},
        7: {'state1': 'X', 'state2': '0', 'parameter1': 0.0, 'parameter2': 5.0, 'parameter3': 7.0, 'parameter4': 3.0},
        8: {'state1': 'X', 'state2': '1', 'parameter1': 0.0, 'parameter2': 10.0, 'parameter3': 8.0, 'parameter4': 2.0},
        9: {'state1': 'X', 'state2': 'X', 'parameter1': 0.0, 'parameter2': 0.0, 'parameter3': 9.0, 'parameter4': 1.0}
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
        print("Unknown Button ID")
        exit()


def update_value_from_buttons(slider, value):
    slider.setValue(value)


def update_value_from_slider(label, slider_id, value):
    label.setText(f"<b>{label.text().split(':')[0]}: {value / voltage_factor}V</b>")
    control_psu(slider_id, value)


def initialize_psu(psu_id, value):
    PSU = None
    if psu_id == 1 or psu_id == 2:
        PSU = PSU_1
    elif psu_id == 3 or psu_id == 4:
        PSU = PSU_2

    PSU.write(f':OUTPut:OVP:VAL CH{psu_ips[psu_id]["channel"]}, 1')
    PSU.write(f':OUTPut:OVP CH{psu_ips[psu_id]["channel"]}, ON')
    PSU.write(f'SOUR{psu_ips[psu_id]["channel"]}:CURR 0.05')
    PSU.write(f'SOUR{psu_ips[psu_id]["channel"]}:VOLT {value / voltage_factor}')
    PSU.write(f':OUTP CH{psu_ips[psu_id]["channel"]}, OFF')

    if psu_id == 1 or psu_id == 2:
        print(f'PSU 1 - Channel {psu_ips[psu_id]["channel"]} -> Initialized')
    elif psu_id == 3 or psu_id == 4:
        print(f'PSU 2 - Channel {psu_ips[psu_id]["channel"]} -> Initialized')


def control_psu(psu_id, value):
    PSU = None
    if psu_id == 1 or psu_id == 2:
        PSU = PSU_1
    elif psu_id == 3 or psu_id == 4:
        PSU = PSU_2

    if value == 0:
        PSU.write(f'SOUR{psu_ips[psu_id]["channel"]}:VOLT 0')
        PSU.write(f':OUTP CH{psu_ips[psu_id]["channel"]}, OFF')
    else:
        PSU.write(f'SOUR{psu_ips[psu_id]["channel"]}:VOLT {value / voltage_factor}')
        PSU.write(f':OUTP CH{psu_ips[psu_id]["channel"]}, ON')

    # print(f"PSU {psu_id} -> {value / voltage_factor}")


class ButtonMessageApp(QWidget):
    def __init__(self):
        super().__init__()

        # Initialize parameters
        self.label = None
        self.slider_label = None
        self.sliders = None
        self.max_input_field = None
        self.confirm_button = None

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Set Mask Voltages')
        self.setGeometry(100, 100, 1000, 300)

        main_layout = QHBoxLayout()
        main_layout.setSpacing(10)  # Set spacing between layouts
        self.setLayout(main_layout)

        # Left side layout (buttons)
        left_layout = QGridLayout()

        self.label = QLabel("<b>Set a State</b>", self)
        self.label.setAlignment(Qt.AlignCenter)  # Align text in the center
        left_layout.addWidget(self.label, 0, 0, 1, 3)  # Span label across all 3 columns

        states = [
            "0-0",
            "0-1",
            "0-X",
            "1-0",
            "1-1",
            "1-X",
            "X-0",
            "X-1",
            "X-X",
        ]

        row = 1
        col = 0
        for i in range(9):
            button = QPushButton(f'{states[i]}', self)
            button.setFixedSize(100, 100)  # Square buttons
            button.clicked.connect(lambda _, button_id=i + 1: self.on_button_click(button_id))
            left_layout.addWidget(button, row, col)
            col += 1
            if col == 3:
                col = 0
                row += 1

        # Right side layout (additional component - sliders)
        right_layout = QVBoxLayout()

        # Slider Title, Minimum Value, Maximum Value, Starting Value
        sliders_info = [
            (f"<b>EAM 1: 0V</b>", psu_min_voltage, psu_max_voltage, 0),
            (f"<b>EAM 2: 0V</b>", psu_min_voltage, psu_max_voltage, 0),
            (f"<b>EAM 3: 0V</b>", psu_min_voltage, psu_max_voltage, 0),
            (f"<b>EAM 4: 0V</b>", psu_min_voltage, psu_max_voltage, 0),
        ]
        self.sliders = []

        i = 1
        for title, min_val, max_val, init_val in sliders_info:
            slider_title_layout = QHBoxLayout()

            self.slider_label = QLabel(title, self)
            self.slider_label.setAlignment(Qt.AlignCenter)  # Align text in the center
            slider_title_layout.addWidget(self.slider_label)
            right_layout.addLayout(slider_title_layout)

            slider_buttons_layout = QHBoxLayout()
            slider = QSlider(Qt.Horizontal, self)  # Set orientation to horizontal

            slider.setMinimum(min_val * voltage_factor)
            slider.setMaximum(max_val * voltage_factor)
            slider.setValue(int(init_val) * voltage_factor)
            initialize_psu(i, int(init_val))
            slider.setTickPosition(QSlider.TicksBelow)
            slider.setTickInterval(voltage_factor)
            slider.valueChanged.connect(
                lambda value, slider_label=self.slider_label, slider_id=i: update_value_from_slider(slider_label,
                                                                                                    slider_id, value))
            slider_buttons_layout.addWidget(slider)

            plus_button = QPushButton("+", self)
            plus_button.setFixedSize(40, 40)  # Square buttons
            plus_button.clicked.connect(lambda _, s=slider: update_value_from_buttons(s, s.value() + voltage_increment))
            slider_buttons_layout.addWidget(plus_button)

            minus_button = QPushButton("-", self)
            minus_button.setFixedSize(40, 40)  # Square buttons
            minus_button.clicked.connect(
                lambda _, s=slider: update_value_from_buttons(s, s.value() - voltage_increment))
            slider_buttons_layout.addWidget(minus_button)

            self.sliders.append(slider)
            i += 1
            right_layout.addLayout(slider_buttons_layout)

        # Text input field and confirm button
        limits_layout = QHBoxLayout()

        # Add label and text input field
        label = QLabel(f"<b>Maximum value (Limit: {psu_max_voltage}V)</b>", self)
        label.setAlignment(Qt.AlignCenter)  # Align text in the center
        limits_layout.addWidget(label)

        self.max_input_field = QLineEdit(self)
        limits_layout.addWidget(self.max_input_field)

        self.confirm_button = QPushButton("Confirm", self)
        self.confirm_button.clicked.connect(self.confirm_button_clicked)

        limits_layout.addWidget(self.confirm_button)

        right_layout.addLayout(limits_layout)

        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)

        self.show()

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
        for slider in self.sliders:
            if max_value and int(max_value) <= psu_max_voltage:
                slider.setMaximum(int(max_value) * voltage_factor)
                if psu_id == 1 or psu_id == 2:
                    PSU_1.write(f':OUTPut:OVP:VAL CH{psu_ips[psu_id]["channel"]}, {max_value}')
                elif psu_id == 3 or psu_id == 4:
                    PSU_2.write(f':OUTPut:OVP:VAL CH{psu_ips[psu_id]["channel"]}, {max_value}')
                # Change button background color to green
                self.confirm_button.setStyleSheet("background-color: #90EE90")
                timer.singleShot(500, self.reset_button_color)
            psu_id += 1

    def reset_button_color(self):
        # Revert button background color to default
        self.confirm_button.setStyleSheet('')

    def closeEvent(self, event):
        # Perform cleanup or other actions when the window is closed
        PSU_1.write(f':OUTP CH1, OFF')
        PSU_1.write(f':OUTP CH2, OFF')
        PSU_2.write(f':OUTP CH1, OFF')
        PSU_2.write(f':OUTP CH2, OFF')
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ButtonMessageApp()
    sys.exit(app.exec_())
