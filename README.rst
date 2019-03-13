Banksim 
============

.. image:: https://travis-ci.org/byeungchun/banksim.svg?branch=master
    :target: https://travis-ci.org/byeungchun/banksim

'Basksim' is the banking simulation model based on An Agent-Based Model using Python MESA library[1].

.. image:: https://github.com/byeungchun/mesaabba/blob/master/mesaabba.jpg

Description
---------------
Core banking simulation logics is based on the ABBA model[2]. In this model, there are four agents; Bank, Saver, Loan, Inter-bank Loan. Every savers can open their saving accounts in one bank and move the bank each steps. Bank can create loans as many as their reserve ratio is bigger than minimum ratio. In each steps, loans are evaluted and some loans are default and it affects the solvency of the bank. When a bank need more capital for solving liquidity issue, bank can borrow money through the inter-bank loans. Current work flow follows the ABBA model[2]

In each steps, all of agents variables are stored in SQLITE database for further analysis. It creates result.db file in the root directory.


Using Banksim
---------------

.. code-block:: bash

        $ pip install -r requirements.txt
        $ python run.py
        

References
---------------
        [1] `MESA`_: Agent-based modeling in Python 3+
        
        [2] `ABBA`_: Agent-Based Model of the Banking System


.. _`MESA` : https://github.com/projectmesa/mesa
.. _`ABBA` : https://github.com/jchanlauimf/ABBA
