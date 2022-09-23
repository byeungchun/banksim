"""
사례 6 - 단일 뱅크, 예금자, 대출, 부도대출, 뱅크런
"""

import mesa
import numpy as np

from mesa.visualization.UserParam import UserSettableParameter


class Saver(mesa.Agent):
    def __init__(self, unique_id, pos, model, money):
        super().__init__(unique_id, pos)
        self.money = money
        self.model = model

    def step(self):
        if self.model.saving_badloan_ratio > self.model.badloan_ratio_threshold:
            self.money -= self.money * self.model.bankrun_rate
        self.money += self.money * self.model.saving_interest_rate


class Loan(mesa.Agent):
    def __init__(self, unique_id, pos, model, loan, bankrupt_rate):
        super().__init__(unique_id, pos)
        self.mypos = pos
        self.loan = loan
        self.model = model
        self.bankrupt_rate = bankrupt_rate
        print("bankrupt_rate", bankrupt_rate)

    def step(self):
        if self.model.random.random() < self.bankrupt_rate:
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            bad_loan = LoanBad(self.model.next_id(), self.mypos, self.model, self.loan)
            self.model.grid.place_agent(bad_loan, self.mypos)
            self.model.schedule.add(bad_loan)


class LoanBad(mesa.Agent):
    def __init__(self, unique_id, pos, model, loan):
        super().__init__(unique_id, pos)
        self.loan = loan

    def step(self):
        pass
        # self.loan -= self.loan * 0.04


class Bank(mesa.Agent):
    def __init__(self, unique_id, pos, model):
        super().__init__(unique_id, pos)
        self.model = model
        self.asset = 0

    def step(self):
        total_saving = 0
        total_interest_expense = 0
        total_interest_revenue = 0
        for agent in self.model.schedule.agents:
            if type(agent) is Saver:
                total_saving += agent.money
                total_interest_expense += agent.money * self.model.saving_interest_rate
            if type(agent) is Loan:
                total_interest_revenue += agent.loan * self.model.loan_interest_rate
        self.asset = total_saving + total_interest_revenue - total_interest_expense


def compute_saver_money(model):
    return sum([agent.money for agent in model.schedule.agents if type(agent) is Saver])


def compute_bank_asset(model):
    total_saving = 0
    total_loan = 0
    total_loan_bad = 0
    for agent in model.schedule.agents:
        if type(agent) is Saver:
            total_saving += agent.money
        if type(agent) is Loan:
            total_loan += agent.loan
        if type(agent) is LoanBad:
            total_loan_bad = agent.loan

    model.saving_badloan_ratio = total_loan_bad / (total_loan_bad + total_loan)
    return total_saving + total_loan - total_loan_bad


def compute_loan_total(model):
    return sum([agent.loan for agent in model.schedule.agents if type(agent) is Loan])


