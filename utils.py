import numpy as np


def normalization(freq_list):
    freq_list_sum = sum(freq_list[:][1])
    return [c / freq_list_sum for c in freq_list]


def draw_company(freq_list):
    probabilities = normalization(freq_list)
    company_id = 0
    for j, value in enumerate(np.npr.multinomial(1, probabilities)):
        if value == 1:
            company_id = freq_list[j][0]
    return company_id
