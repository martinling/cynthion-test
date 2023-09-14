from colorama import Fore, Back, Style
from selftest import InteractiveSelftest, \
    REGISTER_LEDS, REGISTER_CON_VBUS_EN, REGISTER_AUX_VBUS_EN, \
    REGISTER_AUX_TYPEC_CTL_ADDR, REGISTER_AUX_TYPEC_CTL_VALUE, \
    REGISTER_TARGET_TYPEC_CTL_ADDR, REGISTER_TARGET_TYPEC_CTL_VALUE, \
    REGISTER_PWR_MON_ADDR, REGISTER_PWR_MON_VALUE, \
    REGISTER_PASS_CONTROL, REGISTER_PASS_AUX, REGISTER_PASS_TARGET_C, \
    REGISTER_AUX_SBU, REGISTER_TARGET_SBU, REGISTER_BUTTON_USER
from apollo_fpga import ApolloDebugger
from tps55288 import TPS55288
from greatfet import *
from time import time, sleep
import colorama
import inspect
import usb1
import os

gpio_allocations = dict(
    BOOST_EN = ('J2_P25', 0),
    BOOST_VBUS_AUX = ('J2_P16', 0),
    BOOST_VBUS_CON = ('J2_P15', 0),
    BOOST_VBUS_TC = ('J2_P34', 0),
    CC1_test = ('J1_P17', None),
    CC2_test = ('J1_P18', None),
    CC_PULL_UP = ('J1_P7', 1),
    D_S_1 = ('J1_P3', 0),
    D_S_2 = ('J1_P19', 0),
    D_S_3 = ('J1_P26', 0),
    D_OEn_1 = ('J1_P4', 1),
    D_OEn_2 = ('J1_P20', 1),
    D_OEn_3 = ('J1_P28', 1),
    GND_EN = ('J2_P31', 0),
    GND_EUT = ('J2_P33', None),
    SBU1_test = ('J1_P30', None),
    SBU2_test = ('J1_P32', None),
    D_TEST_PLUS = ('J1_P6', None),
    D_TEST_MINUS = ('J1_P8', None),
    V_DIV = ('J1_P9', 0),
    V_DIV_MULT = ('J1_P5', 0),
    REF_LED_EN = ('J1_P35', 0),
    MUX1_EN = ('J1_P15', 0),
    MUX1_A0 = ('J1_P14', 0),
    MUX1_A1 = ('J1_P13', 0),
    MUX1_A2 = ('J1_P12', 0),
    MUX1_A3 = ('J1_P10', 0),
    MUX2_EN = ('J1_P23', 0),
    MUX2_A0 = ('J1_P24', 0),
    MUX2_A1 = ('J1_P21', 0),
    MUX2_A2 = ('J1_P22', 0),
    MUX2_A3 = ('J1_P25', 0),
    TEST_5V = ('J1_P37', 0),
    TEST_20V = ('J1_P33', 0),
    TA_DIS = ('J1_P34', 1),
    HOST_VBUS_CON = ('J2_P13', 0),
    HOST_VBUS_AUX = ('J2_P14', 0),
    SIG1_OEn = ('J2_P24', 1),
    SIG2_OEn = ('J2_P22', 1),
    SIG1_S = ('J2_P23', 0),
    SIG2_S = ('J2_P27', 0),
    nBTN_PROGRAM = ('J1_P27', None),
    nBTN_RESET = ('J1_P29', None),
)

mux_channels = {
    '+1V1': (0, 7),
    '+2V5': (1, 9),
    '+3V3': (1, 8),
    '+5V': (0, 13),
    'VCCRAM': (1, 11),
    'CONTROL_PHY_1V8': (1, 1),
    'CONTROL_PHY_3V3': (0, 6),
    'AUX_PHY_1V8': (1, 0),
    'AUX_PHY_3V3': (1, 2),
    'TARGET_PHY_1V8': (1, 10),
    'TARGET_PHY_3V3': (1, 12),
    'TARGET_A_VBUS': (1, 3),
    'VBUS_CON': (1, 4),
    'VBUS_AUX': (1, 5),
    'VBUS_TA': (1, 7),
    'VBUS_TC': (1, 6),
    'CC1_test': (0, 3),
    'CC2_test': (0, 2),
    'D2_Vf': (0, 1),
    'D3_Vf': (0, 0),
    'D4_Vf': (0, 9),
    'D5_Vf': (0, 8),
    'D6_Vf': (0, 11),
    'D7_Vf': (0, 10),
    'D10_Vf': (0, 12),
    'D11_Vf': (0, 4),
    'D12_Vf': (0, 14),
    'D13_Vf': (0, 5),
    'D14_Vf': (0, 15),
    'CDC': (1, 15),
    'SPARE1': (1, 13),
    'SPARE2': (1, 14),
}

