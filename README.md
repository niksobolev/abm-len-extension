# LEN Model; Marketing and Network extension
General LEN Model with two extensions. Marketing extension, 
which allows companies to invest some amount of their wealth
into the brand value, which will affect householders' decision. Network extension allows householders to share what they buy with their neighbors, which
explained as the "social influence" effect, which also will be
considered by householders during their decision.

## Installation

You can clone the repository and use one of the jupyter notebooks
or create your own in the same working space.

## Usage

```python
import model

number_of_householders = 150
number_of_companies = 10
number_of_days = 20000

abm_model = model.run_model(number_of_householders, number_of_companies, number_of_days)
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## References
<a id="1">[1]</a> 
M. Lengnick, “Agent-based macroeconomics: 
A baseline model,”Journal of Economic Behavior & 
Organization, vol. 86, pp. 102–120, 2013.

<a id="2">[2]</a> D. D. Gatti, E. Gaffeo, and M. Gallegati, 
“Complex agent-basedmacroeconomics:  a  manifesto
for  a  new  paradigm,”Journal  ofEconomic Interaction
and Coordination, vol. 5, no. 2, pp. 111–135, 2010.