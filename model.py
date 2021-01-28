from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
import math
import random
from utils import *
import networkx as nx


class Householder(Agent):
    def __init__(self, unique_id, model, household_parameters):
        super().__init__(unique_id, model)
        # initial sum of money of an agent
        self.wealth = random.randint(household_parameters.min_wealth, household_parameters.max_wealth)
        self.wage = household_parameters.default_wage  # reservation wage (expected wage)
        self.consumption = household_parameters.default_consumption  # how much goods does householder consume per day
        self.companies = []  # list of firms where householder can buy goods (type A connection)
        self.company = None  # firm that householder works for
        # if household was unemployed his reservation wage decreases by 10%
        self.wage_decreasing_coefficient = household_parameters.wage_decreasing_coefficient
        # if price in new company less that this value, replace company by new one
        self.critical_price_ratio = household_parameters.critical_price_ratio
        # in paper self.critical_price_ratio is reffed as xi = 0.01, but here it is (1-xi)
        # allows not to spend all money for consumption (alpha)
        self.consumption_power = household_parameters.consumption_power
        # how many times unemployed household tries to find a job (beta)
        self.unemployed_attempts = household_parameters.unemployed_attempts
        # chance to search a job if wage is more than desired (pi)
        self.search_job_chance = household_parameters.search_job_chance
        # chance to search a better price (phi_price)
        self.prob_search_price = household_parameters.prob_search_price
        # chance to search a new firm with higher demand (phi_quant)
        self.prob_search_prod = household_parameters.prob_search_prod
        # number of type A connections (n)
        self.a_connections_number = household_parameters.a_connections_number
        self.penalty_companies = dict()
        self.preferred_companies = dict()
        self.social_influence = dict()
        self.most_preferred = None
        self.influenced_companies = dict()
        for _ in range(self.a_connections_number):
            self.companies.append(random.choice(model.cmp_schedule.agents))
        for company in self.companies:
            self.penalty_companies[company] = 0
            self.preferred_companies[company] = 0
            self.social_influence[company] = 1

    def search_cheaper_prices(self):
        if random.random() < self.prob_search_price:
            random_known_pick = random.choice(self.companies)
            self.companies.remove(random_known_pick)
            self.add_firm_by_households()

    def add_firm_by_households(self):
        firm_dict = dict()
        for firm in self.model.cmp_schedule.agents:
            if firm not in self.companies:
                firm_dict[firm] = len(firm.households)
        sorted_households = sorted(firm_dict.items(), key=lambda x: x[1])
        if sorted_households:
            company_to_add = draw_company(sorted_households)
            self.companies.append(company_to_add)

    def search_productive_firms(self):
        if random.random() < self.prob_search_prod:
            sorted_penalties = sorted(self.penalty_companies.items(), key=lambda x: x[1])
            company_to_delete = draw_company(sorted_penalties)
            self.add_firm_by_households()
            self.companies.remove(company_to_delete)

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
        average_price = sum(company.price for company in self.companies) / len(self.companies)
        self.consumption = int((self.wealth / (30 * average_price)) ** self.consumption_power)

    def buy_goods(self):
        for company in sorted(self.companies, key=lambda x: x.price * max(1 - math.sqrt(x.marketing_boost) / 100, 0.5)):
            total_price = int(self.consumption * company.price)
            company.demand += self.consumption
            if company.inventory < self.consumption:
                self.penalty_companies[company] += 1
            if (company.inventory > self.consumption) and (total_price < self.wealth):
                self.wealth -= total_price
                company.wealth += total_price
                company.inventory -= self.consumption
                self.preferred_companies[company] += 1
                break

    def calculate_most_preferred(self):
        self.most_preferred = sorted(self.preferred_companies.items(), key=lambda x: x[1], reverse=True)[0]

    def calculate_social_influence(self):
        neighbors_ids = self.model.social_network.neighbors(self.unique_id)
        neighbor_companies = dict()
        for n_id in neighbors_ids:
            neighbor_company_tuple = self.model.hh_schedule._agents[n_id].most_preferred
            if neighbor_company_tuple is not None:
                if neighbor_company_tuple[0] in neighbor_companies:
                    neighbor_companies[neighbor_company_tuple[0]] += neighbor_company_tuple[1]
                elif neighbor_company_tuple[1] != 0:
                    neighbor_companies[neighbor_company_tuple[0]] = neighbor_company_tuple[1]
        self.influenced_companies = neighbor_companies

    def update_penalties_and_preferred(self):
        for company in self.companies:
            self.penalty_companies[company] = 0
            self.preferred_companies[company] = 0

    def end_of_month(self):
        # self.search_cheaper_prices()
        # self.search_productive_firms()
        self.search_new_job()
        self.identify_consumption()
        self.calculate_most_preferred()
        self.calculate_social_influence()
        self.update_penalties_and_preferred()

    def step(self):
        if self.model.current_day % 30 == 0:
            self.end_of_month()
        self.buy_goods()