vbus_channels = {
    'CONTROL':  'VBUS_CON',
    'AUX':      'VBUS_AUX',
    'TARGET-A': 'VBUS_TA',
    'TARGET-C': 'VBUS_TC',
}

vbus_registers = {
    'CONTROL': REGISTER_CON_VBUS_EN,
    'AUX':     REGISTER_AUX_VBUS_EN,
}

passthrough_registers = {
    'CONTROL':  REGISTER_PASS_CONTROL,
    'AUX':      REGISTER_PASS_AUX,
    'TARGET-C': REGISTER_PASS_TARGET_C,
}

typec_registers = {
    'AUX': (REGISTER_AUX_TYPEC_CTL_ADDR, REGISTER_AUX_TYPEC_CTL_VALUE),
    'TARGET-C': (REGISTER_TARGET_TYPEC_CTL_ADDR, REGISTER_TARGET_TYPEC_CTL_VALUE),
}

sbu_registers = {
    'AUX': REGISTER_AUX_SBU,
    'TARGET-C': REGISTER_TARGET_SBU
}

mon_voltage_registers = {
    'CONTROL': 0x08,
    'AUX': 0x07,
    'TARGET-C': 0x0A,
    'TARGET-A': 0x09,
}

mon_current_registers = {
    'CONTROL': 0x0C,
    'AUX': 0x0B,
    'TARGET-C': 0x0E,
    'TARGET-A': 0x0D,
}

gf = GreatFET()

for name, (position, state) in gpio_allocations.items():
    pin = gf.gpio.get_pin(position)
    globals()[name] = pin
    if state is None:
        pin.input()
    elif state:
        pin.high()
    else:
        pin.low()

BOOST_EN.high()
boost = TPS55288(gf)
boost.disable()

colorama.init()

context = usb1.USBContext()

indent = 0

def reset():
    for name, (position, state) in gpio_allocations.items():
        pin = globals()[name]
        if state is None:
            pin.input()
        elif state:
            pin.high()
        else:
            pin.low()

def msg(text, end, flush=False):
    print(("  " * indent) + "• " + text + Style.RESET_ALL, end=end, flush=flush)

def item(text):
    msg(text, "\n")

def begin(text):
    global indent
    msg(text, ":\n")
    indent += 1

def end():
    global indent
    indent -= 1

def start(text):
    msg(text, "... ", flush=True)

def done():
    print(Fore.GREEN + "OK" + Style.RESET_ALL)

def request(text):
    print(Fore.BLUE)
    print(" === Please " + text + " and press ENTER === " + Style.RESET_ALL)
    input()

def fail():
    print(Fore.RED + "FAIL" + Style.RESET_ALL)

def todo(text):
    item(Fore.YELLOW + "TODO" + Style.RESET_ALL + ": " + text)

def info(text):
    return Fore.CYAN + str(text) + Style.RESET_ALL

def begin_short_check(a, b, port):
    begin(f"Checking for {info(a)} to {info(b)} short on {info(port)}")

def check_for_shorts(port):
    begin(f"Checking for shorts on {info(port)}")

    connect_tester_to(port)
    connect_tester_cc_sbu_to(port)

    begin_short_check('VBUS', 'GND', port)
    set_pin('GND_EUT', True)
    test_vbus(port, 0, 0.05)
    set_pin('GND_EUT', None)
    end()

    begin_short_check('VBUS', 'SBU2', port)
    set_pin('SBU2_test', True)
    test_vbus(port, 0.0, 0.05)
    set_pin('SBU2_test', None)
    end()

    begin_short_check('SBU2', 'CC1', port)
    set_pin('SBU2_test', True)
    test_voltage('CC1_test', 0.0, 0.1)
    set_pin('SBU2_test', None)
    end()

    todo("CC1/D- short check")

    todo("D-/D+ short check")

    todo("D+/SBU1 short check")

    begin_short_check('SBU1', 'CC2', port)
    set_pin('SBU1_test', True)
    test_voltage('CC2_test', 0.0, 0.1)
    set_pin('SBU1_test', None)
    end()

    begin_short_check('CC2', 'VBUS', port)
    set_pin('CC2_test', True)
    test_vbus(port, 0.0, 0.05)
    set_pin('CC2_test', None)
    end()

    connect_tester_cc_sbu_to(None)

    end()

