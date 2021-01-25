import numpy as np


def normalization(freq_list):
    freq_list_sum = sum([x[1]+1 for x in freq_list])
    return [(c[1]+1) / freq_list_sum for c in freq_list]


def draw_company(freq_list):
    probabilities = normalization(freq_list)
    company_id = 0
    multinomial = np.random.multinomial(1, probabilities)
    for j, value in enumerate(multinomial):
        if value == 1:
            company_id = freq_list[j][0]
    return company_id