class Company(Agent):
    def __init__(self, unique_id, model, company_parameters):
        super().__init__(unique_id, model)
        # initial sum of money of an agent
        self.wealth = random.randint(company_parameters.company_min_wealth, company_parameters.company_max_wealth)
        # wage that firm will pay to employers
        self.wage = random.randint(company_parameters.company_min_wage, company_parameters.company_max_wage)
        # initial price of goods
        self.price = company_parameters.initial_price + random.randint(company_parameters.min_random_price,
                                                                       company_parameters.max_random_price)
        self.looking_for_worker = False  # True if firm is looking for an employee
        self.full_workplaces = 0  # number of days when we did not loose any employee
        self.workers_in_previous_month = 0  # number of worker on previous month to track if someone was hired
        self.demand = company_parameters.demand  # initial demand value
        # if inventory is less than demand - search for a new employee (phi min)
        self.demand_min_coefficient = company_parameters.demand_min
        # if inventory left is more than demand - fire an employee (phi max)
        self.demand_max_coefficient = company_parameters.demand_max
        self.inventory = company_parameters.inventory  # initial inventory of firms
        self.sigma = company_parameters.sigma  # percent for increasing/decreasing wage
        # after this number of month with fulled working places we can decrease wage
        self.gamma = company_parameters.gamma
        self.phi_min = company_parameters.phi_min  # required for counting marginal costs
        self.phi_max = company_parameters.phi_max  # required for counting marginal costs
        self.tau = company_parameters.tau  # chance to increase a price
        self.upsilon = company_parameters.upsilon  # max range of distribution for increasing price
        # how many products produced by one household per day
        self.lambda_coefficient = company_parameters.lambda_coefficient
        # how much money does company saves for a month with bad sales
        self.money_buffer_coefficient = company_parameters.money_buffer_coefficient
        self.households = []  # list of employees
        self.marketing_investments = company_parameters.marketing_investments  # ratio of power invested in marketing
        self.marketing_boost = 0  # price multiplicator gathered from marketing investments
        self.start_marketing = company_parameters.start_marketing

    def produce(self):
        self.inventory += len(self.households) * self.lambda_coefficient * (1 - self.marketing_investments)

    def marketing_raise(self):
        self.marketing_boost = self.marketing_boost + len(
            self.households) * self.marketing_investments * self.lambda_coefficient

    def pay_wages(self):
        if len(self.households) * self.wage > self.wealth:
            self.wage = int(self.wealth / len(self.households))
        for h in self.households:
            h.wealth += self.wage
            self.wealth -= self.wage
            if h.wage < self.wage:
                h.wage = self.wage

    def share_liquidity(self):
        buffer = self.wage * len(self.households) * self.money_buffer_coefficient
        if len(self.households) > 0:
            liquidity_to_share = int((self.wealth - buffer) / len(self.households))
        else:
            liquidity_to_share = 0
        if liquidity_to_share > 0:
            self.wage += liquidity_to_share
            for h in self.households:
                h.wealth += liquidity_to_share
                self.wealth -= liquidity_to_share
                h.wage += liquidity_to_share

    def count_workers(self):
        number_of_households = len(self.households)
        if number_of_households >= self.workers_in_previous_month:
            self.full_workplaces += 1
        else:
            self.full_workplaces = 0
        self.workers_in_previous_month = number_of_households

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
        marginal_costs = self.wage / (30 * self.lambda_coefficient)
        if self.price < self.phi_min * marginal_costs:
            if random.random() < self.tau:
                self.price = self.price * (1 + random.uniform(0, self.upsilon))
        if self.price > self.phi_max * marginal_costs:
            if random.random() < self.tau:
                self.price = self.price * (1 - random.uniform(0, self.upsilon))

    def change_marketing_investments(self):
        if self.inventory > self.start_marketing * self.demand:
            self.marketing_investments *= 1.1
        elif self.marketing_investments < self.start_marketing * 0.5:
            self.marketing_investments *= 0.8

    def invest_in_marketing(self):
        self.marketing_boost *= 0.8

    def end_of_month(self):
        self.change_marketing_investments()
        self.invest_in_marketing()
        self.pay_wages()
        self.share_liquidity()
        self.count_workers()
        self.set_wage_rate()
        self.hire_or_fire()
        self.change_goods_price()

    def step(self):
        self.marketing_raise()
        self.produce()
        if self.model.current_day % 30 == 0:
            self.end_of_month()