def connect_grounds():
    item("Connecting EUT ground to Tycho ground")
    GND_EN.high()

def connect_tester_to(port):
    todo(f"Connecting tester D+/D- to {info(port)}")

def connect_host_to(port):
    item(f"Connecting host D+/D- to {info(port)}")
    D_OEn_1.high()
    D_OEn_2.high()
    D_OEn_3.high()
    if port is None:
        return
    D_S_1.set_state(0)
    D_S_2.set_state(port != 'CONTROL')
    D_S_3.set_state(port == 'TARGET-C')
    D_OEn_1.low()
    D_OEn_2.low()
    D_OEn_3.low()

def begin_cc_measurement(port):
    connect_tester_cc_sbu_to(port)
    V_DIV.low()
    V_DIV_MULT.low()
    CC_PULL_UP.low()
    CC1_test.input()
    CC2_test.input()

def end_cc_measurement():
    CC_PULL_UP.high()
    connect_tester_cc_sbu_to(None)

def check_cc_resistances(port):
    begin(f"Checking CC resistances on {info(port)}")
    begin_cc_measurement(port)
    for pin in ('CC1', 'CC2'):
        check_cc_resistance(pin, 4.1, 6.1)
    end_cc_measurement()
    end()

def check_cc_resistance(pin, minimum, maximum):
    channel = f'{pin}_test'
    mux_select(channel)
    samples = gf.adc.read_samples(1000)
    mux_disconnect()
    voltage = (3.3 / 1024) * sum(samples) / len(samples)
    item(f"Checking voltage on {info(channel)}: {info(f'{voltage:.2f} V')}")
    resistance = (3.3 * 30 - voltage * 35.1) / (voltage - 3.3)
    return test_value("resistance", pin, resistance, 'kΩ', minimum, maximum, ignore=True)

def test_leakage(port):
    test_vbus(port, 0, 0.2)

def set_boost_supply(voltage, current):
    item(f"Setting DC-DC converter to {info(f'{voltage:.2f} V')} {info(f'{current:.2f} A')}")
    boost.set_voltage(voltage)
    boost.set_current_limit(current)
    boost.enable()

def connect_boost_supply_to(port):
    if port is None:
        item(f"Disconnecting DC-DC converter")
    else:
        item(f"Connecting DC-DC converter to {info(port)}")
    BOOST_VBUS_AUX.low()
    BOOST_VBUS_CON.low()
    BOOST_VBUS_TC.low()
    if port == 'AUX':
        BOOST_VBUS_AUX.high()
    if port == 'CONTROL':
        BOOST_VBUS_CON.high()
    if port == 'TARGET-C':
        BOOST_VBUS_TC.high()

def mux_select(channel):
    mux, pin = mux_channels[channel]

    MUX1_EN.low()
    MUX2_EN.low()

    if mux == 0:
        MUX1_A0.write(pin & 1)
        MUX1_A1.write(pin & 2)
        MUX1_A2.write(pin & 4)
        MUX1_A3.write(pin & 8)
        MUX1_EN.high()
    else:
        MUX2_A0.write(pin & 1)
        MUX2_A1.write(pin & 2)
        MUX2_A2.write(pin & 4)
        MUX2_A3.write(pin & 8)
        MUX2_EN.high()

def mux_disconnect():
    MUX1_EN.low()
    MUX2_EN.low()

