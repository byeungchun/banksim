from datetime import datetime,timezone

def insert_simulation_table(cursor, task):
    """
    Insert a row into Simulation table
    :param conn:
    :param task:
    :return:
    """

    sql = '''INSERT INTO Simulation(simid,title,simdate) VALUES(?,?,?)'''
    cursor.execute(sql, task)
    return cursor.lastrowid


def insert_agtbank_table(cursor, simid, numstep, banks):
    """

    :param cursor:
    :param banks:
    :return:
    """

    sql = '''INSERT INTO AgtBank(AgtBankId,SimId,StepCnt,BankId,BankEquity,BankDeposit,BankLoan,BankReserve,BankAsset,
    BankProvision,BankNProvision,BankDepositRate,BankIbCredit,BankIbDebit,BankNetInterestIncome,BankInterestIncome,
    BankInterestExpense,BankIbInterestIncome,BankIbInterestExpense,BankIbNetInterestIncome,BankIbCreditLoss,
    BankRiskWgtAsset,BankDividend,BankCumDividend,BankDepositOutflow,BankDepositInflow,BankNetDepositflow,
    BankDefaultedLoan,BankSolvent,BankCapitalized,BankCreditFailure,BankLiquidityFailure,BankStepDate) VALUES(
    ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''
    col_date = datetime.now(timezone.utc)

    for bank in banks:
        bank_vars = bank.get_all_variables()
        bank_vars[0] = int(str(10000+numstep)+str(10000+bank_vars[3])) # AgtBankId
        bank_vars[1] = simid
        bank_vars[2] = numstep
        bank_vars[32] = col_date
        cursor.execute(sql, tuple(bank_vars))

    return cursor.lastrowid


def insert_agtsaver_table(cursor, simid, numstep, savers):
    """

    :param cursor:
    :param simid:
    :param numstep:
    :param savers:
    :return:
    """
    sql = '''INSERT INTO AgtSaver(AgtSaverId,SimId,StepCnt,SaverId,SaverBalance,SaverWithdrawProb,SaverExitProb,SaverBankId,
    SaverRegionId,SaverOwnAccount,SaverSolvent,SaverExit,SaverCurrent,SaverStepDate) Values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''

    col_date = datetime.now(timezone.utc)
    for saver in savers:
        saver_vars = saver.get_all_variables()
        saver_vars[0] = int(str(10000+numstep)+str(10000+saver_vars[3])) # AgtSaverId
        saver_vars[1] = simid
        saver_vars[2] = numstep
        saver_vars[13] = col_date
        cursor.execute(sql,tuple(saver_vars))

    return cursor.lastrowid
