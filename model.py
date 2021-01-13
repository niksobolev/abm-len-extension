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

    def check_companies(self):
        pass

    def buy_goods(self):
        pass

    def apply(self):
        pass

    def step(self):
        print("Hi, I am agent {0} with wealth equal to {1}.".format(self.unique_id, self.wealth))
        print('I know about {0}'.format(self.companies))
        self.wealth += random.randint(-100, 100)


class Company(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.wealth = random.randint(1000, 10000)
        self.households = {}
        self.product_price = random.randint(10, 100)

    def produce(self):
        pass

    def pay_salary(self):
        pass

    def step(self):
        print("Hi, I am agent {0} with wealth equal to {1}.".format(self.unique_id, self.wealth))
        self.wealth += random.randint(-100, 100)


class LenExtended(Model):
    def __init__(self, num_hh, num_cmp):
        self.num_hh = num_hh
        self.num_cmp = num_cmp
        self.hh_schedule = RandomActivation(self)
        self.cmp_schedule = RandomActivation(self)

        for i in range(self.num_cmp):
            c = Company(i, self)
            self.cmp_schedule.add(c)

        for i in range(self.num_hh):
            h = Householder(i, self)
            self.hh_schedule.add(h)

    def step(self):
        self.hh_schedule.step()


empty_model = LenExtended(10, 10)
empty_model.step()
empty_model.step()
