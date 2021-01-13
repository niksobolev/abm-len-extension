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
        self.wage = random.randint(100, 1000)
        self.price = 10
        self.looking_for_worker = 0
        self.full_workplaces = 0
        self.demand = 10
        self.demand_min_coefficient = 0.25
        self.demand_max_coefficient = 1
        self.inventory = 0
        self.sigma = 0.019  # percent for increasing/decreasing wage
        self.gamma = 24  # after this number of month with fulled working places we can decrease wage
        self.phi_min = 1.025  # required for counting marginal costs
        self.phi_max = 1.15  # required for counting marginal costs
        self.tau = 0.75  # chance to increase a price
        self.upsilon = 0.02  # max range of distribution for increasing price
        self.lambda_coefficient = 3  # how many products produced by one household per day
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
        if self.looking_for_worker == 1:
            self.wage = self.wage * (1 + random.uniform(0, self.sigma))
        if self.full_workplaces > self.gamma:
            self.wage = self.wage * (1 - random.uniform(0, self.sigma))

    def hire_or_fire(self):
        if self.inventory < self.demand_min_coefficient * self.demand:
            self.looking_for_worker = 1
        if self.inventory > self.demand_max_coefficient * self.demand:
            del self.households[0]

    def change_goods_price(self):
        marginal_costs = self.wage/(30 * self.lambda_coefficient)
        if self.price < self.phi_min * marginal_costs:
            if random.random() < self.tau:
                self.price = self.price * (1 + random.uniform(0, self.upsilon))
        if self.price > self.phi_max * marginal_costs:
            if random.random() < self.tau:
                self.price = self.price * (1 - random.uniform(0, self.upsilon))

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
