"""
A signal (not unix os signal) is an abstraction that helps to establish a one-to-many connection between
objects and a oneway data transfer channel between them. Essentially, this is an implementation of classic
`Observer <https://refactoring.guru/design-patterns/observer>`_ design pattern.

There always some *Observable* object and a number of *Observers*. An Observable holds reference to all Observers that
have *subscribed* to it, and on some event will pass some arbitrary data to all its observers.

**Some key notes.**
*Observable* does not know anything about its observers and does not care which type of data they want or can to accept.
Mainly, *Observable* works like a Beacon - it emits **one** type of data to every listener.

Why signals?
-----------
As application works with asynchronous celery tasks, it doesn't have direct control on task data and particular time
when this data becomes available. Signals allow functions in application that depend on task results data to
accept and process that data accordingly.

Moreover, signals allow gathering some usefull inforamation (like function input, output etc.) during application
execution in comfortable manner. Just plugin some signals issuers in functions or methods and collect the data::

    from django.dispatch import Signal

    class MySignal(Signal):
        # you may implement some data processing logic here

    mysignal = MySignal()

    def observer_func(sender, *args, **kwargs):
        # some signal processing loogic here...

    mysignal.connect(observer_func)

    def observable_func(*args, **kwargs):
        # some logic here ...
        mysignal.send(sender='observable_func', **kwars)


How signals work?
----------------
Essentially, application signal implementation is based on
`Django Signals <https://docs.djangoproject.com/en/2.1/topics/signals/>`_ and complies to its interface.

To use signal you need to use an existing signal insance or implement your own.::

    from celery.signals import task_postrun

    def process_signal(sender, *args, **kwargs):
        # signal data processing here...

    task_postrun.connect(process_signal)

That is, basically all you need. Whenever celery task is end up running process_signal() func will be envoked with
arguments passed by signal initiator.

"""


from functools import wraps
from types import FunctionType
from django.dispatch import Signal


