/****************************************************************
	BankSim Database 
	Script: banksim_Sqlite.sql
	Desciption: Creates the Banksim database
	DB Server: Sqlite
	Author: Byeungchun Kwon
*****************************************************************/

/****************************************************************
	Drop Foreign Keys Constraints
*****************************************************************/


/****************************************************************
	Drop Tables
*****************************************************************/
DROP TABLE IF EXISTS [Simulation];

DROP TABLE IF EXISTS [AgtBank];

DROP TABLE IF EXISTS [AgtSaver];

DROP TABLE IF EXISTS [AgtLoan];

DROP TABLE IF EXISTS [AgtIbLoan];


/****************************************************************
	Create Tables
*****************************************************************/
CREATE TABLE [Simulation]
(
	[SimId] INTEGER NOT NULL,
	[Title] NVARCHAR(200) NOT NULL,
	[SimDate] DATETIME NOT NULL,
	CONSTRAINT [PK_Simulation] PRIMARY KEY ([SimId])
);

CREATE TABLE [AgtBank]
(
	[AgtBankId] INTEGER NOT NULL,
	[SimId] INTEGER NOT NULL,	
	[StepCnt] INTEGER NOT NULL, 
	[BankId] INTEGER NOT NULL,
	[BankEquity] REAL NOT NULL, 	-- equity = None  # equity (capital) of the bank
	[BankDeposit] REAL NOT NULL, 	-- bank_deposits = None  # deposits raised by bank
	[BankLoan] REAL NOT NULL, 		-- bank_loans = None  # amount total loans made by bank
	[BankReserve] REAL NOT NULL,	-- bank_reserves = None  # liquid bank_reserves
	[BankAsset] REAL NOT NULL,		-- total_assets = None  # bank_loans + bank_reserves
	[BankProvision] REAL,			-- bank_provisions = None  # provisions against expected losses
	[BankNProvision] REAL, 			-- bank_new_provisions = None  # required provisions, not met if bank defaults
	[BankDepositRate] REAL,			-- rdeposits = None  # deposit rate
	[BankIbCredit] REAL,			-- ib_credits = None  # interbank loans to other banks
	[BankIbDebit] REAL,				-- ib_debits = None  # interbank loans from other banks
	[BankNetInterestIncome] REAL,	-- net_interest_income = None  # net interest income, balance sheet
	[BankInterestIncome] REAL, 		-- interest_income = None  # interest income, loans
	[BankInterestExpense] REAL,		-- interest_expense = None  # interest expense, depositors
	[BankIbInterestIncome] REAL,	-- ib_interest_income = 0  # interest income, interbank
	[BankIbInterestExpense] REAL,	-- ib_interest_expense = 0  # interest expense, interbank
	[BankIbNetInterestIncome] REAL,	-- ib_net_interest_income = 0  # net interest, interbank
	[BankIbCreditLoss] REAL,		-- ib_credit_loss = None  # credit losses, interbank exposures
	[BankRiskWgtAsset] REAL,		-- rwassets = None  # risk_weighted assets
	[BankDividend] REAL,			-- bank_dividend = None  # dividends
	[BankCumDividend] REAL,			-- bank_cum_dividend = None  # cumulative dividends
	[BankDepositOutflow] REAL,		-- deposit_outflow = 0  # deposit withdrawal shock
	[BankDepositInflow] REAL,		-- deposit_inflow = 0  # deposit inflow from other banks
	[BankNetDepositflow] REAL,		-- net_deposit_flow = None  # net deposit flow
	[BankDefaultedLoan] REAL,		-- defaulted_loans = None  # amount of defaulted loans
	[BankSolvent] INTEGER NOT NULL,			-- 1: TRUE, 0: False, bank_solvent = None  # bank solvent
	[BankCapitalized] INTEGER NOT NULL,		-- 1: TRUE, 0: False, bank_capitalized = None  # bank capitalized
	[BankCreditFailure] INTEGER NOT NULL,	-- 1: TRUE, 0: False, credit_failure = None  # credit failure
	[BankLiquidityFailure] INTEGER NOT NULL,-- 1: TRUE, 0: False, liquidity_failure = None  # liquidity failure
	[BankStepDate] DATETIME NOT NULL,
	CONSTRAINT [PK_AgtBank] PRIMARY KEY ([AgtBankId],[SimId]),
	FOREIGN KEY ([SimId]) REFERENCES [Simulation] ([SimId])
				ON DELETE NO ACTION ON UPDATE NO ACTION
);