def test_value(qty, src, value, unit, minimum, maximum, ignore=False):
    message = f"Checking {qty} on {info(src)} is within {info(f'{minimum:.2f}')} to {info(f'{maximum:.2f} {unit}')}: "
    result = f"{value:.2f} {unit}"
    if value < minimum:
        item(message + Fore.RED + result)
        if not ignore:
            raise ValueError(f"{qty} too low on {src}: {value:.2f} {unit}, minimum was {minimum:.2f} {unit}")
    elif value > maximum:
        item(message + Fore.RED + result)
        if not ignore:
            raise ValueError(f"{qty} too high on {src}: {value:.2f} {unit}, maximum was {maximum:.2f} {unit}")
    else:
        item(message + Fore.GREEN + result)
    return value

def test_voltage(channel, minimum, maximum):
    if maximum <= 6.6:
        V_DIV.high()
        V_DIV_MULT.low()
        scale = 3.3 / 1024 * 2
    else:
        V_DIV.low()
        V_DIV_MULT.high()
        scale = 3.3 / 1024 * (30 + 5.1) / 5.1

    mux_select(channel)
    samples = gf.adc.read_samples(1000)
    mux_disconnect()
    voltage = scale * sum(samples) / len(samples)

    return test_value("voltage", channel, voltage, 'V', minimum, maximum)

def set_pin(pin, level):
    required = ('input' if level is None else
        'output high' if level else 'output low')
    item(f"Setting pin {info(pin)} to {info(required)}")
    pin = globals()[pin]
    if level is None:
        pin.input()
    elif level:
        pin.high()
    else:
        pin.low()

def test_pin(pin, level):
    required = 'high' if level else 'low'
    start(f"Checking pin {info(pin)} is {info(required)}")
    value = globals()[pin].input()
    found = 'high' if value else 'low'
    if value == level:
        done()
    else:
        fail()
        raise ValueError(f"Pin {pin} is {found}, should be {required}")

def disconnect_supply_and_discharge(port):
    item(f"Disconnecting supply and discharging {info(port)}")
    boost.disable()
    mux_select(vbus_channels[port])
    V_DIV.high()
    V_DIV_MULT.high()
    sleep(0.5)
    V_DIV.low()
    V_DIV_MULT.low()
    mux_disconnect()

def test_clock():
    todo(f"Checking clock frequency")

def run_command(cmd):
    result = os.system(cmd + " > /dev/null 2>&1")
    if result != 0:
        raise RuntimeError(f"Command '{cmd}' failed with exit status {result}")

def flash_bootloader():
    start(f"Flashing Saturn-V bootloader to MCU via SWD")
    run_command('gdb-multiarch --batch -x flash-bootloader.gdb')
    done()

def flash_firmware():
    start(f"Flashing Apollo to MCU via DFU")
    run_command('dfu-util -a 0 -d 1d50:615c -D luna_d11-firmware.bin')
    done()

def test_saturnv_present():
    begin(f"Checking for Saturn-V")
    device = find_device(0x1d50, 0x615c)
    match_device(device, "Great Scott Gadgets", "LUNA Saturn-V RCM Bootloader")
    end()

def test_apollo_present():
    begin(f"Checking for Apollo")
    device = find_device(0x1d50, 0x615c)
    match_device(device, "Great Scott Gadgets", "Apollo Debugger")
    end()

def test_bridge_present():
    begin(f"Checking for flash bridge")
    device = find_device(0x1d50, 0x615b)
    match_device(device, "LUNA", "Configuration Flash bridge")
    end()

def test_analyzer_present():
    begin(f"Checking for analyzer")
    device = find_device(0x1d50, 0x615b)
    match_device(device, "LUNA", "USB Analyzer")
    end()

def simulate_program_button():
    begin(f"Simulating pressing the {info('PROGRAM')} button")
    set_pin('nBTN_PROGRAM', False)
    sleep(0.1)
    set_pin('nBTN_PROGRAM', None)
    end()

def simulate_reset_button():
    begin(f"Simulating pressing the {info('RESET')} button")
    set_pin('nBTN_RESET', False)
    sleep(0.1)
    set_pin('nBTN_RESET', None)
    end()

def set_debug_leds(apollo, bitmask):
    start(f"Setting debug LEDs to 0b{bitmask:05b}")
    apollo.set_led_pattern(bitmask)
    done()