class LenExtended(Model):
    def __init__(self, num_hh, num_cmp, household_parameters, company_parameters):

        self.num_hh = num_hh
        self.num_cmp = num_cmp
        self.current_day = 0
        self.hh_schedule = RandomActivation(self)
        self.cmp_schedule = RandomActivation(self)
        self.social_network = nx.gnp_random_graph(num_hh, 0.99)
        for i in range(self.num_cmp):
            c = Company(i, self, company_parameters)
            self.cmp_schedule.add(c)

        for i in range(self.num_hh):
            h = Householder(i, self, household_parameters)
            self.hh_schedule.add(h)

        # Datacollector
        self.datacollector = DataCollector(
            # Household parameters
            {"hh_wealth": lambda m: h.wealth,
             "hh_wage": lambda m: h.wage,
             "consumption": lambda m: h.consumption,
             "companies": lambda m: h.companies,
             "company": lambda m: h.company,
             # "wage_decreasing_coefficient": lambda m: h.wage_decreasing_coefficient,
             # "critical_price_ratio": lambda m: h.critical_price_ratio,
             # "consumption_power": lambda m: h.consumption_power,
             # "unemployed_attempts": lambda m: h.unemployed_attempts,
             # "search_job_chance": lambda m: h.search_job_chance,
             # "prob_search_price": lambda m: h.prob_search_price,
             # "prob_search_prod": lambda m: h.prob_search_prod,
             # "a_connections_number": lambda m: h.a_connections_number,

             # Company parameters
             "C_wealth": lambda m: c.wealth,
             "C_wage": lambda m: c.wage,
             "price": lambda m: c.price,
             "looking_for_worker": lambda m: c.looking_for_worker,
             # "full_workplaces": lambda m: c.full_workplaces,
             # "workers_in_previous_month": lambda m: c.workers_in_previous_month,
             "demand": lambda m: c.demand,
             # "demand_min_coefficient": lambda m: c.demand_min_coefficient,
             # "demand_max_coefficient": lambda m: c.demand_max_coefficient,
             "inventory": lambda m: c.inventory,
             # "sigma": lambda m: c.sigma,
             "gamma": lambda m: c.gamma,
             # "phi_min": lambda m: c.phi_min,
             # "phi_max": lambda m: c.phi_max,
             # "tau": lambda m: c.tau,
             # "upsilon": lambda m: c.upsilon,
             "lambda_coefficient": lambda m: c.lambda_coefficient,
             # "money_buffer_coefficient": lambda m: c.money_buffer_coefficient,
             "households": lambda m: c.households,
             "marketing_investments": lambda m: c.marketing_investments,
             "marketing_boost": lambda m: c.marketing_boost})

    def step(self):
        self.datacollector.collect(self)

        self.cmp_schedule.step()
        self.hh_schedule.step()
        self.current_day += 1