class ParamsInterceptorSignal(Signal):
    """
    This signal allows to intercept input parameters from a given function or method.
    It will have decorated function or method name string as a *sender*.
    ::

        from common.signals import params_interceptor

        @params_interceptor.intercept
        def func_a(*args, **kwargs):
            # do something here ...

        @params_interceptor.intercept
        def func_b(*args, **kwargs):
            # do something here ...

        def func_a_observer(sender, *args, **kwargs):
            # process signal here

        def func_b_observer(sender, *args, **kwargs):
            # process signal here


        # func_a_observer will recieve signals only from func_a
        params_interceptor.coonect(func_a_observer, sender=func_a.__name__)

        # func_b_observer will recieve signals only from func_b
        params_interceptor.coonect(func_b_observer, sender=func_b.__name__)

    """
    def intercept(self, func):
        """
        Decorate any function or method to intercept its input parameters and pass them to signal listeners

        :param func:    decorated function or method
        :type func:     FunctionType
        :return:        decorator wrapper
        :rtype:         FunctionType
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, *kwargs)
            # exclude 'object instance' argement on class methods interception
            args = args[1:] if hasattr(args[0], '__class__') else args
            self.send(func.__name__, args=args, kwargs=kwargs)
            return result
        return wrapper


params_interceptor = ParamsInterceptorSignal(providing_args=['args', 'kwargs'])


class Beacon:
    """
    Abstract base class of *Observable* object implementation.

    You may implement you own observables by inheriting Beacon class::

        # my_signals.py

         from common.signals import Beacon

         class MyBeacon(Beacon):
             def do_something(data):
                 self._data = data
                 self.notify()

    For patter to work you should also add some listeners to your beacon
    ::
        # my_signals.py

        from common.signals import Listener

        class MyListener(Listener):
            def update(beacon):
                beacon_data = beacon.get_data()
                print(beacon_data)

        beacon = MyBeacon()
        listener_1 = MyListener()
        listener_2 = MyListener()
        beacon.add_observers(listener_1, listener_2)

    As your beacon and listeners are initiated and connected you may use beacon instance in your code
    to create an *event-like* notifications for listeners::

        from my_signals import beacon

        # something going on herer...

        beacon.do_something('some data')
        # print -> 'some data'
        # print -> 'some data'

    Note, that every listener of particular beacon will get **the same data**.
    """

    def __init__(self):
        self._observers = []
        self._data = None

    def add_observers(self, *observers: 'Listener'):
        """
        Add listeners to Beacon. Every listener will get the same data when Beacon call it's
        :py:meth:`Beacon.notify`.

        :param observers:   collection of observers. This should be instances of :py:class:`Listener` class
        :type observers:    iter
        """
        self._observers.extend(observers)

    def get_data(self):
        """
        Main method that defines the data a beacon should emit to its listeners.

        This method is called by every beacon's listener to retrieve its data. It may be overriden in sublclasses
        to customize or preprocess returned data.

        :return:            Beacon's data to its listeners
        :rtype:             Any
        """
        return self._data

    def notify(self):
        """
        This method may be called every time beacon should pass its data to listeners::

            from my_signals import beacon

            beacon._data = 'hello world'
            beacon.notify()

            # print -> 'hello world'
            # print -> 'hello world'

        :return:            None
        """
        for obs in self._observers:
            obs.update(self)


class Listener:
    """
    A Beacon listener a.k.a *Observer*
    This is a data type that is able to subscribe to any beacon and receive its output data.

    """
    def update(self, beacon: Beacon) -> None:
        """
        Called everytime :py:meth:`Beacon.notify` method is called.
        Here we should implement some logic of processing beacon output data.
        """
        raise NotImplementedError


class Transceiver(Beacon):
    """
    A special type of beacon that can receive some data as input, process it if needed and emit to listeners.

    This class designed to wrap signal processing procedures. You can connect multiple :py:class:`Signal` instances
    to Transeiver and it will pass all signal's data to its listeners::

        # my_signals.py

        from common.signals import Transceiver, Signal, Listener

        class MyTransceiver(Transceiver):
            def process_signal(self, sender, *args, **kwargs):
                # process signal data here
                self._data = kwargs.get('data')
                self.notify()

        class MyListener(Listener):
            def update(self, beacon):
                print(beacon.get_data())


        trans = MyTransceiver()
        my_signal_1 = Signal(providing_args=['data'])
        my_signal_2 = Signal(providing_args=['data'])
        listener_1 = MyListener()
        listener_2 = MyListener()
        trans.add_signal(my_signal_1, my_signal_2)
        trans.add_observers(listener_1, listener_2)

    As you've created and connected some transceivers you may use signals to pass data from your code
    to all tranceiver's listeners::

        # my_controller.py

        from my_signals import my_signal_1, my_signal_2

        # something going on here ...
        my_signal_1.send(sender='some_sender', data='hello world')
        my_signal_2.send(sender='some_sender', data='hello world')

        # print -> 'hello world'
        # print -> 'hello world'
        # print -> 'hello world'
        # print -> 'hello world'


    You can also dispatch signals data::

        # my_signals.py

        class MyTargetedTransceiver(Transceiver):

            target_sender = 'my_sender'
            # This will limit signals senders only to this name.
            # You may also set a function or class name or object here

            def process_signal(self, sender, *args, **kwargs):
                # process signal data here
                self._data = f"{kwargs.get('data')} received from {self.target_sender}"
                self.notify()

        t_trans = MyTargetedTransceiver()
        t_trans.add_signals(my_signal_1, my_signal_2)
        t_trans.add_observers(listener_1, listener_2)

        # my_controller.py

        # something going on here ...
        my_signal_1.send(sender='some_sender', data='hello world')

        # print -> 'hello world'
        # print -> 'hello world'

        my_signal_2.send(sender='my_sender', data='hello world')

        # print -> 'hello world'
        # print -> 'hello world'
        # print -> 'hello world received from my_sender'
        # print -> 'hello world received from my_sender'

    """

    target_sender = None
    """
    From which sender transceiver will accept signals. 
    Should be a python object or None. If None, will receive signals from all senders.
    """

    def add_signals(self, *signals: Signal):
        """
        Connect beacon to one or multiple input signal sources.

        :param signals:         a collection of :py:class:`Signal` instances
        :type signals:
        :return:                None
        """
        for sig in signals:
            sig.connect(self.process_signal, sender=self.target_sender, dispatch_uid=id(self))

    def process_signal(self, sender, *args, **kwargs) -> None:
        """
        This is a main method that corresponds to :py:meth:`Signal.connect` signature.
        Here you may implement signal processing logic
        `More info <https://docs.djangoproject.com/en/2.1/topics/signals/#django.dispatch.Signal.connect>`_

        :param sender:              signal sender
        :type sender:               str or object
        """
        raise NotImplementedError
