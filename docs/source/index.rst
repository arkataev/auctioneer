.. auctioneer documentation master file, created by
   sphinx-quickstart on Fri Nov 23 16:25:55 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Auctioneer's Developer documentation!
================================================

How it works?
-------------
Auctioneer is intended to automate keyword bids management in Yandex Direct.
The main principle is rather simple: app will request from yandex direct api
keyword bids data, than recalculate bid in every keyword, using user-defined rules,
and, eventually, will send another request to yandex direct api that will set new
bids on keywords provided in request.

Some periodic tasks that will run procedure, described earlier,
on a given schedule may also be defined.


.. toctree::
   :glob:
   :titlesonly:
   :caption: Contents:

   gateways/index
   controllers/index
   entities
   models
   formulas
   signals


Indices and tables
==================

* :ref:`modindex`
* :ref:`search`