def set_fpga_leds(apollo, bitmask):
    start(f"Setting FPGA LEDs to 0b{bitmask:05b}")
    apollo.registers.register_write(REGISTER_LEDS, bitmask)
    assert(apollo.registers.register_read(REGISTER_LEDS) == bitmask)
    done()

def test_leds(apollo, group, leds, set_leds, off_min, off_max):
    begin(f"Testing {group} LEDs")
    for i in range(len(leds)):
        begin(f"Testing {group} LED {info(i)}")
        # Turn on LED
        set_leds(apollo, 1 << i)

        # Check that this and only this LED is on, with the correct voltage.
        for j, (testpoint, minimum, maximum) in enumerate(leds):
            if i == j:
                test_voltage(testpoint, minimum, maximum)
            else:
                test_voltage(testpoint, off_min, off_max)
        end()

    end()

def test_jtag_scan(apollo):
    begin("Checking JTAG scan chain")
    with apollo.jtag as jtag:
        devices = [(device.idcode(), device.description())
            for device in jtag.enumerate()]
    for idcode, desc in devices:
        item(f"Found {info(f'0x{idcode:8X}')}: {info(desc)}")
    if devices != [(0x41111043, "Lattice LFE5U-25F ECP5 FPGA")]:
        raise ValueError("JTAG scan chain did not include expected devices")
    end()

def unconfigure_fpga(apollo):
    with apollo.jtag as jtag:
        programmer = apollo.create_jtag_programmer(jtag)
        start("Unconfiguring FPGA")
        programmer.unconfigure()
        done()

def test_flash_id(apollo, expected_mfg, expected_part):
    begin("Checking flash chip ID")
    with apollo.jtag as jtag:
        programmer = apollo.create_jtag_programmer(jtag)
        start("Reading flash ID")
        mfg, part = programmer.read_flash_id()
        done()
    start(f"Checking manufacturer ID is {info(f'0x{expected_mfg:02X}')}")
    if mfg != expected_mfg:
        raise ValueError(f"Wrong flash chip manufacturer ID: 0x{mfg:02X}")
    done()
    start(f"Checking part ID is {info(f'0x{expected_part:02X}')}")
    if part != expected_part:
        raise ValueError(f"Wrong flash chip part ID: 0x{part:02X}")
    done()
    end()

def flash_bitstream(apollo, filename):
    begin(f"Writing {info(filename)} to FPGA configuration flash")
    bitstream = open(filename, 'rb').read()
    start("Erasing flash")
    with apollo.jtag as jtag:
        programmer = apollo.create_jtag_programmer(jtag)
        programmer.erase_flash()
    done()
    start("Writing flash")
    with apollo.jtag as jtag:
        programmer = apollo.create_jtag_programmer(jtag)
        programmer.flash(bitstream)
    done()
    end()

def configure_fpga(apollo, filename):
    start(f"Configuring FPGA with {info(filename)}")
    bitstream = open(filename, 'rb').read()
    with apollo.jtag as jtag:
        programmer = apollo.create_jtag_programmer(jtag)
        programmer.configure(bitstream)
    done()

def request_control_handoff_to_fpga(apollo):
    start(f"Requesting MCU handoff {info('CONTROL')} port to FPGA")
    apollo.honor_fpga_adv()
    apollo.close()
    done()

def find_device(vid, pid):
    start(f"Looking for device with VID {info(f'0x{vid:04x}')} " +
          f"and PID {info(f'0x{pid:04x}')}")
    device = context.getByVendorIDAndProductID(vid, pid)
    if device is None:
        fail()
        raise ValueError("Device not found")
    else:
        done()
    return device

def match_device(device, manufacturer, product):
    start(f"Checking manufacturer is {info(manufacturer)}")
    if device.getManufacturer() != manufacturer:
        raise ValueError("Wrong manufacturer string")
    done()
    start(f"Checking product is {info(product)}")
    if device.getProduct() != product:
        raise ValueError("Wrong product string")
    done()
    item(f"Device serial is {info(device.getSerialNumber())}")

