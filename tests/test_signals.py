from common import signals

# TODO:: rewrite

_data = []
_signal = signals.Signal(providing_args=['data'])
_signal_1 = signals.Signal(providing_args=['data'])


class TestListener(signals.Listener):
    def update(self, beacon: signals.Beacon):
        _data.append(beacon.get_data() or 1)


class TestListener1(signals.Listener):
    def update(self, beacon: signals.Beacon):
        _data.append(beacon.get_data() or 2)


class TestTrans(signals.Transceiver):
    def process_signal(self, sender, *args, **kwargs):
        self._data = {sender: kwargs.get('data')}


class TestTrans1(signals.Transceiver):
    def process_signal(self, sender, *args, **kwargs):
        self._data = {sender: kwargs.get('data')}



def test_beacon_listener_communicate():
    beacon = signals.Beacon()
    lis1, lis2 = TestListener(), TestListener1()
    beacon.add_observers(lis1, lis2)
    assert len(beacon._observers) == 2
    beacon.notify()
    assert all([1 in _data, 2 in _data])


def test_sig_transceiver():
    # create transciever
    transc = TestTrans()
    # create listeners
    lis1, lis2 = TestListener(), TestListener1()
    # bind signal to transceiver
    transc.add_signals(_signal)
    # bind listeners
    transc.add_observers(lis1, lis2)
    data = {'hello': 1}
    # send signal with data
    _signal.send('test_sender', data=data)
    transc.notify()
    assert {'test_sender': data} in _data