CREATE TABLE [AgtSaver]
(
	[AgtSaverId] INTEGER NOT NULL,
	[SimId] INTEGER NOT NULL,
	[StepCnt] INTEGER NOT NULL,
	[SaverId] INTEGER NOT NULL,
	[SaverBalance] REAL, 				-- balance = None  # deposit balance with bank
	[SaverWithdrawProb] REAL, 			-- withdraw_prob = None  # probability of withdrawing deposit and shift to other bank 
	[SaverExitProb] REAL, 				-- exit_prob = None  # probability that saver withdraws and exits banking system
	[SaverBankId] INTEGER,				-- bank_id = None  # identity of saver's bank
	[SaverRegionId] INTEGER,			-- region_id = None  # region of saver
	[SaverOwnAccount] INTEGER NOT NULL,	-- 1: TRUE, 0: False, owns_account = None # owns account with bank-id
	[SaverSolvent] INTEGER,				-- 1: TRUE, 0: False, saver_solvent = None # solvent if bank returns principal, may become insolvent if bank is bankrupt
	[SaverExit] INTEGER,				-- 1: TRUE, 0: False, saver_exit = None  # saver exits the banking system?
	[SaverCurrent] INTEGER,				-- 1: TRUE, 0: False, saver_current = None  # old saver/ if false, it is a new entrant to the system
	[SaverStepDate] DATETIME NOT NULL,
	CONSTRAINT [PK_AgtSaver] PRIMARY KEY ([AgtSaverId],[SimId]),
	FOREIGN KEY ([SimId]) REFERENCES [Simulation] ([SimId])
				ON DELETE NO ACTION ON UPDATE NO ACTION 
);

CREATE TABLE [AgtLoan]
(
	[AgtLoanId] INTEGER NOT NULL,
	[SimId] INTEGER NOT NULL,
	[StepCnt] INTEGER NOT NULL,
	[LoanId] INTEGER NOT NULL,
	[LoanProbDefault] REAL NOT NULL,-- pdef = None  # true probability of default
	[LoanAmount] REAL NOT NULL, 	-- amount = None  # amount of loan - set to unity
	[LoanRiskWgt] REAL NOT NULL, 	-- rweight = None  # true risk-weight of the loan
	[LoanRiskWgtAmt] REAL, 			-- rwamount = None  # amount * rweight
	[LoanLgdAmt] REAL, 				-- lgdamount = None  # loss given default (1-rcvry-rate) * amount
	[LoanRecovery] REAL, 			-- loan_recovery = None  # rcvry-rate * amount
	[LoanRcvryRate] REAL, 			-- rcvry_rate = None  # recovery rate in case of default
	[LoanFireSaleLoss] REAL, 		-- fire_sale_loss = None  # loss percent if sold or removed from bank book
	[LoanRating] REAL,				-- rating = None  # loan rating - we can specify the rating and then assign pdef from a table - not used
	[LoanRateQuote] REAL, 			-- rate_quote = None  # rate quoted by lending bank
	[LoanRateReservation] REAL,		-- rate_reservation = None  # maximum rate borrower is willing to pay [not used here]
	[LoanPlusRate] REAL,			-- loan_plus_rate = None  # amount * (1 + rate-quote)
	[LoanInterestPymt] REAL,		-- interest_payment = None  # amount * rate-quote
	[LoanRegionId] INTEGER,			-- region_id = None  # Identity of loan's neighborhood - useful for analyzing cross-country/ regional lending patterns
	[LoanApproved] INTEGER,			-- 1: TRUE, 0: False, loan_approved = None  # is loan loan-approved?
	[LoanSolvent] INTEGER,			-- 1: TRUE, 0: False, loan_solvent = None  # is loan solvent?
	[LoanDumped] INTEGER,			-- 1: TRUE, 0: False, loan_dumped = None  # loan dumped during risk-weighted-optimization
	[LoanLiquidated] INTEGER,		-- 1: TRUE, 0: False, loan_liquidated = None  # loan liquidated owing to bank-bankruptcy
	[LoanBankId] INTEGER,			-- 1: TRUE, 0: False, bank_id = None  # identity of lending bank
	[LoanStepDate] DATETIME NOT NULL,
	CONSTRAINT [PK_AgtLoan] PRIMARY KEY ([AgtLoanId],[SimId]),
	FOREIGN KEY ([SimId]) REFERENCES [Simulation] ([SimId])
				ON DELETE NO ACTION ON UPDATE NO ACTION 
);

CREATE TABLE [AgtIbLoan]
(
	[AgtIbLoanId] INTEGER NOT NULL,
	[SimId] INTEGER NOT NULL,
	[StepCnt] INTEGER NOT NULL,
	[IbLoanId] INTEGER NOT NULL,
	[IbLoanRate] REAL NOT NULL, 	-- ib_rate = None  # interbank loan rate
	[IbLoanAmount] REAL NOT NULL, 	-- ib_amount = None  # intferbank amount
	[IbLoanCreditor] INTEGER NOT NULL, -- ib_creditor unique id
	[IbLoanDebtor] INTEGER NOT NULL, 	-- ib_debtor unique id
	[IbLoanStepDate] DATETIME NOT NULL,
	CONSTRAINT [PK_AgtIbLoan] PRIMARY KEY ([AgtIbLoanId],[SimId]),
	FOREIGN KEY ([SimId]) REFERENCES [Simulation] ([SimId])
				ON DELETE NO ACTION ON UPDATE NO ACTION 
);
