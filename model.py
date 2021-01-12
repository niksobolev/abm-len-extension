from mesa import Agent, Model
from mesa.time import RandomActivation
import random


class Householder(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.wealth = random.randint(100, 1000)
        self.wage = 0
        self.companies = {}

    def check_companies(self):
        pass

    def buy_goods(self):
        pass

    def apply(self):
        pass

    def step(self):
        print("Hi, I am agent {0} with wealth equal to {1}.".format(self.unique_id, self.wealth))
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
    def __init__(self, n):
        self.num_agents = n
        self.schedule = RandomActivation(self)

        for i in range(self.num_agents):
            h = Householder(i, self)
            c = Company(i, self)
            self.schedule.add(h)
            self.schedule.add(c)

    def step(self):
        self.schedule.step()


empty_model = LenExtended(10)
empty_model.step()
empty_model.step()
