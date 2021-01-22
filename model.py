from mesa import Agent, Model
from mesa.time import RandomActivation
import random
from utils import *


class Householder(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.wealth = random.randint(20000, 45000)  # initial sum of money of an agent
        self.wage = 0  # reservation wage (expected wage)
        self.consumption = 0  # how much goods does householder consume per day
        self.companies = []  # list of firms where householder can buy goods (type A connection)
        self.company = None  # firm that householder works for
        self.wage_decreasing_coefficient = 0.9  # if household was unemployed his reservation wage decreases by 10%
        self.critical_price_ratio = 0.99  # if price in new company less that this value, replace company by new one
        # in paper self.critical_price_ratio is reffed as xi = 0.01, but here it is (1-xi)
        self.consumption_power = 0.9  # allows not to spend all money for consumption (alpha)
        self.unemployed_attempts = 5  # how many times unemployed household tries to find a job (beta)
        self.search_job_chance = 0.1  # chance to search a job if wage is more than desired (pi)
        self.prob_search_price = 0.25  # chance to search a better price (phi_price)
        self.prob_search_prod = 0.25  # chance to search a new firm with higher demand (phi_quant)
        self.a_connections_number = 7  # number of type A connections (n)
        self.penalty_companies = dict()
        for _ in range(self.a_connections_number):
            self.companies.append(random.choice(model.cmp_schedule.agents))
        for company in self.companies:
            self.penalty_companies[company] = 0

    def search_cheaper_prices(self):
        if random.random() < self.prob_search_price:
            random_known_pick = random.choice(self.companies)
            self.companies.remove(random_known_pick)
            self.add_firm_by_households()

    def add_firm_by_households(self):
        firm_dict = dict()
        for firm in self.model.cmp_schedule.agents:
            if firm not in self.companies:
                firm_dict[firm] = firm.households
        sorted_households = sorted(firm_dict.items(), key=lambda x: x[1])
        company_to_add = draw_company(sorted_households)
        self.companies.append(company_to_add)

    def search_productive_firms(self):
        if random.random() < self.prob_search_prod:
            sorted_penalties = sorted(self.penalty_companies.items(), key=lambda x: x[1])
            company_to_delete = draw_company(sorted_penalties)
            self.companies.remove(company_to_delete)
            self.add_firm_by_households()

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
                                self.company.looking_for_worker = False
                        else:
                            self.company.households.remove(self)
                            self.company = company
                            self.company.households.append(self)
                            self.wage = self.company.wage
                            self.company.looking_for_worker = False
                    break
                else:
                    if company.wage >= self.wage:
                        self.company = company
                        self.company.households.append(self)
                        self.wage = self.company.wage
                        self.company.looking_for_worker = False
                        break
        else:
            self.wage *= self.wage_decreasing_coefficient

    def identify_consumption(self):
        average_price = sum(company.price for company in self.companies)/len(self.companies)
        self.consumption = int((self.wealth/(30 * average_price)) ** self.consumption_power)

    def buy_goods(self):
        for company in sorted(self.companies, key=lambda x: x.price):
            total_price = int(self.consumption * company.price)
            company.demand += self.consumption
            if company.inventory < self.consumption:
                self.penalty_companies[company.unique_id] += 1
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
        if self.model.current_day % 30 == 0:
            self.end_of_month()
        self.buy_goods()
        print('')
        print('Household ', self.unique_id)
        print('Current wealth:', self.wealth)
        try:
            print('Working for company:', self.company.unique_id)
            print('Real wage is:', self.company.wage)
        except:
            print('Unemployed')
        print('Desired wage is:', self.wage)


class Company(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.wealth = random.randint(600000, 1000000)  # initial sum of money of an agent
        self.wage = random.randint(29000, 35000)  # wage that firm will pay to employers
        self.price = 330 + random.randint(0,20)  # initial price of goods
        self.looking_for_worker = False  # True if firm is looking for an employee
        self.full_workplaces = 0  # number of days when we did not loose any employee
        self.demand = 100  # initial demand value
        self.demand_min_coefficient = 0.25  # if inventory is less than demand - search for a new employee (phi min)
        self.demand_max_coefficient = 1  # if inventory left is more than demand - fire an employee (phi max)
        self.inventory = 10  # initial inventory of firms
        self.sigma = 0.019  # percent for increasing/decreasing wage
        self.gamma = 24  # after this number of month with fulled working places we can decrease wage
        self.phi_min = 1.025  # required for counting marginal costs
        self.phi_max = 1.15  # required for counting marginal costs
        self.tau = 0.75  # chance to increase a price
        self.upsilon = 0.02  # max range of distribution for increasing price
        self.lambda_coefficient = 3  # how many products produced by one household per day
        self.money_buffer_coefficient = 0.1  # how much money does company saves for a month with bad sales
        self.households = []  # list of employees

    def produce(self):
        self.inventory += len(self.households) * self.lambda_coefficient

    def pay_wages(self):
        if len(self.households) * self.wage > self.wealth:
            self.wage = int(self.wealth/len(self.households))
        for h in self.households:
            h.wealth += self.wage
            self.wealth -= self.wage
            if h.wage < self.wage:
                h.wage = self.wage

    def share_liquidity(self):
        buffer = self.wage * len(self.households) * self.money_buffer_coefficient
        if len(self.households) > 0:
            liquidity_to_share = int((self.wealth - buffer)/len(self.households))
        else:
            liquidity_to_share = 0
        if liquidity_to_share > 0:
            self.wage += liquidity_to_share
            for h in self.households:
                h.wealth += liquidity_to_share
                self.wealth -= liquidity_to_share
                h.wage += liquidity_to_share

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
        if self.inventory <= self.demand_min_coefficient * self.demand:
            self.looking_for_worker = True
        else:
            self.looking_for_worker = False
        if self.inventory > self.demand_max_coefficient * self.demand:
            if self.households:
                fired_h = self.households[0]
                fired_h.company = None
                del self.households[0]
        self.demand = 0

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
        self.share_liquidity()
        self.set_wage_rate()
        self.hire_or_fire()
        self.change_goods_price()

    def step(self):
        self.produce()
        if self.model.current_day % 30 == 0:
            self.end_of_month()
        print('')
        print('Company ', self.unique_id)
        print('Current list of workers: ', list(worker.unique_id for worker in self.households))
        print('Current wage is: ', self.wage)
        print('Current price is: ', self.price)
        print('Position opened: ', self.looking_for_worker)
        print('Current inventory: ', self.inventory)
        print('Current demand is: ', self.demand)
        print('Current wealth: ', self.wealth)


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
        print('##############################################')
        print('Day #{0}'.format(self.current_day))
        print('##############################################')
        print('\n Companies \n')
        print('----------------------------------------------')

        self.cmp_schedule.step()

        print('----------------------------------------------')
        print('\n Households \n')
        print('----------------------------------------------')

        self.hh_schedule.step()
        self.current_day += 1


empty_model = LenExtended(20, 4)
number_of_steps = 10
for i in range(number_of_steps):
    empty_model.step()