def run_self_test(apollo):
    begin("Running self test")
    selftest = InteractiveSelftest()
    selftest._MustUse__used = True
    selftest.dut = apollo
    for method in [
        selftest.test_debug_connection,
        selftest.test_sideband_phy,
        selftest.test_host_phy,
        selftest.test_target_phy,
        selftest.test_hyperram,
        selftest.test_aux_typec_controller,
        selftest.test_target_typec_controller,
        selftest.test_power_monitor_controller,
    ]:
        description = method.__name__.replace("test_", "")
        try:
            start(description)
            method(apollo)
            done()
        except Exception as e:
            fail()
            raise RuntimeError(f"{description} self-test failed")
    end()

def test_usb_hs(port):
    begin(f"Testing USB HS comms on {info(port)}")
    connect_host_to(port)
    sleep(0.8)

    pids = {'CONTROL': 0x0001, 'AUX': 0x0002, 'TARGET-C': 0x0003}

    BULK_ENDPOINT_NUMBER = 1
    TEST_DATA_SIZE = 1 * 1024 * 1024
    TEST_TRANSFER_SIZE = 16 * 1024
    TRANSFER_QUEUE_DEPTH = 16

    total_data_exchanged = 0
    failed_out = False

    messages = {
        1: "error'd out",
        2: "timed out",
        3: "was prematurely cancelled",
        4: "was stalled",
        5: "lost the device it was connected to",
        6: "sent more data than expected."
    }

    def should_terminate():
        return (total_data_exchanged > TEST_DATA_SIZE) or failed_out

    def transfer_completed(transfer: usb1.USBTransfer):
        nonlocal total_data_exchanged, failed_out

        status = transfer.getStatus()

        # If the transfer completed.
        if status in (usb1.TRANSFER_COMPLETED,):

            # Count the data exchanged in this packet...
            total_data_exchanged += transfer.getActualLength()

            # ... and if we should terminate, abort.
            if should_terminate():
                return

            # Otherwise, re-submit the transfer.
            transfer.submit()

        else:
            failed_out = status

    # Grab a reference to our device...
    handle = find_device(0x1209, pids[port]).open()

    # ... and claim its bulk interface.
    handle.claimInterface(0)

    # Submit a set of transfers to perform async comms with.
    active_transfers = []
    for _ in range(TRANSFER_QUEUE_DEPTH):

        # Allocate the transfer...
        transfer = handle.getTransfer()
        transfer.setBulk(0x80 | BULK_ENDPOINT_NUMBER, TEST_TRANSFER_SIZE, callback=transfer_completed, timeout=1000)

        # ... and store it.
        active_transfers.append(transfer)

    # Start our benchmark timer.
    start_time = time()

    # Submit our transfers all at once.
    for transfer in active_transfers:
        transfer.submit()

    # Run our transfers until we get enough data.
    while not should_terminate():
        context.handleEvents()

    # Figure out how long this took us.
    end_time = time()
    elapsed = end_time - start_time

    # Cancel all of our active transfers.
    for transfer in active_transfers:
        if transfer.isSubmitted():
            transfer.cancel()

    # If we failed out; indicate it.
    if failed_out:
        raise RuntimeError(
            f"Test failed because a transfer {messages[failed_out]}.")

    speed = total_data_exchanged / elapsed / 1000000

    test_value("transfer rate", port, speed, 'MB/s', 45, 50)

    end()

    return handle

def connect_tester_cc_sbu_to(port):
    item(f"Connecting tester CC/SBU lines to {info(port)}")
    SIG1_OEn.high()
    SIG2_OEn.high()
    if port is None:
        return
    SIG1_S.set_state(port == 'CONTROL')
    SIG2_S.set_state(port == 'TARGET-C')
    SIG1_OEn.low()
    SIG2_OEn.low()

def write_register(apollo, reg, value, verify=False):
    apollo.registers.register_write(reg, value)
    if verify:
        readback = apollo.registers.register_read(reg)
        if readback != value:
            raise ValueError(
                f"Wrote 0x{value:02X} to register {reg} "
                f"but read back 0x{readback:02X}")

def read_register(apollo, reg):
    return apollo.registers.register_read(reg)

def enable_supply_input(apollo, port, enable):
    start(f"{'Enabling' if enable else 'Disabling'} supply input on {info(port)}")
    write_register(apollo, vbus_registers[port], enable)
    done()

