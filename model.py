from mesa import Agent, Model
from mesa.time import RandomActivation
import random


class Householder(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.wealth = random.randint(100, 1000)
        self.wage = 0
        self.companies = []
        for company in range(7):
            self.companies.append(self.random.choice(self.model.cmp_schedule.agents).unique_id)

    def search_cheaper_prices(self):
        pass

    def search_productive_firms(self):
        pass

    def search_new_job(self):
        pass

    def identify_consumption(self):
        pass

    def buy_goods(self):
        pass

    def apply(self):
        pass

    def end_of_month(self):
        self.search_cheaper_prices()
        self.search_productive_firms()
        self.search_new_job()
        self.identify_consumption()
        pass

    def step(self):
        if self.model.current_day // 30 == 0:
            self.end_of_month()
        self.buy_goods()


class Company(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.wealth = random.randint(1000, 10000)
        self.households = {}
        self.product_price = random.randint(10, 100)

    def produce(self):
        pass

    def pay_wages(self):
        pass

    def fill_money_buffer(self):
        pass

    def give_shares(self):
        pass

    def set_wage_rate(self):
        pass

    def hire_or_fire(self):
        pass

    def change_goods_price(self):
        pass

    def end_of_month(self):
        self.pay_wages()
        self.fill_money_buffer()
        self.give_shares()
        self.set_wage_rate()
        self.hire_or_fire()
        self.change_goods_price()
        pass

    def step(self):
        self.produce()
        if self.model.current_day // 30 == 0:
            self.end_of_month()


class LenExtended(Model):
    def __init__(self, num_hh, num_cmp):
        self.num_hh = num_hh
        self.num_cmp = num_cmp
        self.current_day = 0
        self.hh_schedule = RandomActivation(self)
        self.cmp_schedule = RandomActivation(self)

        for i in range(self.num_cmp):
            c = Company(i, self)
            self.cmp_schedule.add(c)

        for i in range(self.num_hh):
            h = Householder(i, self)
            self.hh_schedule.add(h)

    def step(self):
        self.cmp_schedule.step()
        self.hh_schedule.step()
        self.current_day += 1


empty_model = LenExtended(10, 10)
empty_model.step()
empty_model.step()