class ModelBankingSystem(mesa.Model):
    def __init__(
        self,
        height,
        width,
        initial_bank,
        initial_savers,
        initial_loans,
        num_step,
        initial_saving_money,
        initial_loan_amount,
        saving_interest_rate,
        loan_interest_rate,
        bankrupt_rate,
        badloan_ratio_threshold,
        bankrun_rate,
    ):
        super().__init__()
        self.width = width
        self.height = height
        self.initial_bank = initial_bank
        self.initial_savers = initial_savers
        self.initial_loans = initial_loans
        self.num_steps = num_step
        self.saving_interest_rate = saving_interest_rate / 100.0
        self.loan_interest_rate = loan_interest_rate / 100.0
        self.bankrupt_rate = bankrupt_rate / 100.0
        self.saving_badloan_ratio = 0
        self.badloan_ratio_threshold = badloan_ratio_threshold / 100.0
        self.bankrun_rate = bankrun_rate / 100.0

        self.grid = mesa.space.MultiGrid(self.width, self.height, True)
        self.schedule = mesa.time.RandomActivation(self)
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "BankAsset": compute_bank_asset,
                "SaverMoney": compute_saver_money,
                "LoanTotal": compute_loan_total,
            }
        )
        self.lst_pos = []

        x = int(self.width / 2)
        y = int(self.height / 2)
        bank = Bank(self.next_id(), (x, y), self)
        self.grid.place_agent(bank, (x, y))
        self.schedule.add(bank)
        self.lst_pos.append((x, y))

        for i in range(initial_savers):
            pos = self._find_empty_pos()
            saver = Saver(self.next_id(), pos, self, initial_saving_money)
            self.grid.place_agent(saver, pos)
            self.schedule.add(saver)

        for i in range(initial_loans):
            pos = self._find_empty_pos()
            loan = Loan(
                self.next_id(), pos, self, initial_loan_amount, self.bankrupt_rate
            )
            self.grid.place_agent(loan, pos)
            self.schedule.add(loan)

        self.running = True
        self.datacollector.collect(self)

    def _find_empty_pos(self):
        for _ in range(self.width * self.height):
            pos = (
                self.random.randrange(self.width),
                self.random.randrange(self.height),
            )
            if pos not in self.lst_pos:
                self.lst_pos.append(pos)
                return pos
        print("There is no empty cell. Check width/height size")

        return False

    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)

        if self.schedule.steps == self.num_steps:
            self.running = False

    def run_model(self, n):
        for i in range(n):
            self.step()


def agent_portrayal(agent):

    if type(agent) is Bank:
        portrayal = {
            "Shape": "files/logo_bankofkorea.png",
            "scale": 1,
            "Layer": 1,
            "Budget": agent.asset,
            "text_color": "red",
        }

    if type(agent) is Saver:
        portrayal = {
            "Shape": "files/saver.png",
            "scale": 0.5,
            "Layer": 1,
            "Budget": agent.money,
            "text_color": "red",
        }

    if type(agent) is Loan:
        portrayal = {
            "Shape": "files/loan.png",
            "scale": 0.5,
            "Layer": 1,
            "Budget": agent.loan,
            "text_color": "red",
        }

    if type(agent) is LoanBad:
        portrayal = {
            "Shape": "files/loan_bad.png",
            "scale": 0.5,
            "Layer": 1,
            "Budget": agent.loan,
            "text_color": "red",
        }

    return portrayal


height = 10
width = 10

initial_bank = 1

model_params = {
    "width": width,
    "height": height,
    "initial_bank": initial_bank,
    "num_step": UserSettableParameter("number", "스텝수", value=10),
    "initial_savers": UserSettableParameter("number", "예금자 수", value=30),
    "initial_loans": UserSettableParameter("number", "대출 수", value=30),
    "initial_saving_money": UserSettableParameter("number", "초기 예금액", value=10),
    "initial_loan_amount": UserSettableParameter("number", "초기 대출액", value=10),
    "saving_interest_rate": UserSettableParameter("number", "저축 이자율(%)", value=3.5),
    "loan_interest_rate": UserSettableParameter("number", "대출 이자율(%)", value=4.5),
    "bankrupt_rate": UserSettableParameter("number", "부도율(%)", value=10.5),
    "badloan_ratio_threshold": UserSettableParameter(
        "number", "대출 부도비율에 따른 뱅크런 문턱값(%)", value=30
    ),
    "bankrun_rate": UserSettableParameter("number", "대출 부도에 따른 인출비율(%)", value=20),
}

grid = mesa.visualization.CanvasGrid(agent_portrayal, width, height, 400, 400)
chart = mesa.visualization.ChartModule(
    [
        {"Label": "BankAsset", "Color": "#0000FF"},
        {"Label": "SaverMoney", "Color": "#FF0000"},
        {"Label": "LoanTotal", "Color": "#00FF00"},
    ]
)

server = mesa.visualization.ModularServer(
    ModelBankingSystem,
    [grid, chart],
    "사례 6 - 단일 뱅크, 예금자, 대출, 부도대출, 뱅크런 ",
    model_params,
)
server.port = 8521  # The default
server.launch()