def set_cc_levels(apollo, port, levels):
    start(f"Setting CC levels on {info(port)} to {info(levels)}")
    value = 0b01 * levels[0] | 0b10 * levels[1]
    reg_addr, reg_val = typec_registers[port]
    write_register(apollo, reg_addr, (0x02 << 8) | 1)
    write_register(apollo, reg_val, value)
    done()

def set_sbu_levels(apollo, port, levels):
    start(f"Setting SBU levels on {info(port)} to {info(levels)}")
    value = 0b01 * levels[0] | 0b10 * levels[1]
    write_register(apollo, sbu_registers[port], value)
    done()

def connect_host_supply_to(*ports):
    if ports == (None,):
        item("Disconnecting host supply")
    else:
        item(f"Connecting host supply to {str.join(' and ', map(info, ports))}")
    if 'CONTROL' in ports:
        HOST_VBUS_CON.high()
    if 'AUX' in ports:
        HOST_VBUS_AUX.high()
    if 'CONTROL' not in ports:
        HOST_VBUS_CON.low()
    if 'AUX' not in ports:
        HOST_VBUS_AUX.low()

def request_target_a_cable():
    print()
    print(
        Fore.BLUE +
        "=== Connect cable to Target-A port on EUT and press ENTER ===" +
        Style.RESET_ALL)
    input()

def set_passthrough(apollo, port, enable):
    action = 'Enabling' if enable else 'Disabling'
    start(f"{action} VBUS passthrough for {info(port)}")
    write_register(apollo, passthrough_registers[port], enable)
    done()

def set_target_passive():
    todo(f"Setting target PHY to passive mode")

def test_usb_fs():
    todo(f"Testing USB FS comms through target passthrough")

def test_vbus(input_port, vmin, vmax):
    test_voltage(vbus_channels[input_port], vmin, vmax)

def configure_power_monitor(apollo):
    start("Configuring I2C power monitor")
    write_register(apollo, REGISTER_PWR_MON_ADDR, (0x1D << 8) | 2)
    write_register(apollo, REGISTER_PWR_MON_VALUE, 0x5500)
    done()

def refresh_power_monitor(apollo):
    write_register(apollo, REGISTER_PWR_MON_ADDR, (0x1F << 8))
    write_register(apollo, REGISTER_PWR_MON_VALUE, 0)
    sleep(0.01)

def test_eut_voltage(apollo, port, vmin, vmax):
    refresh_power_monitor(apollo)
    reg = mon_voltage_registers[port]
    write_register(apollo, REGISTER_PWR_MON_ADDR, (reg << 8) | 2)
    value = read_register(apollo, REGISTER_PWR_MON_VALUE)
    voltage = value * 32 / 65536
    return test_value("EUT voltage", port, voltage, 'V', vmin, vmax)

def test_eut_current(apollo, port, imin, imax):
    refresh_power_monitor(apollo)
    reg = mon_current_registers[port]
    write_register(apollo, REGISTER_PWR_MON_ADDR, (reg << 8) | 2)
    value = read_register(apollo, REGISTER_PWR_MON_VALUE)
    if value >= 32768:
        value -= 65536

    # ¯\_(ツ)_/¯
    if port == 'CONTROL' and value > 0:
        value *= 1.87

    voltage = value * 0.1 / 32678
    resistance = 0.02
    current = voltage / resistance
    return test_value("EUT current", port, current, 'A', imin, imax)

