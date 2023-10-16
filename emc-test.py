from cynthion.gateware.analyzer.top import USBAnalyzerApplet
from luna.gateware.applets.speed_test import USBInSpeedTestDevice
from amaranth import Elaboratable, Module
from luna import top_level_cli

class EMCTestDevice(Elaboratable):

    def elaborate(self, platform):
        m = Module()
        control_phy = platform.request('control_phy')
        aux_phy = platform.request('aux_phy')
        m.submodules += platform.clock_domain_generator()
        m.submodules += USBAnalyzerApplet(generate_clocks=False)
        m.submodules += USBInSpeedTestDevice(generate_clocks=False,
                                             phy=control_phy,
                                             pid=0x0f3b)
        m.submodules += USBInSpeedTestDevice(generate_clocks=False,
                                             phy=aux_phy,
                                             pid=0x0f3c)
        return m

top_level_cli(EMCTestDevice)
