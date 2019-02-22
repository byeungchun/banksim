import logging
import random

from banksim.agent.bank import Bank
from banksim.agent.saver import Saver
from banksim.agent.ibloan import Ibloan
from banksim.bankingsystem.f2_eval_solvency import process_unwind_loans_insolvent_bank


def process_deposit_withdrawal(schedule):
    # savers withdraw funds from solvent banks
    # banks that are insolvent have already liquidated their loan portfolio and
    # returned their deposits to savers
    for solvent_bank in [x for x in schedule.agents if isinstance(x, Bank) and x.bank_solvent]:
        savers = [x for x in schedule.agents if isinstance(x, Saver) and x.pos == solvent_bank.pos and
                  x.saver_solvent and x.owns_account]
        logging.debug('process_deposit_withdrawal- num savers: %d of bank %d',len(savers),solvent_bank.pos)
        for saver in savers:
            if random.random() < saver.withdraw_prob:
                saver.bank_id = 9999
                saver.owns_account = False
                # TO DO: saver.saver_last_color = color
                # TO DO: change color Red
                solvent_bank.deposit_outflow = solvent_bank.deposit_outflow + saver.balance
            #solvent_bank.deposit_outflow = sum([x.balance for x in self.schedule.agents if isinstance(x, Saver) and
            #                                    x.pos == solvent_bank.pos and x.bank_id == 9999])


def process_deposit_reassignment(schedule):
    cap_bankpos = [x.pos for x in schedule.agents if
                   isinstance(x, Bank) and x.bank_solvent and x.bank_capitalized]
    if len(cap_bankpos) == 0:
        cap_bankpos = [x.pos for x in schedule.agents if isinstance(x, Bank) and x.bank_solvent]

    savers = [x for x in schedule.agents if isinstance(x, Saver) and x.bank_id == 9999]
    for saver in savers:
        bankpos = random.choice(cap_bankpos)
        saver.bank_id = bankpos
        saver.pos = bankpos
        saver.owns_account = True
        # TO DO: saver.saver_last_color = color

    for solvent_bank in [x for x in schedule.agents if isinstance(x, Bank) and x.bank_solvent]:
        solvent_bank.deposit_inflow = sum(
            [x.balance for x in savers if x.pos == solvent_bank.pos and x.owns_account])
        solvent_bank.net_deposit_flow = solvent_bank.deposit_inflow - solvent_bank.deposit_outflow


def process_deposit_flow_rebalancing(schedule):
    for solvent_bank in [x for x in schedule.agents if isinstance(x, Bank) and x.bank_solvent]:
        solvent_bank.calculate_bank_deposits()
        solvent_bank.calculate_reserve()
        solvent_bank.calculate_reserve_ratio()
        solvent_bank.calculate_total_assets()
        solvent_bank.deposit_inflow = 0
        solvent_bank.deposit_outflow = 0
        solvent_bank.net_deposit_flow = 0