def test_vbus_distribution(apollo, voltage, load_resistance,
        load_pin, passthrough, input_port):
    vmin_off = 0.0
    vmax_off = 0.2
    imin_off = -0.01
    imax_off =  0.01
    src_resistance = 0.08
    input_cable_resistance = 0.04
    eut_resistance = 0.12
    output_cable_resistance = 0.07

    if passthrough:
        total_resistance = sum([
            src_resistance, input_cable_resistance, eut_resistance,
            output_cable_resistance, load_resistance])
        current = voltage / total_resistance
    else:
        current = 0

    src_drop = src_resistance * current
    input_cable_drop = input_cable_resistance * current
    eut_drop = eut_resistance * current
    output_cable_drop = output_cable_resistance * current
    vmin_sp = voltage * 0.98 - 0.01 - src_drop
    vmax_sp = voltage * 1.02 + 0.01 - src_drop
    vmin_ip = vmin_sp - input_cable_drop
    vmax_ip = vmax_sp - input_cable_drop
    vmin_op = (vmin_ip - eut_drop) if passthrough else vmin_off
    vmax_op = (vmax_ip - eut_drop) if passthrough else vmax_off
    vmin_ld = vmin_op - output_cable_drop
    vmax_ld = vmax_op - output_cable_drop

    imin_on = current * 0.98 - 0.01
    imax_on = current * 1.02 + 0.01

    supply_ports = {
        'CONTROL': 'AUX',
        'AUX': 'CONTROL',
        'TARGET-C': 'CONTROL',
    }

    supply_port = supply_ports[input_port]

    begin(f"Testing VBUS distribution from {info(input_port)} " +
          f"at {info(f'{voltage:.1f} V')} " +
          f"with passthrough {info('ON' if passthrough else 'OFF')}")

    if apollo:
        begin(f"Moving EUT supply to {info(supply_port)}")
        enable_supply_input(apollo, supply_port, True)
        connect_host_supply_to('CONTROL', 'AUX')
        connect_host_supply_to(supply_port)
        enable_supply_input(apollo, input_port, False)
        end()

    begin(f"Setting up test conditions")
    set_boost_supply(voltage, current + 0.3)
    if apollo:
        for port in ('CONTROL', 'AUX', 'TARGET-C'):
            set_passthrough(apollo, port,
                passthrough and port is input_port)
    connect_boost_supply_to(input_port)
    if passthrough:
        set_pin(load_pin, True)
    end()

    sleep(0.1)

    if apollo:
        begin("Checking voltage and current on supply port")
        test_vbus(supply_port, 4.3, 5.25)
        test_eut_voltage(apollo, supply_port, 4.3, 5.25)
        test_eut_current(apollo, supply_port, 0.13, 0.16)
        end()

        begin("Checking voltages and positive current on input")
        test_vbus(input_port, vmin_sp, vmax_sp)
        test_eut_voltage(apollo, input_port, vmin_ip, vmax_ip)
        test_eut_current(apollo, input_port, imin_on, imax_on)
        end()

        begin("Checking voltages and negative current on output")
        test_voltage('TARGET_A_VBUS', vmin_op, vmax_op)
        test_eut_voltage(apollo, 'TARGET-A', vmin_op, vmax_op)
        test_eut_current(apollo, 'TARGET-A', -imax_on, -imin_on)
        test_voltage('VBUS_TA', vmin_ld, vmax_ld)
        end()
    else:
        begin("Checking voltages")
        test_vbus(input_port, vmin_sp, vmax_sp)
        test_voltage('TARGET_A_VBUS', vmin_op, vmax_op)
        test_voltage('VBUS_TA', vmin_ld, vmax_ld)
        end()

    begin("Checking for leakage on other ports")
    for port in ('CONTROL', 'AUX', 'TARGET-C'):
        if port == input_port:
            continue
        if apollo and port == supply_port:
            continue
        test_vbus(port, vmin_off, vmax_off)
        if apollo:
            test_eut_voltage(apollo, port, vmin_off, vmax_off)
            test_eut_current(apollo, port, imin_off, imax_off)
    end()

    begin("Shutting down test")
    if passthrough:
        set_pin(load_pin, False)
        if apollo:
            set_passthrough(apollo, input_port, False)
    connect_boost_supply_to(None)
    end()

    end()

def test_user_button(apollo):
    button = f"{info('USER')} button"
    begin(f"Testing {button}")
    start(f"Checking {button} is released")
    write_register(apollo, REGISTER_BUTTON_USER, 0)
    if read_register(apollo, REGISTER_BUTTON_USER):
        raise ValueError(f"USER button press detected unexpectedly")
    done()
    request("press the USER button")
    start(f"Checking {button} was pressed")
    if not read_register(apollo, REGISTER_BUTTON_USER):
        raise ValueError(f"USER button press not detected")
    done()
    end()

def request_control_handoff_to_mcu(handle):
    start(f"Requesting FPGA handoff {info('CONTROL')} port to MCU")
    handle.controlWrite(
        usb1.TYPE_VENDOR | usb1.RECIPIENT_DEVICE, 0xF0, 0, 0, b'', 1)
    done()

def send_usb_reset():
    pass
