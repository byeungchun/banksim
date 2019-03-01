Banksim 
============

'Basksim' is the banking simulation model based on An Agent-Based Model using Python MESA library.

![alt text](https://github.com/byeungchun/mesaabba/blob/master/mesaabba.jpg)

Description
---------------
Core banking simulation logics is based on the ABBA model[1]. In this model, there are four agents; Bank, Saver, Loan, Inter-bank Loan. Every savers can open their saving accounts in one bank and move the bank each steps. Bank can create loans as many as their reserve ratio is bigger than minimum ratio. In each steps, loans are evaluted and some loans are default and it affects the solvency of the bank. When a bank need more capital for solving liquidity issue, bank can borrow money through the inter-bank loans. Current work flow follows the ABBA model[1]


Using Banksim
---------------

.. code-block:: bash

