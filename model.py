from mesa import Agent, Model
from mesa.time import RandomActivation
import random


class Householder(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.wealth = random.randint(1000, 10000)
        self.wage = 0
        self.consumption = 0
        self.companies = []
        self.company = None
        self.wage_decreasing_coefficient = 0.95
        self.critical_price_ratio = 0.99  # if price in new company less that this value, replace company by new one
        self.consumption_power = 0.9  # allows not to spend all money for consumption
        self.unemployed_attempts = 5  # how many times unemployed household tries to find a job
        self.search_job_chance = 0.1  # chance to search a job if wage is more than desired
        for _ in range(7):
            self.companies.append(random.choice(model.cmp_schedule.agents))

    def search_cheaper_prices(self):
        if random.random() < 0.25:
            random_known_pick = random.choice(self.companies)
            list_of_pretenders = []
            for firm in self.model.cmp_schedule.agents:
                if firm not in self.companies:
                    for i in range(len(firm.households)):
                        list_of_pretenders.append(firm)
            if list_of_pretenders:
                random_unknown_pick = random.choice(list_of_pretenders)
                if random_unknown_pick.price/random_known_pick.price < self.critical_price_ratio:
                    self.companies.remove(random_known_pick)
                    self.companies.append(random_unknown_pick)

    def search_productive_firms(self):
        pass

    def search_new_job(self):
        for i in range(self.unemployed_attempts):
            company = random.choice(self.model.cmp_schedule.agents)
            if company.looking_for_worker:
                if self.company is not None:
                    if company.wage > self.company.wage:
                        if self.company.wage >= self.wage:
                            if random.random() < self.search_job_chance:
                                self.company.households.remove(self)
                                self.company = company
                                self.company.households.append(self)
                                self.wage = self.company.wage
                        else:
                            self.company.households.remove(self)
                            self.company = company
                            self.company.households.append(self)
                            self.wage = self.company.wage
                    break
                else:
                    if company.wage >= self.wage:
                        self.company = company
                        self.company.households.append(self)
                        self.wage = self.company.wage
                        break
        else:
            self.wage *= 0.9

    def identify_consumption(self):
        average_price = sum(company.price for company in self.companies)/len(self.companies)
        self.consumption = int((self.wealth/(30 * average_price)) ** self.consumption_power)

    def buy_goods(self):
        for company in sorted(self.companies, key=lambda x: x.price):
            total_price = self.consumption * company.price
            if (company.inventory > self.consumption) and (total_price < self.wealth):
                self.wealth -= total_price
                company.wealth += total_price
                company.inventory -= self.consumption
                break

    def end_of_month(self):
        self.search_cheaper_prices()
        self.search_productive_firms()
        self.search_new_job()
        self.identify_consumption()

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
        self.looking_for_worker = False
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
        self.households = []
        self.product_price = random.randint(10, 100)

    def produce(self):
        pass

    def pay_wages(self):
        for h in self.households:
            h.wealth += self.wage
            self.wealth -= self.wage

    def fill_money_buffer(self):
        pass

    def give_shares(self):
        pass

    # If we didn't find worker last month then increase wage
    # If we didn't loose worker for last <full_workplaces> months then decrease wage
    def set_wage_rate(self):
        if self.looking_for_worker:
            self.wage = self.wage * (1 + random.uniform(0, self.sigma))
        if self.full_workplaces > self.gamma:
            self.wage = self.wage * (1 - random.uniform(0, self.sigma))

    # If we don't have enough inventory in buffer then hire a worker
    # If we have a lot of inventory in buffer then fire one
    def hire_or_fire(self):
        if self.inventory < self.demand_min_coefficient * self.demand:
            self.looking_for_worker = True
        else:
            self.looking_for_worker = False
        if self.inventory > self.demand_max_coefficient * self.demand:
            fired_h = self.households[0]
            fired_h.company = None
            del self.households[0]

    # Marginal cost is price that we spend on production of 1 unit of inventory.
    # We spend money for only wages. Thus, marginal cost is wage divided by number
    # of products produced per day * days in month. If we have small yield (less
    # than 2.5 percent) then we need to increase price. If we earn more than 15%
    # of marginal cost we should decrease price.
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