def process_access_interbank_market(schedule, car, min_reserves_ratio, bank):
    liq_banks = [x for x in schedule.agents if isinstance(x, Bank) and x.capital_ratio >= car and
                 x.reserves_ratio > x.buffer_reserves_ratio * min_reserves_ratio]
    # for liq_bank in liq_banks:
        # print('Remove this print after implementing below to do')
        # TO DO: change colour to Green
    needed_reserves = min_reserves_ratio * bank.bank_deposits - bank.bank_reserves
    # TO DO: change colour to Yellow
    available_reserves = sum([x.bank_reserves - x.buffer_reserves_ratio * min_reserves_ratio * x.bank_deposits
                              for x in liq_banks])

    ib_request = needed_reserves if needed_reserves < available_reserves else available_reserves
    for liq_bank in liq_banks:
        excess_reserve = liq_bank.bank_reserves - liq_bank.buffer_reserves_ratio * min_reserves_ratio * \
                         liq_bank.bank_deposits
        liquidity_contribution = excess_reserve * ib_request / available_reserves if available_reserves != 0 else 0
        liq_bank.bank_reserves = liq_bank.bank_reserves - liquidity_contribution
        liq_bank.ib_credits = liq_bank.ib_credits + liquidity_contribution
        liq_bank.calculate_reserve_ratio()

        ibloan = Ibloan(schedule.model.next_id(), schedule.model, schedule.model.libor_rate)
        ibloan.ib_creditor = liq_bank
        ibloan.ib_amount = liquidity_contribution
        ibloan.ib_debtor = bank
        schedule.add(ibloan)
        schedule.model.G.add_edge(ibloan.ib_creditor.pos, ibloan.ib_debtor.pos)
        # TO DO: change color Red
        # TO DO: set line to thickness 3

    bank.ib_debits = ib_request
    bank.bank_reserves = bank.bank_reserves + bank.ib_debits
    bank.calculate_reserve_ratio()
    bank.calculate_total_assets()

    # TO DO: set assets=liabilities? (equity + bank-deposits + IB-debits) - (bank-loans + bank-reserves + IB-credits)


def process_evaluate_liquidity_needs(schedule, car, min_reserves_ratio, bankrupt_liquidation):
    for solvent_bank in [x for x in schedule.agents if isinstance(x, Bank) and x.bank_solvent]:
        solvent_bank.calculate_reserve_ratio()
    liq_cap_banks = [x for x in schedule.agents if isinstance(x, Bank) and x.capital_ratio > car and
                     x.reserves_ratio > min_reserves_ratio]
    for bankrun_bank in [x for x in schedule.agents if isinstance(x, Bank) and x.reserves_ratio < 0]:
        process_unwind_loans_insolvent_bank(schedule, bankrupt_liquidation, bankrun_bank)
        # TO DO: change color Brown
        bankrun_bank.liquidity_failure = True

    for noliqcap_bank in [x for x in schedule.agents if isinstance(x, Bank) and
                                                        x.reserves_ratio < min_reserves_ratio and x.capital_ratio >= car]:
        # TO DO: change color Yellow
        process_access_interbank_market(schedule, car, min_reserves_ratio, noliqcap_bank)

    # Recalculate the number of banks experiencing shortages of reserves
    # it could be the case that some banks attempting to find resources were not
    # able to find all the resources they needed

    #for noliqcap_bank in [x for x in self.schedule.agents if isinstance(x, Bank) and x.bank_solvent and
    #                                                         0 < x.reserves_ratio < self.min_reserves_ratio and not x.bank_capitalized]:
        #print('Remove this print after implementing below to do')
        # TO DO: change colour to Yellow


def main_evaluate_liquidity(schedule, car, min_reserves_ratio, bankrupt_liquidation):

    # the four procedures will cause some banks to have:
    #
    # excess reserves: bank-reserves > minimum-reserves
    # excess reserve deficit, reserves > 0
    #   borrow from banks with excess reserve surplus (if solvent and capitalized)
    #   reserve optimization if not capitalized
    # excess reserve deficit, reserves < 0
    #   bank facing liquidity run - cannot borrow from other banks
    #   reserve optimization - sell loans to build up reserves
    #
    #
    #
    # the deposit-<> procedures simulate the following shocks:
    #
    #   process-deposit-withdrawal: a number of savers close their accounts
    #   process-deposit-reassignment: and open accounts with other banks
    #     both process-deposit-withdrawal and -reassignment are liquidity-neutral
    #     system-wide
    #   process-deposit-flow-rebalancing: all bank-deposits and bank-reserves are
    #     adjusted to reflect the movement in reserves

    process_deposit_withdrawal(schedule)
    logging.debug('process_deposit_withdrawal')
    process_deposit_reassignment(schedule)
    process_deposit_flow_rebalancing(schedule)
    process_evaluate_liquidity_needs(schedule, car, min_reserves_ratio, bankrupt_liquidation)