class HouseholdParameters:
    def __init__(self, min_wealth, max_wealth, default_wage, default_consumption, wage_decreasing_coefficient,
                 critical_price_ratio, consumption_power, unemployed_attempts, search_job_chance, prob_search_price,
                 prob_search_prod, a_connections_number):
        self.min_wealth = min_wealth
        self.max_wealth = max_wealth
        self.default_wage = default_wage
        self.default_consumption = default_consumption
        self.wage_decreasing_coefficient = wage_decreasing_coefficient
        self.critical_price_ratio = critical_price_ratio
        self.consumption_power = consumption_power
        self.unemployed_attempts = unemployed_attempts
        self.search_job_chance = search_job_chance
        self.prob_search_price = prob_search_price
        self.prob_search_prod = prob_search_prod
        self.a_connections_number = a_connections_number


class CompanyParameters:
    def __init__(self, company_min_wealth, initial_price, company_max_wealth, company_min_wage, company_max_wage,
                 inventory, min_random_price, max_random_price, demand, demand_min, demand_max, sigma, gamma, phi_min,
                 phi_max, tau, upsilon, lambda_coefficient, money_buffer_coefficient, marketing_investments):
        self.company_min_wealth = company_min_wealth
        self.initial_price = initial_price
        self.company_max_wealth = company_max_wealth
        self.company_min_wage = company_min_wage
        self.company_max_wage = company_max_wage
        self.inventory = inventory
        self.min_random_price = min_random_price
        self.max_random_price = max_random_price
        self.demand = demand
        self.demand_min = demand_min
        self.demand_max = demand_max
        self.sigma = sigma
        self.gamma = gamma
        self.phi_min = phi_min
        self.phi_max = phi_max
        self.tau = tau
        self.upsilon = upsilon
        self.lambda_coefficient = lambda_coefficient
        self.money_buffer_coefficient = money_buffer_coefficient
        self.marketing_investments = marketing_investments


def run_model(number_of_households, number_of_companies, number_of_steps, min_wealth=20000, max_wealth=45000,
              default_wage=0, default_consumption=0, wage_decreasing_coefficient=0.9, critical_price_ratio=0.99,
              consumption_power=0.9, unemployed_attempts=5, search_job_chance=0.1, prob_search_price=0.25,
              prob_search_prod=0.25, a_connections_number=7, company_min_wealth=600000, initial_price=330,
              company_max_wealth=1000000, company_min_wage=29000, company_max_wage=35000, inventory=10,
              min_random_price=0, max_random_price=20, demand=100, demand_min=0.25, demand_max=1, sigma=0.019,
              gamma=24, phi_min=1.025, phi_max=1.15, tau=0.75, upsilon=0.02, lambda_coefficient=3,
              money_buffer_coefficient=0.1, marketing_investments=0.2, start_marketing=0.05):
    household_parameters = HouseholdParameters(min_wealth, max_wealth, default_wage, default_consumption,
                                               wage_decreasing_coefficient, critical_price_ratio, consumption_power,
                                               unemployed_attempts, search_job_chance, prob_search_price,
                                               prob_search_prod, a_connections_number)
    company_parameters = CompanyParameters(company_min_wealth, initial_price, company_max_wealth, company_min_wage,
                                           company_max_wage, inventory, min_random_price, max_random_price, demand,
                                           demand_min, demand_max, sigma, gamma, phi_min, phi_max, tau, upsilon,
                                           lambda_coefficient, money_buffer_coefficient, marketing_investments,
                                           start_marketing)

    abm_model = LenExtended(number_of_households, number_of_companies, household_parameters, company_parameters)
    for _ in range(number_of_steps):
        abm_model.step()

    return abm_model
